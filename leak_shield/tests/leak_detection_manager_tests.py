import json
from unittest import mock
from leak_shield.services import LeakDetectionManager
from leak_shield.tests.base_tests import AsyncTestCase


class LeakDetectionManagerTests(AsyncTestCase):
    def setUp(self):
        super().setUp()
        self.queue_name = 'test-queue'
        self.region_name = 'us-east-1'

    @mock.patch('leak_shield.services.LeakScannerAdapter')
    @mock.patch('boto3.client')
    def test_manager_initialization(self, mock_boto, mock_adapter):
        mock_sqs = mock.MagicMock()
        mock_sqs.get_queue_url.return_value = {'QueueUrl': 'test-url'}
        mock_boto.return_value = mock_sqs

        with mock.patch('boto3.Session') as mock_session:
            mock_session.return_value.get_credentials.return_value = mock.MagicMock(
                access_key='test-key',
                secret_key='test-secret'
            )
            manager = LeakDetectionManager(self.queue_name, self.region_name)
            self.assertEqual(manager.queue, self.queue_name)
            self.assertIn('scan_file', manager.tasks)
            self.assertIn('scan_message', manager.tasks)

    @mock.patch('boto3.client')
    @mock.patch('leak_shield.services.LeakScannerAdapter')
    async def test_get_messages_async(self, mock_adapter, mock_boto):
        mock_adapter.get_patterns = mock.AsyncMock(return_value=[])
        mock_adapter.scan_message = mock.AsyncMock(return_value=[])
        mock_adapter.scan_file = mock.AsyncMock(return_value=[])

        mock_sqs = mock.MagicMock()
        mock_sqs.receive_message.return_value = {
            'Messages': [{
                'Body': json.dumps({
                    'task': 'scan_message',
                    'args': ['test message'],
                    'kwargs': {}
                }),
                'ReceiptHandle': 'receipt123'
            }]
        }
        mock_sqs.get_queue_url.return_value = {'QueueUrl': 'test-url'}
        mock_boto.return_value = mock_sqs

        manager = LeakDetectionManager(self.queue_name, self.region_name)
        messages = await manager._get_messages()

        self.assertEqual(len(messages), 1)
        self.assertIn('Body', messages[0])
        mock_adapter.scan_message.assert_called_once_with('test message')
        mock_sqs.delete_message.assert_called_once()

    @mock.patch('boto3.client')
    @mock.patch('leak_shield.services.LeakScannerAdapter')
    async def test_scan_file_task(self, mock_adapter, mock_boto):
        mock_adapter.scan_file = mock.AsyncMock(
            return_value=[{'type': 'test', 'match': 'secret123'}])

        mock_sqs = mock.MagicMock()
        mock_sqs.receive_message.return_value = {
            'Messages': [{
                'Body': json.dumps({
                    'task': 'scan_file',
                    'args': ['/test/file.txt'],
                    'kwargs': {}
                }),
                'ReceiptHandle': 'receipt123'
            }]
        }
        mock_sqs.get_queue_url.return_value = {'QueueUrl': 'test-url'}
        mock_boto.return_value = mock_sqs

        manager = LeakDetectionManager(self.queue_name, self.region_name)
        messages = await manager._get_messages()

        self.assertEqual(len(messages), 1)
        mock_adapter.scan_file.assert_called_once_with('/test/file.txt')

    @mock.patch('boto3.client')
    @mock.patch('leak_shield.services.LeakScannerAdapter')
    async def test_invalid_message_format(self, mock_adapter, mock_boto):
        mock_sqs = mock.MagicMock()
        mock_sqs.receive_message.return_value = {
            'Messages': [{
                'Body': 'invalid json',
                'ReceiptHandle': 'receipt123'
            }]
        }
        mock_sqs.get_queue_url.return_value = {'QueueUrl': 'test-url'}
        mock_boto.return_value = mock_sqs

        manager = LeakDetectionManager(self.queue_name, self.region_name)
        messages = await manager._get_messages()

        self.assertEqual(len(messages), 1)
        mock_adapter.scan_file.assert_not_called()
        mock_adapter.scan_message.assert_not_called()

    def test_get_messages(self):
        self.loop.run_until_complete(self.test_get_messages_async())
