import hashlib
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from accounts.permissions import IsCandidate
from accounts.services import log_action
from . import models as m
from . import serializers as s


def get_profile(user):
    return getattr(user, "candidate_profile", None)


class OwnedSubResource(viewsets.ModelViewSet):
    """Base viewset for candidate-owned collections (education, skills, etc.)."""
    permission_classes = [IsCandidate]
    model = None

    def get_queryset(self):
        profile = get_profile(self.request.user)
        return self.model.objects.filter(candidate=profile)

    def perform_create(self, serializer):
        profile = get_profile(self.request.user)
        serializer.save(candidate=profile)
        profile.recompute_completion()

    def perform_update(self, serializer):
        serializer.save()
        get_profile(self.request.user).recompute_completion()

    def perform_destroy(self, instance):
        profile = instance.candidate
        instance.delete()
        profile.recompute_completion()


class AddressViewSet(OwnedSubResource):
    model = m.CandidateAddress
    serializer_class = s.CandidateAddressSerializer


class EducationViewSet(OwnedSubResource):
    model = m.EducationRecord
    serializer_class = s.EducationRecordSerializer


class LanguageViewSet(OwnedSubResource):
    model = m.LanguageQualification
    serializer_class = s.LanguageQualificationSerializer


class SkillTestViewSet(OwnedSubResource):
    model = m.SkillTest
    serializer_class = s.SkillTestSerializer


class WorkExperienceViewSet(OwnedSubResource):
    model = m.WorkExperience
    serializer_class = s.WorkExperienceSerializer


@api_view(["GET", "PUT"])
@permission_classes([IsCandidate])
def profile(request):
    profile = get_profile(request.user)
    if request.method == "GET":
        return Response(s.CandidateProfileSerializer(profile).data)
    ser = s.CandidateProfileSerializer(profile, data=request.data, partial=True)
    ser.is_valid(raise_exception=True)
    ser.save()
    profile.recompute_completion()
    log_action(request.user, "candidate.profile.update", "CandidateProfile", profile.id)
    return Response(s.CandidateProfileSerializer(profile).data)


@api_view(["GET"])
@permission_classes([IsCandidate])
def completion(request):
    profile = get_profile(request.user)
    pct = profile.recompute_completion()
    missing = []
    if not profile.date_of_birth:
        missing.append("Personal information")
    if not profile.addresses.exists():
        missing.append("Address")
    if not profile.education_records.exists():
        missing.append("Education")
    if not profile.language_qualifications.exists():
        missing.append("Japanese language")
    if not profile.documents.exists():
        missing.append("Documents")
    return Response({"profile_completion_percentage": pct, "missing_sections": missing})


@api_view(["POST"])
@permission_classes([IsCandidate])
def submit_profile(request):
    profile = get_profile(request.user)
    pct = profile.recompute_completion()
    if pct < 60:
        return Response(
            {"detail": f"Profile is only {pct}% complete. Complete key sections before submitting."},
            status=status.HTTP_400_BAD_REQUEST)
    old = profile.current_status
    profile.verification_status = "pending"
    profile.current_status = "pending_verification"
    profile.submitted_at = timezone.now()
    profile.save(update_fields=["verification_status", "current_status", "submitted_at"])
    m.CandidateStatusHistory.objects.create(
        candidate=profile, previous_status=old, new_status="pending_verification",
        reason="Candidate submitted profile for verification", changed_by=request.user)
    log_action(request.user, "candidate.profile.submit", "CandidateProfile", profile.id)
    return Response({"detail": "Profile submitted for verification.",
                     "verification_status": profile.verification_status})


class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCandidate]
    serializer_class = s.CandidateDocumentSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return m.CandidateDocument.objects.filter(
            candidate=get_profile(self.request.user), deleted_at__isnull=True)

    def perform_create(self, serializer):
        profile = get_profile(self.request.user)
        upload = self.request.FILES.get("file")
        if upload:
            data = upload.read()
            upload.seek(0)
            serializer.save(
                candidate=profile, original_filename=upload.name,
                mime_type=getattr(upload, "content_type", ""), file_size=upload.size,
                checksum=hashlib.sha256(data).hexdigest())
        else:
            serializer.save(candidate=profile)
        profile.recompute_completion()
        log_action(self.request.user, "candidate.document.upload", "CandidateDocument")

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at"])
