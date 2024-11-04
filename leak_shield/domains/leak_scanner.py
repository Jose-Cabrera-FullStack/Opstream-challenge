"""
Leak Shield Domain Module

This module provides functionality for scanning files and messages for potential
sensitive information leaks such as API keys, passwords, and private keys.
"""

import re


class LeakScannerDomain:
    """
    Domain class for scanning files and messages for potential sensitive information leaks.
    """

    async def check_for_leaks(self, patterns: list, content: str) -> list:
        """
        Scan content for potential sensitive information leaks using patterns from database.

        Args:
            patterns (list): List of patterns to check against
            content (str): The text content to scan for leaks

        Returns:
            list: A list of dictionaries containing details about found leaks
        """
        findings = []

        for pattern in patterns:
            matches = re.finditer(pattern.regex, content)
            for match in matches:
                findings.append({
                    'type': pattern.name,
                    'match': match.group(0),
                    'position': match.span()
                })
        return findings
