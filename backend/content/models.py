from django.db import models
from django.conf import settings


class Notification(models.Model):
    CHANNEL = [("dashboard", "Dashboard"), ("email", "Email"),
               ("sms", "SMS"), ("whatsapp", "WhatsApp")]
    DELIVERY = [("pending", "Pending"), ("sent", "Sent"), ("failed", "Failed")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=60)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data_json = models.JSONField(null=True, blank=True)
    channel = models.CharField(max_length=15, choices=CHANNEL, default="dashboard")
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(max_length=10, choices=DELIVERY, default="sent")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class HomepageStatistic(models.Model):
    statistic_code = models.CharField(max_length=60, unique=True)
    statistic_label = models.CharField(max_length=150)
    calculated_value = models.BigIntegerField(default=0)
    manual_override_value = models.BigIntegerField(null=True, blank=True)
    use_manual_override = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    last_calculated_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order"]

    @property
    def value(self):
        if self.use_manual_override and self.manual_override_value is not None:
            return self.manual_override_value
        return self.calculated_value


class ContentPage(models.Model):
    STATUS = [("draft", "Draft"), ("published", "Published")]
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    language_code = models.CharField(max_length=5, default="en")
    page_type = models.CharField(max_length=50, default="page")
    content = models.TextField(blank=True)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="draft")
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("slug", "language_code")


class SystemSetting(models.Model):
    setting_group = models.CharField(max_length=60)
    setting_key = models.CharField(max_length=100, unique=True)
    setting_value = models.TextField(blank=True)
    data_type = models.CharField(max_length=20, default="string")
    is_public = models.BooleanField(default=False)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    organisation = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    telephone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    user_type = models.CharField(max_length=50, blank=True)
    is_handled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


def notify(user, notification_type, title, message, data=None, channel="dashboard"):
    from django.utils import timezone
    return Notification.objects.create(
        user=user, notification_type=notification_type, title=title,
        message=message, data_json=data, channel=channel,
        sent_at=timezone.now(), delivery_status="sent")
