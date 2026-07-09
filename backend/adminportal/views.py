from django.utils import timezone
from django.db.models import Count
from rest_framework import status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.generics import ListAPIView

from accounts.permissions import IsAdminStaff
from accounts.services import log_action
from candidates.models import CandidateProfile, CandidateStatusHistory, CandidateDocument
from candidates.serializers import CandidateProfileSerializer, StatusHistorySerializer, CandidateDocumentSerializer
from employers.models import EmployerProfile
from employers.serializers import EmployerAdminSerializer
from jobs.models import Job, JobApplication
from jobs.serializers import JobEmployerSerializer
from interviews.models import InterviewRequest, Interview, InterviewCandidate
from interviews.serializers import InterviewRequestSerializer, InterviewSerializer
from content.models import notify
from content.services import recompute_homepage_statistics


def _set_status(candidate, new_status, user, reason=""):
    old = candidate.current_status
    candidate.current_status = new_status
    candidate.save(update_fields=["current_status"])
    CandidateStatusHistory.objects.create(
        candidate=candidate, previous_status=old, new_status=new_status,
        reason=reason, changed_by=user)


# ---------------- Candidate management ----------------
class AdminCandidateList(ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = CandidateProfileSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["candidate_code", "full_name"]

    def get_queryset(self):
        qs = CandidateProfile.objects.filter(deleted_at__isnull=True).order_by("-created_at")
        p = self.request.query_params
        for field in ["verification_status", "current_status", "availability_status", "gender"]:
            if p.get(field):
                qs = qs.filter(**{field: p[field]})
        return qs


@api_view(["GET", "PUT"])
@permission_classes([IsAdminStaff])
def admin_candidate_detail(request, candidate_id):
    c = CandidateProfile.objects.filter(id=candidate_id).first()
    if not c:
        return Response({"detail": "Candidate not found."}, status=404)
    if request.method == "GET":
        return Response(CandidateProfileSerializer(c).data)
    ser = CandidateProfileSerializer(c, data=request.data, partial=True)
    ser.is_valid(raise_exception=True)
    ser.save()
    log_action(request.user, "admin.candidate.update", "CandidateProfile", c.id)
    return Response(ser.data)


@api_view(["POST"])
@permission_classes([IsAdminStaff])
def admin_candidate_approve(request, candidate_id):
    c = CandidateProfile.objects.filter(id=candidate_id).first()
    if not c:
        return Response({"detail": "Candidate not found."}, status=404)
    c.verification_status = "verified"
    c.verified_at = timezone.now()
    c.save(update_fields=["verification_status", "verified_at"])
    _set_status(c, "verified", request.user, "Profile approved by admin")
    notify(c.user, "profile_approved", "Profile approved",
           "Your profile has been verified. Employers can now discover your profile.")
    log_action(request.user, "admin.candidate.approve", "CandidateProfile", c.id)
    return Response({"detail": "Candidate approved.", "verification_status": "verified"})


@api_view(["POST"])
@permission_classes([IsAdminStaff])
def admin_candidate_reject(request, candidate_id):
    c = CandidateProfile.objects.filter(id=candidate_id).first()
    if not c:
        return Response({"detail": "Candidate not found."}, status=404)
    reason = request.data.get("reason", "")
    c.verification_status = "rejected"
    c.save(update_fields=["verification_status"])
    _set_status(c, "rejected", request.user, reason)
    notify(c.user, "profile_rejected", "Profile not approved",
           reason or "Your profile could not be verified. Please contact support.")
    return Response({"detail": "Candidate rejected."})


@api_view(["POST"])
@permission_classes([IsAdminStaff])
def admin_candidate_request_correction(request, candidate_id):
    c = CandidateProfile.objects.filter(id=candidate_id).first()
    if not c:
        return Response({"detail": "Candidate not found."}, status=404)
    reason = request.data.get("reason", "")
    c.verification_status = "correction_required"
    c.save(update_fields=["verification_status"])
    notify(c.user, "correction_required", "Correction required", reason)
    return Response({"detail": "Correction requested."})


@api_view(["POST"])
@permission_classes([IsAdminStaff])
def admin_candidate_change_status(request, candidate_id):
    c = CandidateProfile.objects.filter(id=candidate_id).first()
    if not c:
        return Response({"detail": "Candidate not found."}, status=404)
    new_status = request.data.get("status")
    valid = dict(CandidateProfile.STATUS)
    if new_status not in valid:
        return Response({"detail": "Invalid status."}, status=400)
    _set_status(c, new_status, request.user, request.data.get("reason", ""))
    notify(c.user, "status_update", "Status updated",
           f"Your application status is now: {valid[new_status]}.")
    return Response({"detail": "Status updated.", "current_status": new_status})


@api_view(["GET"])
@permission_classes([IsAdminStaff])
def admin_candidate_status_history(request, candidate_id):
    qs = CandidateStatusHistory.objects.filter(candidate_id=candidate_id)
    return Response(StatusHistorySerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAdminStaff])
