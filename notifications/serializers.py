from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    # Extra read-only fields for display
    sender_name = serializers.SerializerMethodField()
    user_name   = serializers.SerializerMethodField()

    class Meta:
        model  = Notification
        fields = [
            'id', 'title', 'message', 'type',
            'is_read', 'created_at',
            'sender_name', 'user_name',
        ]
        read_only_fields = ['id', 'created_at']

    def get_sender_name(self, obj):
        # Notification model may not have sender — handle gracefully
        sender = getattr(obj, 'sender', None)
        if sender:
            return sender.full_name
        return 'System'

    def get_user_name(self, obj):
        return obj.user.full_name if obj.user else '—'