from django.db import models
from django.conf import settings
from django.utils import timezone

from accounts.encryption import encrypt, decrypt
from reference.models import (
    Country, Division, District, JapanRegion, Prefecture, ProgramType,
    JobSector, Industry, EducationLevel, QualificationType, DocumentType)


def gen_code(prefix, pk):
    return f"{prefix}{timezone.now():%Y}{pk:06d}"


class CandidateProfile(models.Model):
    GENDER = [("male", "Male"), ("female", "Female"), ("other", "Other")]

    VERIFICATION = [
        ("new", "New"), ("pending", "Pending Verification"),
        ("verified", "Verified"), ("correction_required", "Correction Required"),
        ("rejected", "Rejected"),
    ]
    # SRS Candidate Status lifecycle
    STATUS = [
        ("new", "New"), ("incomplete", "Incomplete"),
        ("pending_verification", "Pending Verification"), ("verified", "Verified"),
        ("shortlisted", "Shortlisted"), ("interview_scheduled", "Interview Scheduled"),
        ("interview_completed", "Interview Completed"), ("selected", "Selected"),
        ("visa_processing", "Visa Processing"), ("coe_processing", "COE Processing"),
        ("departure_ready", "Departure Ready"), ("deployed", "Deployed"),
        ("inactive", "Inactive"), ("rejected", "Rejected"),
    ]
    AVAILABILITY = [("available", "Available"), ("engaged", "Engaged"),
                    ("unavailable", "Unavailable")]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="candidate_profile")
    candidate_code = models.CharField(max_length=30, unique=True, blank=True)
    full_name = models.CharField(max_length=150)
    passport_name = models.CharField(max_length=150, blank=True)
    father_name = models.CharField(max_length=150, blank=True)
    mother_name = models.CharField(max_length=150, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER, blank=True)
    nationality = models.CharField(max_length=100, default="Bangladeshi", blank=True)
    marital_status = models.CharField(max_length=20, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    # Sensitive identifiers — stored encrypted (SRS *_encrypted fields)
    national_id_encrypted = models.CharField(max_length=255, blank=True)
    passport_number_encrypted = models.CharField(max_length=255, blank=True)
    passport_issue_date = models.DateField(null=True, blank=True)
    passport_expiry_date = models.DateField(null=True, blank=True)
    passport_issuing_authority = models.CharField(max_length=150, blank=True)
    profile_photo = models.ImageField(upload_to="candidate_photos/", null=True, blank=True)

    profile_completion_percentage = models.PositiveIntegerField(default=0)
    verification_status = models.CharField(max_length=30, choices=VERIFICATION, default="new")
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY, default="available")
    current_status = models.CharField(max_length=30, choices=STATUS, default="new", db_index=True)
    assigned_admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name="assigned_candidates")
    submitted_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # M2M-ish preference relations
    program_preferences = models.ManyToManyField(
        ProgramType, through="CandidateProgramPreference", related_name="candidates")
    job_preferences = models.ManyToManyField(
        JobSector, through="CandidateJobPreference", related_name="candidates")

    class Meta:
        indexes = [
            models.Index(fields=["verification_status"]),
            models.Index(fields=["availability_status"]),
        ]

    def __str__(self):
        return f"{self.candidate_code} - {self.full_name}"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating and not self.candidate_code:
            self.candidate_code = gen_code("JC-C-", self.pk)
            super().save(update_fields=["candidate_code"])

    # Encrypted accessors
    @property
    def passport_number(self):
        return decrypt(self.passport_number_encrypted)

    @passport_number.setter
    def passport_number(self, value):
        self.passport_number_encrypted = encrypt(value or "")

    @property
    def national_id(self):
        return decrypt(self.national_id_encrypted)

    @national_id.setter
    def national_id(self, value):
        self.national_id_encrypted = encrypt(value or "")

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    @property
    def highest_japanese_level(self):
        q = self.language_qualifications.filter(result_status="passed").order_by("level").first()
        return q.level if q else None

    def recompute_completion(self):
        checks = [
            bool(self.full_name), bool(self.date_of_birth), bool(self.gender),
            bool(self.passport_number_encrypted), self.addresses.exists(),
            self.education_records.exists(), self.language_qualifications.exists(),
            self.documents.exists(), self.program_preference_links.exists(),
            self.job_preference_links.exists(),
        ]
        self.profile_completion_percentage = round(100 * sum(checks) / len(checks))
        self.save(update_fields=["profile_completion_percentage"])
        return self.profile_completion_percentage