def admin_document_verify(request, document_id):
    doc = CandidateDocument.objects.filter(id=document_id).first()
    if not doc:
        return Response({"detail": "Document not found."}, status=404)
    doc.verification_status = "verified"
    doc.verified_by = request.user
    doc.verified_at = timezone.now()
    doc.save(update_fields=["verification_status", "verified_by", "verified_at"])
    return Response({"detail": "Document verified."})


# ---------------- Employer management ----------------
class AdminEmployerList(ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = EmployerAdminSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["employer_code", "company_name_english"]

    def get_queryset(self):
        qs = EmployerProfile.objects.filter(deleted_at__isnull=True).order_by("-created_at")
        if self.request.query_params.get("approval_status"):
            qs = qs.filter(approval_status=self.request.query_params["approval_status"])
        return qs


@api_view(["POST"])
@permission_classes([IsAdminStaff])
def admin_employer_approve(request, employer_id):
    ep = EmployerProfile.objects.filter(id=employer_id).first()
    if not ep:
        return Response({"detail": "Employer not found."}, status=404)
    ep.approval_status = "approved"
    ep.approved_by = request.user
    ep.approved_at = timezone.now()
    ep.save(update_fields=["approval_status", "approved_by", "approved_at"])
    notify(ep.user, "employer_approved", "Company approved",
           "Your company has been approved. You can now search candidates and post jobs.")
    log_action(request.user, "admin.employer.approve", "EmployerProfile", ep.id)
    return Response({"detail": "Employer approved."})


@api_view(["POST"])
@permission_classes([IsAdminStaff])
def admin_employer_reject(request, employer_id):
    ep = EmployerProfile.objects.filter(id=employer_id).first()
    if not ep:
        return Response({"detail": "Employer not found."}, status=404)
    ep.approval_status = "rejected"
    ep.save(update_fields=["approval_status"])
    notify(ep.user, "employer_rejected", "Registration not approved",
           request.data.get("reason", "Your registration could not be approved."))
    return Response({"detail": "Employer rejected."})


@api_view(["POST"])
@permission_classes([IsAdminStaff])
def admin_employer_suspend(request, employer_id):
    ep = EmployerProfile.objects.filter(id=employer_id).first()
    if not ep:
        return Response({"detail": "Employer not found."}, status=404)
    ep.approval_status = "suspended"
    ep.suspended_at = timezone.now()
    ep.save(update_fields=["approval_status", "suspended_at"])
    return Response({"detail": "Employer suspended."})


@api_view(["PUT"])
@permission_classes([IsAdminStaff])
def admin_employer_permissions(request, employer_id):
    ep = EmployerProfile.objects.filter(id=employer_id).first()
    if not ep:
        return Response({"detail": "Employer not found."}, status=404)
    ep.can_view_photos = request.data.get("can_view_photos", ep.can_view_photos)
    ep.can_request_interviews = request.data.get("can_request_interviews", ep.can_request_interviews)
    ep.save(update_fields=["can_view_photos", "can_request_interviews"])
    return Response({"detail": "Permissions updated."})


# ---------------- Job approval ----------------
class AdminJobList(ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = JobEmployerSerializer

    def get_queryset(self):
        qs = Job.objects.filter(deleted_at__isnull=True).order_by("-created_at")
        if self.request.query_params.get("approval_status"):
            qs = qs.filter(approval_status=self.request.query_params["approval_status"])
        return qs


@api_view(["POST"])
@permission_classes([IsAdminStaff])
def admin_job_action(request, job_id, action):
    job = Job.objects.filter(id=job_id).first()
    if not job:
        return Response({"detail": "Job not found."}, status=404)
    transitions = {
        "approve": ("approved", "job_approved", "Your job posting has been approved."),
        "reject": ("rejected", "job_rejected", "Your job posting was not approved."),
        "request-correction": ("correction_required", "job_correction", "Your job posting needs corrections."),
        "publish": ("published", "job_published", "Your job posting is now live."),
        "unpublish": ("approved", None, None),
        "close": ("approved", None, None),
    }
    if action not in transitions:
        return Response({"detail": "Invalid action."}, status=400)
    new_status, ntype, msg = transitions[action]
    job.approval_status = new_status
    if action == "publish":
        job.published_at = timezone.now()
        job.approved_by = request.user
        job.approved_at = timezone.now()
    if action == "close":
        job.job_status = "closed"
    job.save()
    if ntype:
        notify(job.employer.user, ntype, "Job update", msg)
    log_action(request.user, f"admin.job.{action}", "Job", job.id)
    return Response({"detail": f"Job {action} complete.", "approval_status": job.approval_status})


# ---------------- Interview management ----------------
@api_view(["GET"])
@permission_classes([IsAdminStaff])
def admin_interview_requests(request):
    qs = InterviewRequest.objects.all().prefetch_related("candidates")
    if request.query_params.get("request_status"):
        qs = qs.filter(request_status=request.query_params["request_status"])
    return Response(InterviewRequestSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAdminStaff])
def admin_interview_request_action(request, request_id, action):
    req = InterviewRequest.objects.filter(id=request_id).first()
    if not req:
        return Response({"detail": "Request not found."}, status=404)
    req.request_status = "approved" if action == "approve" else "rejected"
    req.reviewed_by = request.user
    req.reviewed_at = timezone.now()
    req.save()
    notify(req.employer.user, f"interview_request_{action}d", "Interview request update",
           f"Your interview request {req.request_code} was {req.request_status}.")
    return Response({"detail": f"Interview request {req.request_status}."})


@api_view(["GET", "POST"])
@permission_classes([IsAdminStaff])
def admin_interviews(request):
    if request.method == "GET":
        qs = Interview.objects.all().prefetch_related("candidates")
        return Response(InterviewSerializer(qs, many=True).data)
    data = request.data
    interview = Interview.objects.create(
        interview_request_id=data.get("interview_request"),
        employer_id=data["employer"], job_id=data["job"],
        interview_date=data["interview_date"], start_time=data["start_time"],
        end_time=data.get("end_time"), interview_mode=data.get("interview_mode", "online"),
        meeting_platform=data.get("meeting_platform", ""), meeting_url=data.get("meeting_url", ""),
        venue=data.get("venue", ""), interpreter_name=data.get("interpreter_name", ""),
        created_by=request.user)
    for cid in data.get("candidate_ids", []):
        InterviewCandidate.objects.create(interview=interview, candidate_id=cid)
        c = CandidateProfile.objects.filter(id=cid).first()
        if c:
            _set_status(c, "interview_scheduled", request.user, "Interview scheduled")
            notify(c.user, "interview_scheduled", "Interview scheduled",
                   f"An interview has been scheduled for {interview.interview_date}.")
    log_action(request.user, "admin.interview.create", "Interview", interview.id)
    return Response(InterviewSerializer(interview).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAdminStaff])
