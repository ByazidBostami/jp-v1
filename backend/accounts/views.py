import secrets
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (User, Role, EmailVerificationToken, PasswordResetToken, MobileOTP)
from .serializers import (
    CandidateRegisterSerializer, EmployerRegisterSerializer, LoginSerializer,
    UserSerializer, issue_tokens, make_token)
from .services import log_action
from candidates.models import CandidateProfile
from employers.models import EmployerProfile


class AuthThrottle(ScopedRateThrottle):
    scope = "auth"


def _role(code, name):
    role, _ = Role.objects.get_or_create(code=code, defaults={"name": name})
    return role


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def candidate_register(request):
    s = CandidateRegisterSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    d = s.validated_data
    with transaction.atomic():
        user = User.objects.create_user(
            email=d["email"], password=d["password"], mobile=d["mobile"],
            role=_role(Role.CANDIDATE, "Candidate"), account_status=User.ACTIVE)
        profile = CandidateProfile.objects.create(user=user, full_name=d["full_name"])
        token = EmailVerificationToken.objects.create(user=user, token=make_token())
    log_action(user, "candidate.register", "User", user.id)
    # In production the token is emailed; returned here for dev convenience.
    tokens = issue_tokens(user)
    return Response({
        "user": UserSerializer(user).data,
        "candidate_code": profile.candidate_code,
        "tokens": tokens,
        "email_verification_token": token.token,
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def employer_register(request):
    s = EmployerRegisterSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    d = s.validated_data
    with transaction.atomic():
        user = User.objects.create_user(
            email=d["email"], password=d["password"], mobile=d["telephone"],
            role=_role(Role.EMPLOYER, "Employer"), account_status=User.ACTIVE)
        profile = EmployerProfile.objects.create(
            user=user,
            company_name_english=d["company_name_english"],
            company_name_japanese=d.get("company_name_japanese", ""),
            registration_number=d.get("registration_number", ""),
            representative_name=d["representative_name"],
            contact_person_name=d["contact_person_name"],
            company_email=d["email"],
            telephone=d["telephone"],
        )
    log_action(user, "employer.register", "Employer", profile.id)
    tokens = issue_tokens(user)
    return Response({
        "user": UserSerializer(user).data,
        "employer_code": profile.employer_code,
        "approval_status": profile.approval_status,
        "tokens": tokens,
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def login(request):
    s = LoginSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    user = s.validated_data["user"]
    log_action(user, "auth.login", "User", user.id)
    return Response({"user": UserSerializer(user).data, "tokens": issue_tokens(user)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        RefreshToken(request.data.get("refresh")).blacklist()
    except Exception:
        pass
    return Response({"detail": "Logged out."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    data = UserSerializer(request.user).data
    profile = None
    if request.user.has_role(Role.CANDIDATE):
        cp = getattr(request.user, "candidate_profile", None)
        if cp:
            profile = {"candidate_code": cp.candidate_code,
                       "verification_status": cp.verification_status,
                       "current_status": cp.current_status,
                       "profile_completion_percentage": cp.profile_completion_percentage}
    elif request.user.has_role(Role.EMPLOYER):
        ep = getattr(request.user, "employer_profile", None)
        if ep:
            profile = {"employer_code": ep.employer_code,
                       "company_name": ep.company_name_english,
                       "approval_status": ep.approval_status}
    data["profile"] = profile
    return Response(data)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email(request):
    token = request.data.get("token")
    t = EmailVerificationToken.objects.filter(token=token, used_at__isnull=True).first()
    if not t:
        return Response({"detail": "Invalid or expired token."},
                        status=status.HTTP_400_BAD_REQUEST)
    t.used_at = timezone.now()
    t.save(update_fields=["used_at"])
    t.user.email_verified_at = timezone.now()
    t.user.save(update_fields=["email_verified_at"])
    return Response({"detail": "Email verified."})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def forgot_password(request):
    email = request.data.get("email", "").lower()
    user = User.objects.filter(email__iexact=email).first()
    payload = {"detail": "If the account exists, reset instructions were sent."}
    if user:
        t = PasswordResetToken.objects.create(
            user=user, token=make_token(),
            expires_at=timezone.now() + timedelta(hours=1))
        payload["reset_token"] = t.token  # dev convenience only
    return Response(payload)


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    token = request.data.get("token")
    new_password = request.data.get("password", "")
    t = PasswordResetToken.objects.filter(
        token=token, used_at__isnull=True, expires_at__gt=timezone.now()).first()
    if not t or len(new_password) < 8:
        return Response({"detail": "Invalid token or password too short."},
                        status=status.HTTP_400_BAD_REQUEST)
    t.user.set_password(new_password)
    t.user.save(update_fields=["password"])
    t.used_at = timezone.now()
    t.save(update_fields=["used_at"])
    log_action(t.user, "auth.password_reset", "User", t.user.id)
    return Response({"detail": "Password updated."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_mobile_otp(request):
    code = f"{secrets.randbelow(1000000):06d}"
    MobileOTP.objects.create(user=request.user, code=code,
                             expires_at=timezone.now() + timedelta(minutes=10))
    return Response({"detail": "OTP sent.", "otp": code})  # dev convenience


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_mobile_otp(request):
    code = request.data.get("code")
    otp = MobileOTP.objects.filter(
        user=request.user, code=code, verified_at__isnull=True,
        expires_at__gt=timezone.now()).first()
    if not otp:
        return Response({"detail": "Invalid or expired code."},
                        status=status.HTTP_400_BAD_REQUEST)
    otp.verified_at = timezone.now()
    otp.save(update_fields=["verified_at"])
    request.user.mobile_verified_at = timezone.now()
    request.user.save(update_fields=["mobile_verified_at"])
    return Response({"detail": "Mobile number verified."})
