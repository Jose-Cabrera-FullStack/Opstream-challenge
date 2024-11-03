import json
from unittest import mock
from leak_shield.services import LeakDetectionManager
from leak_shield.tests.base_tests import AsyncTestCase


class LeakDetectionManagerTests(AsyncTestCase):
    def setUp(self):
        super().setUp()
        self.queue_name = 'test-queue'
        self.region_name = 'us-east-1'
        self.mock_credentials = {
            'aws_access_key_id': 'test',
            'aws_secret_access_key': 'test',
            'region_name': 'us-east-1'
        }

    @mock.patch('boto3.client')
    def test_manager_initialization(self, mock_boto):
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
            mock_boto.assert_called_with('sqs', region_name=self.region_name)

    @mock.patch('boto3.client')
    async def test_get_messages_async(self, mock_boto):
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

        with mock.patch('boto3.Session') as mock_session:
            mock_session.return_value.get_credentials.return_value = mock.MagicMock(
                access_key='test-key',
                secret_key='test-secret'
            )
            manager = LeakDetectionManager(self.queue_name, self.region_name)
            messages = await manager._get_messages()

            self.assertEqual(len(messages), 1)
            self.assertIn('Body', messages[0])
            mock_sqs.delete_message.assert_called_once()

    def test_get_messages(self):
        self.loop.run_until_complete(
            self.__class__.test_get_messages_async(self))

    @mock.patch('leak_shield.domains.LeakScanner.scan_file')
    @mock.patch('boto3.client')
    async def test_scan_file_task_execution(self, mock_boto, mock_scan_file):
        mock_sqs = mock.MagicMock()
        mock_sqs.get_queue_url.return_value = {'QueueUrl': 'test-url'}
        mock_sqs.receive_message.return_value = {
            'Messages': [{
                'Body': json.dumps({
                    'task': 'scan_file',
                    'args': ['/path/to/test.txt'],
                    'kwargs': {}
                }),
                'ReceiptHandle': 'receipt123'
            }]
        }
        mock_boto.return_value = mock_sqs

        expected_leaks = [
            {'type': 'api_key', 'match': 'test123', 'position': (0, 6)}]
        mock_scan_file.return_value = expected_leaks

        with mock.patch('boto3.Session') as mock_session:
            mock_session.return_value.get_credentials.return_value = mock.MagicMock(
                access_key='test-key',
                secret_key='test-secret'
            )
            manager = LeakDetectionManager(self.queue_name, self.region_name)
            await manager._get_messages()

        mock_scan_file.assert_called_once_with('/path/to/test.txt')

    @mock.patch('leak_shield.domains.LeakScanner.scan_message')
    @mock.patch('boto3.client')
    async def test_scan_message_task_execution(self, mock_boto, mock_scan_message):
        mock_sqs = mock.MagicMock()
        mock_sqs.get_queue_url.return_value = {'QueueUrl': 'test-url'}
        mock_sqs.receive_message.return_value = {
            'Messages': [{
                'Body': json.dumps({
                    'task': 'scan_message',
                    'args': ['sensitive message content'],
                    'kwargs': {}
                }),
                'ReceiptHandle': 'receipt123'
            }]
        }
        mock_boto.return_value = mock_sqs

        expected_leaks = [{'type': 'password',
                           'match': 'pass123', 'position': (0, 6)}]
        mock_scan_message.return_value = expected_leaks

        with mock.patch('boto3.Session') as mock_session:
            mock_session.return_value.get_credentials.return_value = mock.MagicMock(
                access_key='test-key',
                secret_key='test-secret'
            )
            manager = LeakDetectionManager(self.queue_name, self.region_name)

            await manager._get_messages()

            mock_scan_message.assert_called_once_with(
                'sensitive message content')

    @mock.patch('boto3.client')
    async def test_invalid_task_handling(self, mock_boto):
        mock_sqs = mock.MagicMock()
        mock_sqs.get_queue_url.return_value = {'QueueUrl': 'test-url'}
        mock_sqs.receive_message.return_value = {
            'Messages': [{
                'Body': json.dumps({
                    'task': 'invalid_task',
                    'args': [],
                    'kwargs': {}
                }),
                'ReceiptHandle': 'receipt123'
            }]
        }
        mock_boto.return_value = mock_sqs

        with mock.patch('boto3.Session') as mock_session:
            mock_session.return_value.get_credentials.return_value = mock.MagicMock(
                access_key='test-key',
                secret_key='test-secret'
            )
            manager = LeakDetectionManager(self.queue_name, self.region_name)

            messages = await manager._get_messages()
            self.assertEqual(len(messages), 1)
