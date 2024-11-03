"""
Leak Shield Domain Module

This module provides functionality for scanning files and messages for potential
sensitive information leaks such as API keys, passwords, and private keys.
It uses patterns from the database to identify sensitive data.

Classes:
    LeakScanner: A static class that implements the scanning functionality.

Usage:
    from leak_shield.domains import LeakScanner

    # Scan a file
    leaks = await LeakScanner.scan_file("path/to/file")

    # Scan a message
    leaks = await LeakScanner.scan_message("content to scan")
"""

import os
import re
from typing import List
from django.apps import apps
from asgiref.sync import sync_to_async


class LeakScanner:
    """
    A static class for scanning files and messages for potential sensitive information leaks.

    This class provides methods to detect patterns that might indicate leaked credentials,
    API keys, passwords, or other sensitive information using patterns stored in the database.
    """

    @staticmethod
    @sync_to_async
    def get_patterns():
        """
        Retrieve all active patterns from the database.

        Returns:
            QuerySet: A queryset containing all Pattern instances
        """
        Pattern = apps.get_model('leak_shield', 'Pattern')
        return list(Pattern.objects.all())

    @staticmethod
    async def check_for_leaks(content: str) -> list:
        """
        Scan content for potential sensitive information leaks using patterns from database.

        Args:
            content (str): The text content to scan for leaks

        Returns:
            list: A list of dictionaries containing details about found leaks:
                 - type: The name of the pattern that matched
                 - match: The actual matched text
                 - position: Tuple of start and end positions of the match
        """
        findings = []
        patterns = await LeakScanner.get_patterns()

        for pattern in patterns:
            matches = re.finditer(pattern.regex, content)
            for match in matches:
                findings.append({
                    'type': pattern.name,
                    'match': match.group(0),
                    'position': match.span()
                })
        return findings

    @staticmethod
    async def scan_file(file_path: str) -> List[dict]:
        """
        Asynchronously scan a file for potential sensitive information leaks.

        Args:
            file_path (str): Path to the file to be scanned

        Returns:
            List[dict]: A list of dictionaries containing details about found leaks.
                       Returns empty list if file doesn't exist.
        """
        if not os.path.exists(file_path):
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return await LeakScanner.check_for_leaks(content)

    @staticmethod
    async def scan_message(message: str) -> List[dict]:
        """
        Asynchronously scan a message or string for potential sensitive information leaks.

        Args:
            message (str): The message content to scan

        Returns:
            List[dict]: A list of dictionaries containing details about found leaks
        """
        return await LeakScanner.check_for_leaks(message)
