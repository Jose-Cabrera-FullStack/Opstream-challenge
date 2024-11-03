from django.shortcuts import render
from django.conf import settings
from .infrastructures import SlackConfig


def slack_messages(request, channel_id=None):
    try:
        if channel_id is None:
            channel_id = settings.SLACK_DEFAULT_CHANNEL

        messages = SlackConfig.get_channel_messages(channel_id)
        return render(request, 'leak_shield/slack_messages.html', {
            'messages': messages.get('messages', []),
            'channel_id': channel_id
        })
    except Exception as e:
        return render(request, 'leak_shield/slack_messages.html', {
            'error': str(e)
        })
