import asyncio
from asgiref.sync import sync_to_async
from leak_shield.domains.leak_scanner import LeakScannerDomain
from leak_shield.models import Pattern
from .base_tests import AsyncTestCase


class LeakScannerTests(AsyncTestCase):
    """Test cases for the LeakScanner class functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)

    @classmethod
    def tearDownClass(cls):
        cls.loop.close()
        asyncio.set_event_loop(None)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.loop.run_until_complete(self.asyncSetUp())

    async def asyncSetUp(self):
        self.domain = LeakScannerDomain()
        self.test_api_key = 'api_key="secret123"'
        self.test_password = 'password="supersecret"'
        self.test_safe = 'this is safe content'

        create_pattern = sync_to_async(Pattern.objects.create)
        self.api_key_pattern = await create_pattern(
            name='api_key',
            regex=r'api_key\s*=\s*["\']([^"\']+)["\']',
            description='API Key Pattern'
        )
        self.password_pattern = await create_pattern(
            name='password',
            regex=r'password\s*=\s*["\']([^"\']+)["\']',
            description='Password Pattern'
        )
        self.patterns = [self.api_key_pattern, self.password_pattern]

    async def test_check_for_leaks_async(self):
        results = await self.domain.check_for_leaks(self.patterns, self.test_api_key)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'api_key')

        results = await self.domain.check_for_leaks(self.patterns, self.test_password)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'password')

        results = await self.domain.check_for_leaks(self.patterns, self.test_safe)
        self.assertEqual(len(results), 0)

    async def test_check_for_multiple_leaks_async(self):
        content = 'api_key="123" password="456"'
        results = await self.domain.check_for_leaks(self.patterns, content)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['type'], 'api_key')
        self.assertEqual(results[1]['type'], 'password')

    async def test_check_for_overlapping_patterns(self):
        create_pattern = sync_to_async(Pattern.objects.create)
        overlapping_pattern = await create_pattern(
            name='general_secret',
            regex=r'["\']([^"\']+)["\']',
            description='General Secret Pattern'
        )
        self.patterns.append(overlapping_pattern)

        content = 'api_key="secret123"'
        results = await self.domain.check_for_leaks(self.patterns, content)

        self.assertGreaterEqual(len(results), 2)

    def test_check_for_leaks(self):
        self.loop.run_until_complete(self.test_check_for_leaks_async())
