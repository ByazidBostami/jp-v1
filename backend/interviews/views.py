from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import IsApprovedEmployer, IsCandidate, IsAdminStaff
from accounts.services import log_action
from candidates.views import get_profile
from content.models import notify
from . import models as m
from . import serializers as s


# ---------- Employer ----------
@api_view(["GET", "POST"])
@permission_classes([IsApprovedEmployer])
def employer_interview_requests(request):
    ep = request.user.employer_profile
    if request.method == "GET":
        qs = m.InterviewRequest.objects.filter(employer=ep).prefetch_related("candidates")
        return Response(s.InterviewRequestSerializer(qs, many=True).data)

    if not ep.can_request_interviews:
        return Response({"detail": "Interview requests are disabled for this account."},
                        status=status.HTTP_403_FORBIDDEN)
    ser = s.InterviewRequestSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    candidate_ids = ser.validated_data.pop("candidate_ids", [])
    req = m.InterviewRequest.objects.create(
        employer=ep, requested_by=request.user, **ser.validated_data)
    for cid in candidate_ids:
        m.InterviewRequestCandidate.objects.create(interview_request=req, candidate_id=cid)
    log_action(request.user, "employer.interview.request", "InterviewRequest", req.id)
    return Response(s.InterviewRequestSerializer(req).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsApprovedEmployer])
def employer_interviews(request):
    qs = m.Interview.objects.filter(employer=request.user.employer_profile)
    return Response(s.InterviewSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsApprovedEmployer])
def employer_feedback(request, interview_id):
    interview = m.Interview.objects.filter(
        id=interview_id, employer=request.user.employer_profile).first()
    if not interview:
        return Response({"detail": "Interview not found."}, status=404)
    ic = m.InterviewCandidate.objects.filter(
        interview=interview, candidate_id=request.data.get("candidate_id")).first()
    if not ic:
        return Response({"detail": "Candidate not part of this interview."}, status=404)
    ic.employer_result = request.data.get("result", ic.employer_result)
    ic.employer_feedback = request.data.get("comments", ic.employer_feedback)
    ic.score = request.data.get("score", ic.score)
    ic.save()
    log_action(request.user, "employer.interview.feedback", "InterviewCandidate", ic.id)
    return Response({"detail": "Feedback recorded."})


# ---------- Candidate ----------
@api_view(["GET"])
@permission_classes([IsCandidate])
def candidate_interviews(request):
    profile = get_profile(request.user)
    qs = m.InterviewCandidate.objects.filter(candidate=profile).select_related("interview__job")
    return Response(s.CandidateInterviewSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsCandidate])
def confirm_interview(request, interview_id):
    profile = get_profile(request.user)
    ic = m.InterviewCandidate.objects.filter(
        interview_id=interview_id, candidate=profile).first()
    if not ic:
        return Response({"detail": "Interview not found."}, status=404)
    ic.attendance_status = "confirmed"
    ic.save(update_fields=["attendance_status"])
    return Response({"detail": "Attendance confirmed."})
