"""
Slack infrastructure configuration and utilities.
"""
from typing import Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
from django.conf import settings


class SlackConfig:
    """
    Static configuration class for Slack API integration.
    Handles authentication, client initialization and basic message operations.
    """
    _client = None
    _bot_token = None

    @classmethod
    def initialize(cls) -> None:
        """Initialize Slack configuration and client"""
        cls._validate_env()
        cls._bot_token = settings.SLACK_BOT_TOKEN
        cls._client = WebClient(token=cls._bot_token)

    @staticmethod
    def _validate_env() -> None:
        """Validate required environment variables"""
        required_vars = [
            'SLACK_CLIENT_ID',
            'SLACK_CLIENT_SECRET',
            'SLACK_SIGNING_SECRET',
            'SLACK_BOT_TOKEN'
        ]
        missing = [var for var in required_vars if not hasattr(settings, var)]
        if missing:
            raise ValueError(
                f"Missing required settings variables: {', '.join(missing)}")

    @classmethod
    def get_client(cls) -> WebClient:
        """Get initialized Slack client"""
        if cls._client is None:
            cls.initialize()
        return cls._client

    @classmethod
    async def send_message(cls, channel: str, text: str) -> Dict[str, Any]:
        """
        Send a message to a Slack channel

        Args:
            channel: Channel ID or name
            text: Message text to send

        Returns:
            Dict containing the API response
        """
        try:
            return cls.get_client().chat_postMessage(
                channel=channel,
                text=text
            )
        except SlackApiError as e:
            raise Exception(f"Failed to send message: {str(e)}")

    @classmethod
    async def update_message(cls, channel: str, ts: str, text: str) -> Dict[str, Any]:
        """
        Update an existing message

        Args:
            channel: Channel ID where message exists
            ts: Timestamp of message to update
            text: New message text

        Returns:
            Dict containing the API response
        """
        try:
            return cls.get_client().chat_update(
                channel=channel,
                ts=ts,
                text=text
            )
        except SlackApiError as e:
            raise Exception(f"Failed to update message: {str(e)}")

    @classmethod
    async def delete_message(cls, channel: str, ts: str) -> Dict[str, Any]:
        """
        Delete a message

        Args:
            channel: Channel ID where message exists
            ts: Timestamp of message to delete

        Returns:
            Dict containing the API response
        """
        try:
            return cls.get_client().chat_delete(
                channel=channel,
                ts=ts
            )
        except SlackApiError as e:
            raise Exception(f"Failed to delete message: {str(e)}")

    @classmethod
    def get_channel_messages(cls, channel: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get messages from a channel

        Args:
            channel: Channel ID to fetch messages from
            limit: Maximum number of messages to return

        Returns:
            Dict containing the messages
        """
        try:
            return cls.get_client().conversations_history(
                channel=channel,
                limit=limit
            )
        except SlackApiError as e:
            raise Exception(f"Failed to fetch messages: {str(e)}")

    @classmethod
    def verify_signature(cls, timestamp: str, signature: str, body: str) -> bool:
        """
        Verify request signature from Slack

        Args:
            timestamp: Request timestamp
            signature: Request signature
            body: Raw request body

        Returns:
            bool indicating if signature is valid
        """
        verifier = SignatureVerifier(settings.SLACK_SIGNING_SECRET)
        return verifier.is_valid(body, timestamp, signature)
