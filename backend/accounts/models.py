import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class Role(models.Model):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    VERIFIER = "verifier"
    INTERVIEWER = "interviewer"
    EMPLOYER = "employer"
    CANDIDATE = "candidate"

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Permission(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("role", "permission")


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("account_status", User.ACTIVE)
        role, _ = Role.objects.get_or_create(
            code=Role.SUPER_ADMIN, defaults={"name": "Super Administrator"})
        extra.setdefault("role", role)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    STATUS_CHOICES = [
        (ACTIVE, "Active"), (PENDING, "Pending"),
        (SUSPENDED, "Suspended"), (LOCKED, "Locked"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="users", null=True)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=20, blank=True, db_index=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    mobile_verified_at = models.DateTimeField(null=True, blank=True)
    account_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    last_login_at = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    @property
    def role_code(self):
        return self.role.code if self.role else None

    def has_role(self, *codes):
        return self.role_code in codes

    @property
    def is_admin_staff(self):
        return self.has_role(Role.SUPER_ADMIN, Role.ADMIN, Role.VERIFIER, Role.INTERVIEWER)


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_tokens")
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_tokens")
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class MobileOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    """SRS §7.32 — every sensitive action is logged."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100, blank=True)
    entity_id = models.CharField(max_length=64, blank=True)
    old_values_json = models.JSONField(null=True, blank=True)
    new_values_json = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