class CandidateAddress(models.Model):
    TYPE = [("present", "Present"), ("permanent", "Permanent")]
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="addresses")
    address_type = models.CharField(max_length=10, choices=TYPE)
    house_village = models.CharField(max_length=150, blank=True)
    road = models.CharField(max_length=150, blank=True)
    area = models.CharField(max_length=150, blank=True)
    post_office = models.CharField(max_length=100, blank=True)
    police_station_upazila = models.CharField(max_length=100, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)
    postal_code = models.CharField(max_length=15, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    is_current = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class EducationRecord(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="education_records")
    education_level = models.ForeignKey(EducationLevel, on_delete=models.SET_NULL, null=True, blank=True)
    degree_name = models.CharField(max_length=150)
    subject = models.CharField(max_length=150, blank=True)
    institution_name = models.CharField(max_length=200)
    board_university = models.CharField(max_length=200, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    start_year = models.PositiveIntegerField(null=True, blank=True)
    passing_year = models.PositiveIntegerField(null=True, blank=True)
    result_type = models.CharField(max_length=30, blank=True)
    result_value = models.CharField(max_length=30, blank=True)
    verification_status = models.CharField(max_length=30, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LanguageQualification(models.Model):
    RESULT = [("passed", "Passed"), ("appeared", "Appeared"), ("studying", "Studying")]
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="language_qualifications")
    qualification_type = models.ForeignKey(QualificationType, on_delete=models.SET_NULL, null=True, blank=True)
    level = models.CharField(max_length=20, blank=True)  # N5..N1 / A2 etc.
    result_status = models.CharField(max_length=20, choices=RESULT, default="appeared")
    exam_date = models.DateField(null=True, blank=True)
    result_date = models.DateField(null=True, blank=True)
    score = models.CharField(max_length=20, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    institute_name = models.CharField(max_length=200, blank=True)
    verification_status = models.CharField(max_length=30, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SkillTest(models.Model):
    RESULT = [("passed", "Passed"), ("appeared", "Appeared")]
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="skill_tests")
    sector = models.ForeignKey(JobSector, on_delete=models.SET_NULL, null=True, blank=True)
    test_name = models.CharField(max_length=150)
    test_authority = models.CharField(max_length=150, blank=True)
    result_status = models.CharField(max_length=20, choices=RESULT, default="appeared")
    test_date = models.DateField(null=True, blank=True)
    score = models.CharField(max_length=20, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    verification_status = models.CharField(max_length=30, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class WorkExperience(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="work_experiences")
    company_name = models.CharField(max_length=200)
    designation = models.CharField(max_length=150)
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    responsibilities = models.TextField(blank=True)
    verification_status = models.CharField(max_length=30, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CandidateProgramPreference(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="program_preference_links")
    program_type = models.ForeignKey(ProgramType, on_delete=models.CASCADE)
    priority_order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("candidate", "program_type")


class CandidateJobPreference(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="job_preference_links")
    job_sector = models.ForeignKey(JobSector, on_delete=models.CASCADE)
    priority_order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("candidate", "job_sector")


class CandidateLocationPreference(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="location_preferences")
    japan_region = models.ForeignKey(JapanRegion, on_delete=models.CASCADE, null=True, blank=True)
    prefecture = models.ForeignKey(Prefecture, on_delete=models.SET_NULL, null=True, blank=True)
    priority_order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)


class CandidateDocument(models.Model):
    VISIBILITY = [
        ("admin_only", "Admin Only"),
        ("candidate_and_admin", "Candidate and Admin"),
        ("employer_summary_only", "Employer Summary Only"),
        ("employer_viewable", "Employer Viewable"),
        ("downloadable_by_admin_only", "Downloadable by Admin Only"),
    ]
    VERIFICATION = [("pending", "Pending"), ("verified", "Verified"),
                    ("rejected", "Rejected"), ("correction_required", "Correction Required")]

    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="documents")
    document_type = models.ForeignKey(DocumentType, on_delete=models.SET_NULL, null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to="candidate_documents/")
    mime_type = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    checksum = models.CharField(max_length=64, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    verification_status = models.CharField(max_length=30, choices=VERIFICATION, default="pending")
    verification_notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name="verified_documents")
    verified_at = models.DateTimeField(null=True, blank=True)
    visibility_level = models.CharField(max_length=40, choices=VISIBILITY, default="admin_only")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)


class CandidateStatusHistory(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="status_history")
    previous_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30)
    reason = models.TextField(blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]
