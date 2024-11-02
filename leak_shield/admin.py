"""
Leak Shield Admin Configuration Module

This module configures the Django admin interface for the Leak Shield application.
It provides administrative views for managing patterns, monitoring scanned messages
and files, tracking actions, and configuring Slack channels.

Each admin class is customized with specific list displays, filters, and search
capabilities to facilitate efficient management of the DLP system.
"""

from django.contrib import admin
from .models import Pattern, ScannedMessage, ScannedFile, ActionLog, SlackChannel


@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    """
    Admin interface for Pattern model.

    Provides interface for managing DLP detection patterns with features for:
    - Viewing and editing regex patterns
    - Searching patterns by name and content
    - Filtering by creation/update dates
    """
    list_display = ('name', 'regex', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'regex', 'description')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ScannedMessage)
class ScannedMessageAdmin(admin.ModelAdmin):
    """
    Admin interface for ScannedMessage model.

    Manages messages flagged by the DLP system with features for:
    - Viewing message content and metadata
    - Filtering by channel, pattern, and detection date
    - Searching through message content and user details
    """
    list_display = ('user_id', 'channel_id', 'message_preview',
                    'pattern', 'detected_at')
    search_fields = ('user_id', 'channel_id', 'message_text')
    list_filter = ('detected_at', 'pattern', 'channel_id')
    readonly_fields = ('detected_at',)

    def message_preview(self, obj):
        """Generate a truncated preview of the message content."""
        return obj.message_text[:100] + '...' if len(obj.message_text) > 100 else obj.message_text
    message_preview.short_description = 'Message Content'


@admin.register(ScannedFile)
class ScannedFileAdmin(admin.ModelAdmin):
    """
    Admin interface for ScannedFile model.

    Manages files scanned by the DLP system with features for:
    - Viewing file content and metadata
    - Filtering by pattern and detection date
    - Searching through file names and content
    """
    list_display = ('file_name', 'content_preview', 'pattern', 'detected_at')
    search_fields = ('file_name', 'file_content')
    list_filter = ('detected_at', 'pattern')
    readonly_fields = ('detected_at',)

    def content_preview(self, obj):
        """Generate a truncated preview of the file content."""
        return obj.file_content[:100] + '...' if len(obj.file_content) > 100 else obj.file_content
    content_preview.short_description = 'File Content'


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    """
    Admin interface for ActionLog model.

    Tracks all DLP system actions with features for:
    - Viewing action details and targets
    - Filtering by action type and date
    - Searching through action details
    """
    list_display = ('action_type', 'action_date',
                    'get_target', 'action_details')
    list_filter = ('action_type', 'action_date')
    search_fields = ('action_details',)
    readonly_fields = ('action_date',)

    def get_target(self, obj):
        """Determine and format the target of the action (message or file)."""
        if obj.message:
            return f"Message: {obj.message}"
        elif obj.file:
            return f"File: {obj.file}"
        return "No target"
    get_target.short_description = 'Target'


@admin.register(SlackChannel)
class SlackChannelAdmin(admin.ModelAdmin):
    """
    Admin interface for SlackChannel model.

    Manages monitored Slack channels with features for:
    - Viewing channel details and status
    - Filtering by active status
    - Searching through channel names and IDs
    """
    list_display = ('name', 'channel_id', 'is_active')
    search_fields = ('name', 'channel_id')
    list_filter = ('is_active',)
