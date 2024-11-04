import os
from typing import List
from asgiref.sync import sync_to_async
from django.db import transaction
from leak_shield.domains import LeakScannerDomain
from leak_shield.models import Pattern, ScannedMessage, ScannedFile, ActionLog


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
        return list(Pattern.objects.all())

    @staticmethod
    @sync_to_async
    def save_scanned_message(
        channel_id: str,
        user_id: str,
        message: str,
        findings: List[dict]
    ) -> None:
        """Save message scan results to database"""
        with transaction.atomic():
            pattern_types = {finding['type'] for finding in findings}

            for pattern_type in pattern_types:
                pattern = Pattern.objects.select_for_update().get(name=pattern_type)

                # Check if message already exists for this pattern
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
        """Save file scan results to database"""
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
        findings = await LeakScannerAdapter._domain.check_for_leaks(patterns, content)

        if findings:
            file_name = os.path.basename(file_path)
            await LeakScannerAdapter.save_scanned_file(file_name, content, findings)

        return findings

    @staticmethod
    async def scan_message(channel_id: str, user_id: str, message: str) -> List[dict]:
        """
        Scan and store message results
        """
        patterns = await LeakScannerAdapter.get_patterns()
        findings = await LeakScannerAdapter._domain.check_for_leaks(patterns, message)

        if findings:
            await LeakScannerAdapter.save_scanned_message(channel_id, user_id, message, findings)

        return findings
