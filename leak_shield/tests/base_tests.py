import asyncio
from django.test import TransactionTestCase
from django.db import connections


class AsyncTestCase(TransactionTestCase):
    """Base test class for async tests."""

    def setUp(self):
        super().setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()
        asyncio.set_event_loop(None)
        for conn in connections.all():
            conn.close_if_unusable_or_obsolete()
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        for conn in connections.all():
            conn.close()
        super().tearDownClass()
