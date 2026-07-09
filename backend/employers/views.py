from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import ListAPIView, RetrieveAPIView

from accounts.permissions import IsEmployer, IsApprovedEmployer
from accounts.services import log_action
from candidates.models import CandidateProfile
from candidates.serializers import (
    CandidateEmployerCardSerializer, CandidateEmployerDetailSerializer)
from . import models as m
from . import serializers as s


@api_view(["GET", "PUT"])
@permission_classes([IsEmployer])
def profile(request):
    ep = request.user.employer_profile
    if request.method == "GET":
        return Response(s.EmployerProfileSerializer(ep).data)
    ser = s.EmployerProfileSerializer(ep, data=request.data, partial=True)
    ser.is_valid(raise_exception=True)
    ser.save()
    log_action(request.user, "employer.profile.update", "EmployerProfile", ep.id)
    return Response(ser.data)


@api_view(["GET"])
@permission_classes([IsEmployer])
def approval_status(request):
    ep = request.user.employer_profile
    return Response({"approval_status": ep.approval_status,
                     "employer_code": ep.employer_code})


class EmployerDocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsEmployer]
    serializer_class = s.EmployerDocumentSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return m.EmployerDocument.objects.filter(employer=self.request.user.employer_profile)

    def perform_create(self, serializer):
        upload = self.request.FILES.get("file")
        extra = {}
        if upload:
            extra = {"original_filename": upload.name,
                     "mime_type": getattr(upload, "content_type", ""),
                     "file_size": upload.size}
        serializer.save(employer=self.request.user.employer_profile, **extra)


# ---- PRIVACY-ENFORCED candidate search (SRS §14, §17) ------------------
class EmployerCandidateSearch(ListAPIView):
    """Approved employers see only verified candidate summaries, never
    contact details. Serializer strips all sensitive fields."""
    permission_classes = [IsApprovedEmployer]
    serializer_class = CandidateEmployerCardSerializer
    filter_backends = [filters.OrderingFilter]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["employer"] = self.request.user.employer_profile
        return ctx

    def get_queryset(self):
        qs = CandidateProfile.objects.filter(
            verification_status="verified", deleted_at__isnull=True
        ).prefetch_related("education_records", "language_qualifications",
                           "skill_tests", "work_experiences")
        p = self.request.query_params
        if p.get("gender"):
            qs = qs.filter(gender=p["gender"])
        if p.get("availability_status"):
            qs = qs.filter(availability_status=p["availability_status"])
        if p.get("job_sector"):
            qs = qs.filter(job_preferences__code=p["job_sector"])
        if p.get("program_type"):
            qs = qs.filter(program_preferences__code=p["program_type"])
        if p.get("japanese_level"):
            qs = qs.filter(language_qualifications__level=p["japanese_level"],
                           language_qualifications__result_status="passed")
        if p.get("skill_test_status") == "passed":
            qs = qs.filter(skill_tests__result_status="passed")
        return qs.distinct()


class EmployerCandidateDetail(RetrieveAPIView):
    permission_classes = [IsApprovedEmployer]
    serializer_class = CandidateEmployerDetailSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["employer"] = self.request.user.employer_profile
        return ctx

    def get_queryset(self):
        return CandidateProfile.objects.filter(verification_status="verified")

    def retrieve(self, request, *args, **kwargs):
        log_action(request.user, "employer.candidate.view", "CandidateProfile",
                   kwargs.get("pk"))
        return super().retrieve(request, *args, **kwargs)
