from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsCandidate, IsApprovedEmployer, IsAdminStaff
from accounts.services import log_action
from candidates.views import get_profile
from content.models import notify
from . import models as m
from . import serializers as s


# ---------- Public ----------
class PublicJobViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = s.JobPublicSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["program_type", "job_sector", "work_prefecture", "job_status"]
    search_fields = ["title", "work_city", "description"]

    def get_queryset(self):
        return m.Job.objects.filter(
            approval_status="published", deleted_at__isnull=True
        ).select_related("program_type", "job_sector", "work_prefecture", "requirement")


# ---------- Candidate ----------
@api_view(["GET"])
@permission_classes([IsCandidate])
def candidate_jobs(request):
    qs = m.Job.objects.filter(approval_status="published", job_status="open")
    return Response(s.JobPublicSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsCandidate])
def apply_job(request, job_id):
    profile = get_profile(request.user)
    if profile.verification_status != "verified":
        return Response({"detail": "Only verified candidates can apply."},
                        status=status.HTTP_403_FORBIDDEN)
    job = m.Job.objects.filter(id=job_id, approval_status="published").first()
    if not job:
        return Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
    app, created = m.JobApplication.objects.get_or_create(
        job=job, candidate=profile,
        defaults={"applied_by": request.user,
                  "candidate_notes": request.data.get("candidate_notes", "")})
    if not created:
        return Response({"detail": "You have already applied for this job."},
                        status=status.HTTP_400_BAD_REQUEST)
    log_action(request.user, "candidate.job.apply", "JobApplication", app.id)
    return Response(s.JobApplicationSerializer(app).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsCandidate])
def candidate_applications(request):
    profile = get_profile(request.user)
    qs = m.JobApplication.objects.filter(candidate=profile).select_related("job")
    return Response(s.JobApplicationSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsCandidate])
def withdraw_application(request, application_id):
    profile = get_profile(request.user)
    app = m.JobApplication.objects.filter(id=application_id, candidate=profile).first()
    if not app:
        return Response({"detail": "Application not found."}, status=404)
    app.application_status = "withdrawn"
    app.save(update_fields=["application_status"])
    return Response({"detail": "Application withdrawn."})


# ---------- Employer ----------
class EmployerJobViewSet(viewsets.ModelViewSet):
    permission_classes = [IsApprovedEmployer]
    serializer_class = s.JobEmployerSerializer

    def get_queryset(self):
        return m.Job.objects.filter(
            employer=self.request.user.employer_profile, deleted_at__isnull=True)

    def perform_create(self, serializer):
        job = serializer.save(employer=self.request.user.employer_profile,
                              approval_status="draft")
        log_action(self.request.user, "employer.job.create", "Job", job.id)

    def perform_destroy(self, instance):
        if instance.approval_status != "draft":
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Only draft jobs can be deleted.")
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at"])


@api_view(["POST"])
@permission_classes([IsApprovedEmployer])
def submit_job(request, job_id):
    job = m.Job.objects.filter(id=job_id, employer=request.user.employer_profile).first()
    if not job:
        return Response({"detail": "Job not found."}, status=404)
    if job.approval_status not in ("draft", "correction_required"):
        return Response({"detail": "Job cannot be submitted in its current state."}, status=400)
    job.approval_status = "pending"
    job.save(update_fields=["approval_status"])
    log_action(request.user, "employer.job.submit", "Job", job.id)
    return Response({"detail": "Job submitted for admin approval.",
                     "approval_status": job.approval_status})


# ---------- Shortlists (employer) ----------
class ShortlistViewSet(viewsets.ModelViewSet):
    permission_classes = [IsApprovedEmployer]
    serializer_class = s.ShortlistSerializer

    def get_queryset(self):
        return m.EmployerShortlist.objects.filter(
            employer=self.request.user.employer_profile).exclude(shortlist_status="removed")

    def perform_create(self, serializer):
        serializer.save(employer=self.request.user.employer_profile,
                        shortlisted_by=self.request.user)

    def perform_destroy(self, instance):
        instance.shortlist_status = "removed"
        instance.save(update_fields=["shortlist_status"])
