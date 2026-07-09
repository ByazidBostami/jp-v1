import secrets
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Role, EmailVerificationToken, PasswordResetToken, MobileOTP


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="role.code", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)
    email_verified = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["uuid", "email", "mobile", "role", "role_name",
                  "account_status", "email_verified", "last_login_at"]

    def get_email_verified(self, obj):
        return obj.email_verified_at is not None


class CandidateRegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    mobile = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    consent_privacy = serializers.BooleanField()
    consent_terms = serializers.BooleanField()

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("The email address is already registered.")
        return value.lower()

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        if not (data["consent_privacy"] and data["consent_terms"]):
            raise serializers.ValidationError(
                "You must accept the privacy policy and terms to register.")
        return data


class EmployerRegisterSerializer(serializers.Serializer):
    company_name_english = serializers.CharField(max_length=200)
    company_name_japanese = serializers.CharField(max_length=200, required=False, allow_blank=True)
    registration_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    representative_name = serializers.CharField(max_length=150)
    contact_person_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    telephone = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    consent_rules = serializers.BooleanField()

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("The email address is already registered.")
        return value.lower()

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        if not data["consent_rules"]:
            raise serializers.ValidationError("You must accept the platform rules.")
        return data


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            user = User.objects.get(email__iexact=data["email"])
        except User.DoesNotExist:
            user = User.objects.filter(mobile=data["email"]).first()
        if user is None:
            raise serializers.ValidationError("Invalid credentials.")

        if user.locked_until and user.locked_until > timezone.now():
            raise serializers.ValidationError(
                "Account temporarily locked due to failed login attempts.")

        auth_user = authenticate(username=user.email, password=data["password"])
        if auth_user is None:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = timezone.now() + timedelta(minutes=15)
                user.failed_login_attempts = 0
            user.save(update_fields=["failed_login_attempts", "locked_until"])
            raise serializers.ValidationError("Invalid credentials.")

        if user.account_status == User.SUSPENDED:
            raise serializers.ValidationError("This account has been suspended.")

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = timezone.now()
        user.save(update_fields=["failed_login_attempts", "locked_until", "last_login_at"])
        data["user"] = user
        return data


def issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role_code
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def make_token():
    return secrets.token_urlsafe(32)
