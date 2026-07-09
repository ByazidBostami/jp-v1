from django.db import models
from django.conf import settings
from django.utils import timezone

from employers.models import EmployerProfile
from candidates.models import CandidateProfile
from jobs.models import Job


def gen_code(prefix, pk):
    return f"{prefix}{timezone.now():%Y}{pk:05d}"


class InterviewRequest(models.Model):
    MODE = [("online", "Online"), ("offline", "Offline")]
    STATUS = [("pending", "Pending Admin Review"), ("approved", "Approved"),
              ("rejected", "Rejected"), ("scheduled", "Scheduled")]
    request_code = models.CharField(max_length=30, unique=True, blank=True)
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name="interview_requests")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="interview_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    preferred_dates = models.CharField(max_length=200, blank=True)
    preferred_time = models.CharField(max_length=100, blank=True)
    timezone_name = models.CharField(max_length=50, default="Asia/Tokyo")
    interview_mode = models.CharField(max_length=10, choices=MODE, default="online")
    interpreter_required = models.BooleanField(default=False)
    employer_notes = models.TextField(blank=True)
    request_status = models.CharField(max_length=15, choices=STATUS, default="pending", db_index=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name="reviewed_interview_requests")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating and not self.request_code:
            self.request_code = gen_code("JC-IR-", self.pk)
            super().save(update_fields=["request_code"])


class InterviewRequestCandidate(models.Model):
    interview_request = models.ForeignKey(InterviewRequest, on_delete=models.CASCADE, related_name="candidates")
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE)
    request_status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)


class Interview(models.Model):
    MODE = [("online", "Online"), ("offline", "Offline")]
    PLATFORM = [("google_meet", "Google Meet"), ("zoom", "Zoom"),
                ("teams", "Microsoft Teams"), ("physical", "Physical Office")]
    STATUS = [("scheduled", "Scheduled"), ("rescheduled", "Rescheduled"),
              ("completed", "Completed"), ("cancelled", "Cancelled")]

    interview_code = models.CharField(max_length=30, unique=True, blank=True)
    interview_request = models.ForeignKey(InterviewRequest, on_delete=models.SET_NULL, null=True, blank=True)
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name="interviews")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="interviews")
    interview_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    timezone_name = models.CharField(max_length=50, default="Asia/Tokyo")
    interview_mode = models.CharField(max_length=10, choices=MODE, default="online")
    meeting_platform = models.CharField(max_length=20, choices=PLATFORM, blank=True)
    meeting_url = models.URLField(blank=True)
    venue = models.CharField(max_length=250, blank=True)
    interpreter_name = models.CharField(max_length=150, blank=True)
    interview_status = models.CharField(max_length=15, choices=STATUS, default="scheduled", db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-interview_date", "-start_time"]

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating and not self.interview_code:
            self.interview_code = gen_code("JC-IV-", self.pk)
            super().save(update_fields=["interview_code"])


class InterviewCandidate(models.Model):
    ATTENDANCE = [("pending", "Pending"), ("present", "Present"),
                  ("absent", "Absent"), ("confirmed", "Confirmed")]
    RESULT = [("pending", "Pending"), ("selected", "Selected"),
              ("rejected", "Rejected"), ("hold", "On Hold")]
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name="candidates")
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="interviews")
    attendance_status = models.CharField(max_length=15, choices=ATTENDANCE, default="pending")
    employer_result = models.CharField(max_length=15, choices=RESULT, default="pending")
    admin_result = models.CharField(max_length=15, choices=RESULT, default="pending")
    candidate_result = models.CharField(max_length=15, choices=RESULT, default="pending")
    employer_feedback = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    score = models.CharField(max_length=20, blank=True)
    final_status = models.CharField(max_length=15, choices=RESULT, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("interview", "candidate")
