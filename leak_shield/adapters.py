import os
from typing import List
from asgiref.sync import sync_to_async
from django.apps import apps

from leak_shield.domains.leak_scanner import LeakScannerDomain


class LeakScannerAdapter:
    """
    Adapter class for handling infrastructure concerns of leak scanning.
    """

    _domain = LeakScannerDomain()

    @staticmethod
    @sync_to_async
    def get_patterns() -> list:
        """
        Retrieve all active patterns from the database.

        Returns:
            list: A list containing all Pattern instances
        """
        Pattern = apps.get_model('leak_shield', 'Pattern')
        return list(Pattern.objects.all())

    @staticmethod
    async def scan_file(file_path: str) -> List[dict]:
        """
        Scan a file for potential sensitive information leaks.

        Args:
            file_path (str): Path to the file to be scanned

        Returns:
            List[dict]: A list of dictionaries containing details about found leaks
        """
        if not os.path.exists(file_path):
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        patterns = await LeakScannerAdapter.get_patterns()
        return await LeakScannerAdapter._domain.check_for_leaks(patterns, content)

    @staticmethod
    async def scan_message(message: str) -> List[dict]:
        """
        Scan a message for potential sensitive information leaks.

        Args:
            message (str): The message content to scan

        Returns:
            List[dict]: A list of dictionaries containing details about found leaks
        """
        patterns = await LeakScannerAdapter.get_patterns()
        return await LeakScannerAdapter._domain.check_for_leaks(patterns, message)
