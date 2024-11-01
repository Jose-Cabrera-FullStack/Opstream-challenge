"""
Leak Shield Models Module

This module contains the core models for the Leak Shield application, which manages
data leak prevention in Slack channels. The models are organized as follows:

- Pattern: Stores regex patterns for detecting sensitive information
- ScannedMessage: Records Slack messages that match sensitive patterns
- ScannedFile: Tracks files that contain sensitive information
- ActionLog: Logs actions taken on detected sensitive content
- SlackChannel: Manages monitored Slack channels

These models work together to provide a complete audit trail of detected sensitive
information and actions taken to prevent data leaks.
"""

from django.db import models


class Pattern(models.Model):
    """
    Stores text patterns used to detect sensitive information in messages and files.

    This model is the foundation of the detection system, containing regex patterns
    that are used to scan both messages and files in Slack channels. Each pattern
    can be associated with multiple ScannedMessage and ScannedFile instances.

    Key fields:
        - name: Unique identifier for the pattern
        - regex: Regular expression used for pattern matching
        - description: Detailed explanation of what the pattern detects

    Relationships:
        - Has many ScannedMessages (through matched_messages)
        - Has many ScannedFiles (through matched_files)
    """
    name = models.CharField(max_length=100, unique=True)
    regex = models.CharField(
        max_length=255,
        help_text="Regular expression used for pattern matching."
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the pattern."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.name)


class ScannedMessage(models.Model):
    """
    Records Slack messages that have been identified as containing sensitive information.

    This model maintains a record of messages that matched one or more patterns,
    storing both the message content and metadata about where and when it was detected.
    It serves as an audit trail for detected sensitive information in messages.

    Key fields:
        - channel_id: ID of the Slack channel where the message was detected
        - user_id: ID of the Slack user who sent the message
        - message_text: Original content of the flagged message

    Relationships:
        - Belongs to one Pattern (foreign key)
        - Has many ActionLogs (through actions)
    """
    channel_id = models.CharField(max_length=50)
    user_id = models.CharField(max_length=50)
    message_text = models.TextField(
        help_text="Original content of the message."
    )
    pattern = models.ForeignKey(
        Pattern,
        on_delete=models.CASCADE,
        related_name="matched_messages"
    )
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
            Meta options for the ScannedMessage model.
        """
        ordering = ['-detected_at']
        verbose_name = 'Scanned Message'
        verbose_name_plural = 'Scanned Messages'

    def __str__(self) -> str:
        return f"Message from {self.user_id} in {self.channel_id}"


class ScannedFile(models.Model):
    """
    Tracks files shared in Slack that contain sensitive information.

    Similar to ScannedMessage, this model maintains records of files that
    triggered pattern matches. It stores both the file content and metadata
    for audit purposes.

    Key fields:
        - file_name: Name of the uploaded file
        - file_content: Extracted text content from the file

    Relationships:
        - Belongs to one Pattern (foreign key)
        - Has many ActionLogs (through actions)
    """
    file_name = models.CharField(max_length=255)
    file_content = models.TextField(
        help_text="Extracted text content from the file for pattern analysis.")
    pattern = models.ForeignKey(
        Pattern, on_delete=models.CASCADE, related_name="matched_files")
    detected_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.file_name)


class ActionLog(models.Model):
    """
    Records all actions taken in response to detected sensitive information.

    This model serves as a comprehensive audit log of all automated or manual
    actions performed when sensitive information is detected. It can be linked
    to either a message or file, providing a complete history of interventions.

    Key fields:
        - action_type: Type of action taken (BLOCK/REPLACE/ALERT)
        - action_details: Specific details about the action

    Relationships:
        - May belong to one ScannedMessage (optional foreign key)
        - May belong to one ScannedFile (optional foreign key)
    """
    ACTION_CHOICES = [
        ('BLOCK', 'Message Blocked'),
        ('REPLACE', 'Message Replaced'),
        ('ALERT', 'Alert Sent')
    ]

    message = models.ForeignKey(
        ScannedMessage,
        on_delete=models.CASCADE,
        related_name="actions",
        null=True,
        blank=True
    )
    file = models.ForeignKey(
        ScannedFile,
        on_delete=models.CASCADE,
        related_name="actions",
        null=True,
        blank=True
    )
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    action_details = models.TextField(
        help_text="Additional details about the action taken."
    )
    action_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{dict(self.ACTION_CHOICES).get(self.action_type, 'Unknown')} on {self.action_date}"


class SlackChannel(models.Model):
    """
    Manages the list of Slack channels being monitored by the system.

    This model maintains the configuration of which Slack channels should be
    monitored for sensitive information. It allows for selective monitoring
    and can be toggled active/inactive as needed.

    Key fields:
        - channel_id: Unique Slack channel identifier
        - name: Human-readable channel name
        - is_active: Toggle for enabling/disabling monitoring
    """
    channel_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return str(self.name)
