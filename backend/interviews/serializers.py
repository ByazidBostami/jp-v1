from rest_framework import serializers
from . import models as m


class InterviewRequestSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    candidate_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False)
    candidates_list = serializers.SerializerMethodField()

    class Meta:
        model = m.InterviewRequest
        fields = ["id", "request_code", "job", "job_title", "preferred_dates",
                  "preferred_time", "timezone_name", "interview_mode",
                  "interpreter_required", "employer_notes", "request_status",
                  "candidate_ids", "candidates_list", "created_at"]
        read_only_fields = ["request_code", "request_status"]

    def get_candidates_list(self, obj):
        return [c.candidate.candidate_code for c in obj.candidates.all()]


class InterviewCandidateSerializer(serializers.ModelSerializer):
    candidate_code = serializers.CharField(source="candidate.candidate_code", read_only=True)

    class Meta:
        model = m.InterviewCandidate
        fields = ["id", "candidate", "candidate_code", "attendance_status",
                  "employer_result", "admin_result", "final_status",
                  "employer_feedback", "score"]


class InterviewSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    employer_name = serializers.CharField(source="employer.company_name_english", read_only=True)
    candidates = InterviewCandidateSerializer(many=True, read_only=True)

    class Meta:
        model = m.Interview
        fields = ["id", "interview_code", "job", "job_title", "employer", "employer_name",
                  "interview_date", "start_time", "end_time", "timezone_name",
                  "interview_mode", "meeting_platform", "meeting_url", "venue",
                  "interpreter_name", "interview_status", "candidates", "created_at"]
        read_only_fields = ["interview_code"]


class CandidateInterviewSerializer(serializers.ModelSerializer):
    """Candidate view — employer identity shown only if admin permits."""
    job_title = serializers.CharField(source="interview.job.title", read_only=True)
    interview_date = serializers.DateField(source="interview.interview_date", read_only=True)
    start_time = serializers.TimeField(source="interview.start_time", read_only=True)
    interview_mode = serializers.CharField(source="interview.interview_mode", read_only=True)
    meeting_platform = serializers.CharField(source="interview.meeting_platform", read_only=True)
    meeting_url = serializers.CharField(source="interview.meeting_url", read_only=True)
    venue = serializers.CharField(source="interview.venue", read_only=True)
    status = serializers.CharField(source="interview.interview_status", read_only=True)
    interview_code = serializers.CharField(source="interview.interview_code", read_only=True)

    class Meta:
        model = m.InterviewCandidate
        fields = ["id", "interview_code", "job_title", "interview_date", "start_time",
                  "interview_mode", "meeting_platform", "meeting_url", "venue",
                  "attendance_status", "final_status", "status"]
