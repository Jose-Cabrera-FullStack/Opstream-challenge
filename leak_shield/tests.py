import json
import asyncio
from unittest import mock
from django.test import TestCase
from leak_shield.domains import LeakScanner
from leak_shield.services import LeakDetectionManager


class LeakScannerTests(TestCase):
    """
    Test cases for the LeakScanner class functionality.

    Tests the detection of sensitive information in messages and files.
    """

    def setUp(self):
        """Initialize test data for leak detection scenarios."""
        self.test_api_key = 'api_key="secret123"'
        self.test_password = 'password="supersecret"'
        self.test_safe = 'this is safe content'

    def test_check_for_leaks(self):
        """
        Test the check_for_leaks method for various types of content.

        Verifies:
        - API key detection
        - Password detection
        - Safe content handling
        """
        # Test API key detection
        results = LeakScanner.check_for_leaks(self.test_api_key)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'api_key')

        # Test password detection
        results = LeakScanner.check_for_leaks(self.test_password)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'password')

        # Test safe content
        results = LeakScanner.check_for_leaks(self.test_safe)
        self.assertEqual(len(results), 0)

    async def async_test_scan_message(self):
        """Test asynchronous message scanning for sensitive content."""
        results = await LeakScanner.scan_message(self.test_api_key)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'api_key')

    def test_scan_message(self):
        """Run the asynchronous message scanning test."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_test_scan_message())


class LeakDetectionManagerTests(TestCase):
    """
    Test cases for the LeakDetectionManager class.

    Tests the AWS SQS integration and message handling functionality.
    """

    def setUp(self):
        """Initialize test configuration and mock credentials."""
        self.queue_name = 'test-queue'
        self.region_name = 'us-east-1'
        self.mock_credentials = {
            'aws_access_key_id': 'test',
            'aws_secret_access_key': 'test',
            'region_name': 'us-east-1'
        }

    @mock.patch('boto3.client')
    def test_manager_initialization(self, mock_boto):
        """
        Test LeakDetectionManager initialization.

        Verifies:
        - Queue name assignment
        - Task registration
        - AWS SQS client configuration
        """
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
    async def async_test_get_messages(self, mock_boto):
        """
        Test asynchronous message retrieval from SQS queue.

        Verifies:
        - Message retrieval
        - Message deletion after processing
        - Proper message format handling
        """
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
        """Run the asynchronous message retrieval test."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_test_get_messages())
