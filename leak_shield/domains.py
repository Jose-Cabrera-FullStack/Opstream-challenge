"""
Leak Shield Domain Module

This module provides functionality for scanning files and messages for potential
sensitive information leaks such as API keys, passwords, and private keys.
It uses regular expressions to identify common patterns of sensitive data.

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


class LeakScanner:
    """
    A static class for scanning files and messages for potential sensitive information leaks.

    This class provides methods to detect patterns that might indicate leaked credentials,
    API keys, passwords, or other sensitive information.
    """

    SENSITIVE_PATTERNS = {
        'api_key': r'([a-zA-Z0-9_-]*(?:api|key|token|secret)[a-zA-Z0-9_-]*\s*[=:]\s*[\'""][a-zA-Z0-9_-]+[\'""])',
        'password': r'(?i)(password\s*[=:]\s*[\'""][^\'""]+[\'""])',
        'private_key': r'-----BEGIN\s+PRIVATE\s+KEY-----[^-]+-----END\s+PRIVATE\s+KEY-----',
        'aws_key': r'(?i)(aws[_-]?(?:access[_-]?)?key[_-]?id\s*[=:]\s*[\'""][A-Z0-9]+[\'""])'
    }

    @staticmethod
    def check_for_leaks(content: str) -> list:
        """
        Scan content for potential sensitive information leaks using predefined patterns.

        Args:
            content (str): The text content to scan for leaks

        Returns:
            list: A list of dictionaries containing details about found leaks:
                 - type: The type of leak found (e.g., 'api_key', 'password')
                 - match: The actual matched text
                 - position: Tuple of start and end positions of the match
        """
        findings = []
        for leak_type, pattern in LeakScanner.SENSITIVE_PATTERNS.items():
            matches = re.finditer(pattern, content)
            for match in matches:
                findings.append({
                    'type': leak_type,
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
        return LeakScanner.check_for_leaks(content)

    @staticmethod
    async def scan_message(message: str) -> List[dict]:
        """
        Asynchronously scan a message or string for potential sensitive information leaks.

        Args:
            message (str): The message content to scan

        Returns:
            List[dict]: A list of dictionaries containing details about found leaks
        """
        return LeakScanner.check_for_leaks(message)
