"""
Test module for the Leak Shield application.

This module provides comprehensive test coverage for the leak detection system,
including both the scanning functionality and AWS SQS integration.

Test Structure:
    1. LeakScannerTests
       - Tests for pattern detection in messages and files
       - Verifies detection of API keys, passwords, and safe content
       - Tests both synchronous and asynchronous scanning methods

    2. LeakDetectionManagerTests
       - Tests AWS SQS queue integration
       - Verifies message processing and task execution
       - Tests proper handling of AWS credentials and regions
       - Mocks AWS services for reliable testing

Usage:
    Run tests using Django's test runner:
    $ python manage.py test leak_shield.tests or python manage.py test leak_shield

Test Dependencies:
    - Django TestCase
    - unittest.mock for AWS service mocking
    - asyncio for testing asynchronous operations
"""

from slack_sdk import WebClient
import logging
import sys
import json
import asyncio
from unittest import mock
from django.test import TransactionTestCase
from asgiref.sync import sync_to_async
from leak_shield.domains import LeakScanner
from leak_shield.services import LeakDetectionManager
from leak_shield.models import Pattern


class LeakScannerTests(TransactionTestCase):
    """Test cases for the LeakScanner class functionality."""

    def setUp(self):
        """Initialize test data and patterns synchronously."""
        super().setUp()
        self.test_api_key = 'api_key="secret123"'
        self.test_password = 'password="supersecret"'
        self.test_safe = 'this is safe content'

        # Create test patterns synchronously
        self.api_key_pattern = Pattern.objects.create(
            name='api_key',
            regex=r'api_key\s*=\s*["\']([^"\']+)["\']',
            description='API Key Pattern'
        )
        self.password_pattern = Pattern.objects.create(
            name='password',
            regex=r'password\s*=\s*["\']([^"\']+)["\']',
            description='Password Pattern'
        )

    async def test_check_for_leaks_async(self):
        """Test the check_for_leaks method asynchronously."""
        # Test API key detection
        results = await LeakScanner.check_for_leaks(self.test_api_key)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'api_key')

        # Test password detection
        results = await LeakScanner.check_for_leaks(self.test_password)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'password')

        # Test safe content
        results = await LeakScanner.check_for_leaks(self.test_safe)
        self.assertEqual(len(results), 0)

    def test_check_for_leaks(self):
        """Run the synchronous version of leak checking tests."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.test_check_for_leaks_async())
        finally:
            loop.close()

    async def test_scan_message_async(self):
        """Test asynchronous message scanning."""
        results = await LeakScanner.scan_message(self.test_api_key)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'api_key')

    def test_scan_message(self):
        """Run the asynchronous message scanning test."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.test_scan_message_async())
        finally:
            loop.close()


class LeakDetectionManagerTests(TransactionTestCase):
    """
    Test cases for the LeakDetectionManager class.

    Tests the AWS SQS integration and message handling functionality.
    """

    def setUp(self):
        """Initialize test configuration and mock credentials."""
        super().setUp()
        self.queue_name = 'test-queue'
        self.region_name = 'us-east-1'
        self.mock_credentials = {
            'aws_access_key_id': 'test',
            'aws_secret_access_key': 'test',
            'region_name': 'us-east-1'
        }
        # Create new event loop for each test
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Clean up resources after each test."""
        self.loop.close()
        asyncio.set_event_loop(None)
        super().tearDown()

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
        """Async implementation of message retrieval test."""
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

    # @mock.patch('boto3.client')
    # def test_get_messages(self, mock_boto):
    #     """Run the asynchronous message retrieval test."""
    #     self.loop.run_until_complete(self.async_test_get_messages(mock_boto))


# test.py
# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
# Verify it works
client = WebClient()
api_response = client.api_test()
