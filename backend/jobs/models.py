from django.db import models
from django.conf import settings
from django.utils import timezone

from employers.models import EmployerProfile
from candidates.models import CandidateProfile
from reference.models import (ProgramType, VisaCategory, JobSector, Industry,
                              Prefecture, EducationLevel, QualificationType)


def gen_code(prefix, pk):
    return f"{prefix}{timezone.now():%Y}{pk:05d}"


class Job(models.Model):
    JOB_STATUS = [("open", "Open"), ("closed", "Closed"), ("filled", "Filled"),
                  ("expired", "Expired")]
    APPROVAL = [("draft", "Draft"), ("pending", "Pending Approval"),
                ("correction_required", "Correction Required"),
                ("approved", "Approved"), ("rejected", "Rejected"),
                ("published", "Published")]
    SALARY_TYPE = [("monthly", "Monthly"), ("hourly", "Hourly"), ("annual", "Annual")]
    GENDER = [("any", "Any"), ("male", "Male"), ("female", "Female")]

    job_code = models.CharField(max_length=30, unique=True, blank=True)
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=200)
    internal_reference = models.CharField(max_length=100, blank=True)
    program_type = models.ForeignKey(ProgramType, on_delete=models.SET_NULL, null=True, blank=True)
    visa_category = models.ForeignKey(VisaCategory, on_delete=models.SET_NULL, null=True, blank=True)
    job_sector = models.ForeignKey(JobSector, on_delete=models.SET_NULL, null=True, blank=True)
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    number_of_positions = models.PositiveIntegerField(default=1)
    work_prefecture = models.ForeignKey(Prefecture, on_delete=models.SET_NULL, null=True, blank=True)
    work_city = models.CharField(max_length=100, blank=True)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=5, default="JPY")
    salary_type = models.CharField(max_length=10, choices=SALARY_TYPE, default="monthly")
    working_hours = models.CharField(max_length=100, blank=True)
    overtime_details = models.CharField(max_length=200, blank=True)
    weekly_holidays = models.CharField(max_length=100, blank=True)
    annual_leave_details = models.CharField(max_length=200, blank=True)
    accommodation_available = models.BooleanField(default=False)
    accommodation_cost = models.CharField(max_length=100, blank=True)
    food_support = models.CharField(max_length=100, blank=True)
    transportation_support = models.CharField(max_length=100, blank=True)
    insurance_details = models.CharField(max_length=200, blank=True)
    contract_duration = models.CharField(max_length=100, blank=True)
    expected_joining_date = models.DateField(null=True, blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    job_status = models.CharField(max_length=15, choices=JOB_STATUS, default="open")
    approval_status = models.CharField(max_length=25, choices=APPROVAL, default="draft", db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["approval_status", "job_status"])]

    def __str__(self):
        return f"{self.job_code} - {self.title}"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating and not self.job_code:
            self.job_code = gen_code("JC-J-", self.pk)
            super().save(update_fields=["job_code"])


class JobRequirement(models.Model):
    GENDER = [("any", "Any"), ("male", "Male"), ("female", "Female")]
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name="requirement")
    minimum_age = models.PositiveIntegerField(null=True, blank=True)
    maximum_age = models.PositiveIntegerField(null=True, blank=True)
    gender_preference = models.CharField(max_length=10, choices=GENDER, default="any")
    education_level = models.ForeignKey(EducationLevel, on_delete=models.SET_NULL, null=True, blank=True)
    japanese_qualification_type = models.ForeignKey(QualificationType, on_delete=models.SET_NULL, null=True, blank=True)
    japanese_level = models.CharField(max_length=20, blank=True)
    skill_test_required = models.BooleanField(default=False)
    skill_sector = models.ForeignKey(JobSector, on_delete=models.SET_NULL, null=True, blank=True, related_name="skill_requirements")
    minimum_experience_months = models.PositiveIntegerField(default=0)
    driving_licence_required = models.BooleanField(default=False)
    additional_skills = models.TextField(blank=True)
    additional_requirements = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class JobApplication(models.Model):
    STATUS = [("submitted", "Submitted"), ("under_review", "Under Review"),
              ("shortlisted", "Shortlisted"), ("interview", "Interview"),
              ("selected", "Selected"), ("rejected", "Rejected"),
              ("withdrawn", "Withdrawn")]
    SOURCE = [("candidate", "Candidate"), ("admin", "Admin")]

    application_code = models.CharField(max_length=30, unique=True, blank=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="applications")
    application_source = models.CharField(max_length=15, choices=SOURCE, default="candidate")
    applied_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    application_status = models.CharField(max_length=15, choices=STATUS, default="submitted")
    admin_notes = models.TextField(blank=True)
    candidate_notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("job", "candidate")
        ordering = ["-applied_at"]

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating and not self.application_code:
            self.application_code = gen_code("JC-A-", self.pk)
            super().save(update_fields=["application_code"])


class EmployerShortlist(models.Model):
    STATUS = [("active", "Active"), ("interview_requested", "Interview Requested"),
              ("removed", "Removed")]
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name="shortlists")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="shortlists")
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="shortlisted_in")
    shortlisted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    employer_note = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)
    shortlist_status = models.CharField(max_length=25, choices=STATUS, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("employer", "job", "candidate")
        ordering = ["-created_at"]
