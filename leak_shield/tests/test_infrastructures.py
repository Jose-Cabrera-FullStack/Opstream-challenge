"""
Test module for SlackConfig infrastructure class.
Tests Slack API integration and configuration management.
"""
import pytest
from unittest.mock import patch, MagicMock
from slack_sdk.errors import SlackApiError
from leak_shield.infrastructures import SlackConfig

# Remove global asyncio mark since not all tests are async
# pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_settings():
    """Fixture to provide mock settings for tests"""
    with patch('leak_shield.infrastructures.settings') as mock_settings:
        mock_settings.SLACK_CLIENT_ID = 'test_client_id'
        mock_settings.SLACK_CLIENT_SECRET = 'test_client_secret'
        mock_settings.SLACK_SIGNING_SECRET = 'test_signing_secret'
        mock_settings.SLACK_BOT_TOKEN = 'xoxb-test-token'
        yield mock_settings


@pytest.fixture
def mock_slack_client():
    """Fixture to provide mock Slack client"""
    with patch('leak_shield.infrastructures.WebClient') as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.auth_test.return_value = {
            'ok': True,
            'user': 'test_bot',
            'team': 'test_team'
        }
        yield mock_instance


class TestSlackConfig:
    def setup_method(self):
        """Reset SlackConfig state before each test"""
        SlackConfig._client = None
        SlackConfig._bot_token = None

    def test_initialize_missing_env_vars(self):
        """Test initialization fails with missing environment variables"""
        with patch('leak_shield.infrastructures.settings') as mock_settings:
            # Remove hasattr so getattr raises AttributeError
            delattr(mock_settings, 'SLACK_CLIENT_ID')
            delattr(mock_settings, 'SLACK_CLIENT_SECRET')
            delattr(mock_settings, 'SLACK_SIGNING_SECRET')
            delattr(mock_settings, 'SLACK_BOT_TOKEN')

            with pytest.raises(ValueError) as exc_info:
                SlackConfig.initialize()

            assert "Missing required settings variables" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_settings, mock_slack_client):
        """Test successful message sending"""
        mock_response = {'ok': True, 'ts': '1234.5678'}
        mock_slack_client.chat_postMessage.return_value = mock_response

        # Set client directly to avoid initialization
        SlackConfig._client = mock_slack_client
        response = await SlackConfig.send_message('channel', 'test message')

        assert response == mock_response
        mock_slack_client.chat_postMessage.assert_called_once_with(
            channel='channel',
            text='test message'
        )

    @pytest.mark.asyncio
    async def test_send_message_failure(self, mock_settings, mock_slack_client):
        """Test message sending failure"""
        mock_slack_client.chat_postMessage.side_effect = SlackApiError(
            "Channel not found", {'error': 'channel_not_found'}
        )

        SlackConfig._client = mock_slack_client  # Set client directly
        with pytest.raises(Exception) as exc_info:
            await SlackConfig.send_message('invalid-channel', 'test')
        assert "Failed to send message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_message_success(self, mock_settings, mock_slack_client):
        """Test successful message update"""
        mock_response = {'ok': True}
        mock_slack_client.chat_update.return_value = mock_response

        SlackConfig._client = mock_slack_client  # Set client directly
        response = await SlackConfig.update_message('channel', '1234.5678', 'updated text')

        assert response == mock_response
        mock_slack_client.chat_update.assert_called_once_with(
            channel='channel',
            ts='1234.5678',
            text='updated text'
        )

    def test_get_channel_messages_success(self, mock_settings, mock_slack_client):
        """Test successful retrieval of channel messages"""
        mock_response = {
            'ok': True,
            'messages': [{'text': 'test message'}]
        }
        mock_slack_client.conversations_history.return_value = mock_response
        mock_slack_client.conversations_info.return_value = {
            'channel': {'id': 'C1234'}
        }

        SlackConfig._client = mock_slack_client  # Set client directly
        response = SlackConfig.get_channel_messages('C1234', limit=10)

        assert response == mock_response
        mock_slack_client.conversations_history.assert_called_once_with(
            channel='C1234',
            limit=10
        )
