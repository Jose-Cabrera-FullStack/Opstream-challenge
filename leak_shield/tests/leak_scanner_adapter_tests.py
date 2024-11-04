import os
from unittest import mock
from leak_shield.adapters import LeakScannerAdapter
from leak_shield.models import Pattern
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
        # Setup mocks
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
        results = await LeakScannerAdapter.scan_message(message)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'test_pattern')
        self.assertEqual(results[0]['match'], 'secret=mysecret123')

    async def test_scan_message_without_leak(self):
        message = "This is a safe message"
        results = await LeakScannerAdapter.scan_message(message)
        self.assertEqual(len(results), 0)
