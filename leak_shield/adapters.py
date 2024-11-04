"""
LeakShield Adapter Module

This module provides the infrastructure layer implementation for the LeakShield system.
It contains adapter classes that bridge the domain logic with external systems like
databases and file systems.

The main component is the LeakScannerAdapter class which handles:
- Pattern retrieval from the database
- Message and file scanning for sensitive information
- Persistence of scan results
- Action logging for detected leaks

The adapter follows the hexagonal architecture pattern, isolating domain logic
from infrastructure concerns and providing a clean interface for the application layer.

Usage:
    adapter = LeakScannerAdapter()
    results = await adapter.scan_message(
        channel_id="CH123",
        user_id="U123",
        message="sensitive content"
    )
"""

import os
from typing import List
from asgiref.sync import sync_to_async
from django.db import transaction
from leak_shield.domains import LeakScannerDomain
from leak_shield.models import Pattern, ScannedMessage, ScannedFile, ActionLog


class LeakScannerAdapter:
    """
    Adapter class for handling infrastructure concerns of leak scanning.

    This class serves as an adapter between the domain logic and infrastructure,
    handling database operations and file system interactions for leak detection.
    It provides methods for scanning both messages and files for sensitive information
    and persisting the results.

    Attributes:
        _domain (LeakScannerDomain): Domain class instance for leak detection logic

    Usage:
        adapter = LeakScannerAdapter()
        results = await adapter.scan_message(
            channel_id="CH123",
            user_id="U123",
            message="sensitive content"
        )
    """

    _domain = LeakScannerDomain()

    @staticmethod
    @sync_to_async
    def get_patterns() -> list:
        """
        Retrieve all active patterns from the database asynchronously.

        This method fetches all pattern records that are used for scanning
        messages and files for sensitive information.

        Returns:
            list[Pattern]: A list containing all Pattern model instances

        Example:
            patterns = await LeakScannerAdapter.get_patterns()
            print(patterns[0].name)
            'credit_card_pattern'
        """
        return list(Pattern.objects.all())

    @staticmethod
    @sync_to_async
    def save_scanned_message(
        channel_id: str,
        user_id: str,
        message: str,
        findings: List[dict]
    ) -> None:
        """
        Save message scan results to database within a transaction.

        This method creates records for messages that contain sensitive information,
        ensuring that duplicate records are not created for the same pattern match.

        Args:
            channel_id (str): Slack channel identifier where message was posted
            user_id (str): Slack user identifier who posted the message
            message (str): Content of the message that was scanned
            findings (List[dict]): List of detected pattern matches in the message

        The findings list should contain dictionaries with the following structure:
            {
                'type': str,      # Pattern name that matched
                'match': str,     # The actual text that matched
                'position': tuple # Start and end positions of the match
            }

        Example:
            findings = [{'type': 'api_key', 'match': 'key=123', 'position': (0, 7)}]
            await save_scanned_message('CH1', 'U1', 'message', findings)
        """
        with transaction.atomic():
            pattern_types = {finding['type'] for finding in findings}

            for pattern_type in pattern_types:
                pattern = Pattern.objects.select_for_update().get(name=pattern_type)

                exists = ScannedMessage.objects.filter(
                    channel_id=channel_id,
                    user_id=user_id,
                    pattern=pattern,
                    message_text=message
                ).exists()

                if not exists:
                    scanned_message = ScannedMessage.objects.create(
                        channel_id=channel_id,
                        user_id=user_id,
                        message_text=message,
                        pattern=pattern
                    )

                    ActionLog.objects.create(
                        message=scanned_message,
                        action_type='BLOCK',
                        action_details=f"Blocked message containing {pattern_type}"
                    )

    @staticmethod
    @sync_to_async
    def save_scanned_file(file_name: str, content: str, findings: List[dict]) -> None:
        """
        Save file scan results to database within a transaction.

        This method creates records for files that contain sensitive information,
        ensuring that duplicate records are not created for the same pattern match.

        Args:
            file_name (str): Name of the file that was scanned
            content (str): Content of the file that was scanned
            findings (List[dict]): List of detected pattern matches in the file

        The findings list should contain dictionaries with the following structure:
            {
                'type': str,      # Pattern name that matched
                'match': str,     # The actual text that matched
                'position': tuple # Start and end positions of the match
            }

        Example:
            findings = [{'type': 'password', 'match': 'pwd=123', 'position': (0, 7)}]
            await save_scanned_file('config.txt', 'file content', findings)
        """
        with transaction.atomic():
            pattern_types = {finding['type'] for finding in findings}

            for pattern_type in pattern_types:
                pattern = Pattern.objects.select_for_update().get(name=pattern_type)

                exists = ScannedFile.objects.filter(
                    file_name=file_name,
                    pattern=pattern,
                    file_content=content
                ).exists()

                if not exists:
                    scanned_file = ScannedFile.objects.create(
                        file_name=file_name,
                        file_content=content,
                        pattern=pattern
                    )

                    ActionLog.objects.create(
                        file=scanned_file,
                        action_type='BLOCK',
                        action_details=f"Blocked file containing {pattern_type}"
                    )

    @staticmethod
    async def scan_file(file_path: str) -> List[dict]:
        """
        Scan a file for potential sensitive information leaks.

        This method reads a file's content and scans it for patterns that might
        indicate sensitive information. If any matches are found, the results
        are saved to the database.

        Args:
            file_path (str): Full path to the file to be scanned

        Returns:
            List[dict]: A list of dictionaries containing details about found leaks.
                Each dictionary has the following structure:
                {
                    'type': str,      # Pattern name that matched
                    'match': str,     # The actual text that matched
                    'position': tuple # Start and end positions of the match
                }

        Example:
            results = await LeakScannerAdapter.scan_file('/path/to/file.txt')
            print(results[0]['type'])
            'api_key'
        """
        if not os.path.exists(file_path):
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        patterns = await LeakScannerAdapter.get_patterns()
        findings = await LeakScannerAdapter._domain.check_for_leaks(patterns, content)

        if findings:
            file_name = os.path.basename(file_path)
            await LeakScannerAdapter.save_scanned_file(file_name, content, findings)

        return findings

    @staticmethod
    async def scan_message(channel_id: str, user_id: str, message: str) -> List[dict]:
        """
        Scan a Slack message for sensitive information and store results.

        This method scans a message for patterns that might indicate sensitive
        information. If any matches are found, the results are saved to the database
        and appropriate actions are logged.

        Args:
            channel_id (str): Slack channel identifier where message was posted
            user_id (str): Slack user identifier who posted the message
            message (str): Content of the message to scan

        Returns:
            List[dict]: A list of dictionaries containing details about found leaks.
                Each dictionary has the following structure:
                {
                    'type': str,      # Pattern name that matched
                    'match': str,     # The actual text that matched
                    'position': tuple # Start and end positions of the match
                }

        Example:
            results = await LeakScannerAdapter.scan_message(
                'CH123', 'U123', 'api_key=secret123'
            )
            print(results[0]['type'])
            'api_key'
        """
        patterns = await LeakScannerAdapter.get_patterns()
        findings = await LeakScannerAdapter._domain.check_for_leaks(patterns, message)

        if findings:
            await LeakScannerAdapter.save_scanned_message(channel_id, user_id, message, findings)

        return findings
