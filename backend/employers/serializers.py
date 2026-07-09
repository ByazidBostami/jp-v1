from rest_framework import serializers
from . import models as m


class EmployerProfileSerializer(serializers.ModelSerializer):
    industry_name = serializers.CharField(source="industry.name", read_only=True)

    class Meta:
        model = m.EmployerProfile
        fields = ["id", "employer_code", "company_name_english", "company_name_japanese",
                  "registration_number", "company_type", "industry", "industry_name",
                  "established_year", "employee_count", "website", "representative_name",
                  "contact_person_name", "contact_designation", "telephone",
                  "company_email", "company_profile", "approval_status",
                  "can_view_photos", "can_request_interviews", "created_at"]
        read_only_fields = ["employer_code", "approval_status", "can_view_photos",
                            "can_request_interviews"]


class EmployerAdminSerializer(EmployerProfileSerializer):
    """Admin view exposes approval controls."""
    class Meta(EmployerProfileSerializer.Meta):
        read_only_fields = ["employer_code"]


class EmployerDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.EmployerDocument
        fields = ["id", "document_type", "original_filename", "file", "mime_type",
                  "file_size", "verification_status", "verification_notes", "created_at"]
        read_only_fields = ["mime_type", "file_size", "verification_status",
                            "original_filename"]
