from unittest import mock
from asgiref.sync import sync_to_async
from leak_shield.adapters import LeakScannerAdapter
from leak_shield.models import Pattern, ScannedMessage, ScannedFile, ActionLog
from .base_tests import AsyncTestCase


class LeakScannerAdapterTests(AsyncTestCase):
    def setUp(self):
        super().setUp()
        self.adapter = LeakScannerAdapter()
        self.test_pattern = Pattern.objects.create(
            name='test_pattern',
            regex=r'secret=([^\s]+)',
            description='Test Pattern'
        )

    async def test_get_patterns_async(self):
        patterns = await LeakScannerAdapter.get_patterns()
        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0].name, 'test_pattern')

    @mock.patch('os.path.exists')
    @mock.patch('builtins.open', create=True)
    async def test_scan_file_with_leak(self, mock_open, mock_exists):
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = 'secret=123456'

        results = await LeakScannerAdapter.scan_file('test.txt')

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'test_pattern')
        mock_exists.assert_called_once_with('test.txt')

    @mock.patch('os.path.exists')
    async def test_scan_file_not_exists(self, mock_exists):
        mock_exists.return_value = False
        results = await LeakScannerAdapter.scan_file('nonexistent.txt')
        self.assertEqual(results, [])

    async def test_scan_message_with_leak(self):
        message = "This is a test secret=mysecret123"
        results = await LeakScannerAdapter.scan_message(
            channel_id="test-channel",
            user_id="test-user",
            message=message
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'test_pattern')
        self.assertEqual(results[0]['match'], 'secret=mysecret123')

    async def test_scan_message_without_leak(self):
        message = "This is a safe message"
        results = await LeakScannerAdapter.scan_message(
            channel_id="test-channel",
            user_id="test-user",
            message=message
        )
        self.assertEqual(len(results), 0)

    async def test_save_scanned_message_creates_records(self):
        """Test that scanning a message with leaks creates appropriate records"""
        message = "This is a test secret=mysecret123"
        results = await LeakScannerAdapter.scan_message(
            channel_id="test-channel",
            user_id="test-user",
            message=message
        )

        scanned_message = await sync_to_async(lambda: ScannedMessage.objects.select_related('pattern').filter(
            channel_id="test-channel"
        ).first())()

        self.assertIsNotNone(scanned_message)
        self.assertEqual(scanned_message.message_text, message)
        pattern_id = await sync_to_async(lambda: scanned_message.pattern.id)()
        self.assertEqual(pattern_id, self.test_pattern.id)

        action_log = await sync_to_async(lambda: ActionLog.objects.select_related('message').filter(
            message=scanned_message
        ).first())()

        self.assertIsNotNone(action_log)
        self.assertEqual(action_log.action_type, 'BLOCK')

    @mock.patch('os.path.exists')
    @mock.patch('builtins.open', create=True)
    async def test_save_scanned_file_creates_records(self, mock_open, mock_exists):
        """Test that scanning a file with leaks creates appropriate records"""
        mock_exists.return_value = True
        file_content = 'secret=123456'
        mock_open.return_value.__enter__.return_value.read.return_value = file_content

        results = await LeakScannerAdapter.scan_file('test.txt')

        scanned_file = await sync_to_async(lambda: ScannedFile.objects.select_related('pattern').filter(
            file_name='test.txt'
        ).first())()

        self.assertIsNotNone(scanned_file)
        self.assertEqual(scanned_file.file_content, file_content)
        pattern_id = await sync_to_async(lambda: scanned_file.pattern.id)()
        self.assertEqual(pattern_id, self.test_pattern.id)

        action_log = await sync_to_async(lambda: ActionLog.objects.select_related('file').filter(
            file=scanned_file
        ).first())()

        self.assertIsNotNone(action_log)
        self.assertEqual(action_log.action_type, 'BLOCK')

    async def test_multiple_patterns_in_message(self):
        """Test handling multiple pattern matches in a single message"""
        another_pattern = await sync_to_async(Pattern.objects.create)(
            name='password_pattern',
            regex=r'password=([^\s]+)',
            description='Password Pattern'
        )

        message = "secret=123456 password=abc123"
        results = await LeakScannerAdapter.scan_message(
            channel_id="test-channel",
            user_id="test-user",
            message=message
        )

        self.assertEqual(len(results), 2)

        scanned_messages = await sync_to_async(list)(
            ScannedMessage.objects.filter(channel_id="test-channel")
        )
        self.assertEqual(len(scanned_messages), 2)

        action_logs = await sync_to_async(list)(
            ActionLog.objects.filter(message__in=scanned_messages)
        )
        self.assertEqual(len(action_logs), 2)

    async def test_no_duplicate_records_for_same_pattern(self):
        """Test that multiple matches of the same pattern don't create duplicate records"""
        message = "secret=123 secret=456"
        await LeakScannerAdapter.scan_message(
            channel_id="test-channel",
            user_id="test-user",
            message=message
        )

        count = await sync_to_async(lambda: ScannedMessage.objects.filter(
            channel_id="test-channel",
            pattern=self.test_pattern
        ).count())()

        self.assertEqual(count, 1)

    @classmethod
    async def async_get(cls, queryset):
        """Helper method to get async query results"""
        return await sync_to_async(lambda: queryset)()

    @classmethod
    async def async_filter(cls, queryset):
        """Helper method to filter async query results"""
        return await sync_to_async(lambda: list(queryset))()

    @classmethod
    async def async_create(cls, model, **kwargs):
        """Helper method to create model instances asynchronously"""
        return await sync_to_async(model.objects.create)(**kwargs)
