from django.db import models
from django.conf import settings
from django.utils import timezone
from reference.models import Country, Prefecture, Industry, DocumentType


def gen_code(prefix, pk):
    return f"{prefix}{timezone.now():%Y}{pk:05d}"


class EmployerProfile(models.Model):
    APPROVAL = [
        ("pending", "Pending Review"),
        ("info_required", "Additional Information Required"),
        ("approved", "Approved"), ("rejected", "Rejected"),
        ("suspended", "Suspended"),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="employer_profile")
    employer_code = models.CharField(max_length=30, unique=True, blank=True)
    company_name_english = models.CharField(max_length=200)
    company_name_japanese = models.CharField(max_length=200, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    company_type = models.CharField(max_length=100, blank=True)
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True)
    established_year = models.PositiveIntegerField(null=True, blank=True)
    employee_count = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    representative_name = models.CharField(max_length=150)
    contact_person_name = models.CharField(max_length=150)
    contact_designation = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    company_email = models.EmailField(blank=True)
    company_profile = models.TextField(blank=True)
    approval_status = models.CharField(max_length=20, choices=APPROVAL, default="pending", db_index=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name="approved_employers")
    approved_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    # Permission flags an admin can toggle (Screen 26)
    can_view_photos = models.BooleanField(default=True)
    can_request_interviews = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employer_code} - {self.company_name_english}"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating and not self.employer_code:
            self.employer_code = gen_code("JC-E-", self.pk)
            super().save(update_fields=["employer_code"])


class EmployerAddress(models.Model):
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name="addresses")
    address_type = models.CharField(max_length=20, default="head_office")
    postal_code = models.CharField(max_length=15, blank=True)
    prefecture = models.ForeignKey(Prefecture, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address_line_1 = models.CharField(max_length=200, blank=True)
    address_line_2 = models.CharField(max_length=200, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class EmployerDocument(models.Model):
    VERIFICATION = [("pending", "Pending"), ("verified", "Verified"), ("rejected", "Rejected")]
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name="documents")
    document_type = models.ForeignKey(DocumentType, on_delete=models.SET_NULL, null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to="employer_documents/")
    mime_type = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION, default="pending")
    verification_notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
