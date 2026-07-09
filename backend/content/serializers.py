from rest_framework import serializers
from . import models as m


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Notification
        fields = ["id", "notification_type", "title", "message", "data_json",
                  "channel", "read_at", "created_at"]


class HomepageStatisticSerializer(serializers.ModelSerializer):
    value = serializers.IntegerField(read_only=True)

    class Meta:
        model = m.HomepageStatistic
        fields = ["id", "statistic_code", "statistic_label", "value",
                  "is_visible", "display_order"]


class ContentPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ContentPage
        fields = ["id", "title", "slug", "language_code", "page_type", "content",
                  "meta_title", "meta_description", "status", "published_at"]


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ContactMessage
        fields = ["name", "organisation", "country", "email", "telephone",
                  "subject", "message", "user_type"]