def admin_interview_results(request, interview_id):
    interview = Interview.objects.filter(id=interview_id).first()
    if not interview:
        return Response({"detail": "Interview not found."}, status=404)
    interview.interview_status = "completed"
    interview.save(update_fields=["interview_status"])
    for row in request.data.get("results", []):
        ic = InterviewCandidate.objects.filter(
            interview=interview, candidate_id=row["candidate_id"]).first()
        if not ic:
            continue
        ic.admin_result = row.get("result", ic.admin_result)
        ic.final_status = row.get("result", ic.final_status)
        ic.attendance_status = row.get("attendance", ic.attendance_status)
        ic.save()
        if ic.final_status == "selected":
            _set_status(ic.candidate, "selected", request.user, "Selected at interview")
            notify(ic.candidate.user, "selection_result", "Congratulations — you were selected",
                   "You have been selected. Our team will contact you about next steps.")
    return Response({"detail": "Interview results recorded."})


# ---------------- Dashboard ----------------
@api_view(["GET"])
@permission_classes([IsAdminStaff])
def admin_dashboard(request):
    today = timezone.now().date()
    cands = CandidateProfile.objects.filter(deleted_at__isnull=True)
    stats = {
        "new_candidates_today": cands.filter(created_at__date=today).count(),
        "total_candidates": cands.count(),
        "pending_verification": cands.filter(verification_status="pending").count(),
        "verified_candidates": cands.filter(verification_status="verified").count(),
        "incomplete_profiles": cands.filter(profile_completion_percentage__lt=60).count(),
        "total_employers": EmployerProfile.objects.count(),
        "approved_employers": EmployerProfile.objects.filter(approval_status="approved").count(),
        "pending_employers": EmployerProfile.objects.filter(approval_status="pending").count(),
        "active_jobs": Job.objects.filter(approval_status="published", job_status="open").count(),
        "pending_jobs": Job.objects.filter(approval_status="pending").count(),
        "upcoming_interviews": Interview.objects.filter(
            interview_status="scheduled", interview_date__gte=today).count(),
        "selected_candidates": cands.filter(current_status="selected").count(),
        "visa_processing": cands.filter(current_status="visa_processing").count(),
        "deployed": cands.filter(current_status="deployed").count(),
    }
    by_level = list(
        CandidateProfile.objects.filter(language_qualifications__result_status="passed")
        .values("language_qualifications__level")
        .annotate(count=Count("id")).order_by())
    by_status = list(cands.values("current_status").annotate(count=Count("id")).order_by())
    return Response({"summary": stats, "candidates_by_japanese_level": by_level,
                     "candidates_by_status": by_status})
