from leak_shield.domains.leak_scanner import LeakScanner
from leak_shield.models import Pattern
from tests.base_tests import AsyncTestCase


class LeakScannerTests(AsyncTestCase):
    """Test cases for the LeakScanner class functionality."""

    def setUp(self):
        super().setUp()
        self.test_api_key = 'api_key="secret123"'
        self.test_password = 'password="supersecret"'
        self.test_safe = 'this is safe content'

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
        results = await LeakScanner.check_for_leaks(self.test_api_key)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'api_key')

        results = await LeakScanner.check_for_leaks(self.test_password)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'password')

        results = await LeakScanner.check_for_leaks(self.test_safe)
        self.assertEqual(len(results), 0)

    def test_check_for_leaks(self):
        self.loop.run_until_complete(self.test_check_for_leaks_async())

    async def test_scan_message_async(self):
        results = await LeakScanner.scan_message(self.test_api_key)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'api_key')

    def test_scan_message(self):
        self.loop.run_until_complete(self.test_scan_message_async())
