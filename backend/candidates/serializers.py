from rest_framework import serializers
from . import models as m


# ---- Sub-resource serializers -------------------------------------------
class CandidateAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.CandidateAddress
        exclude = ["candidate"]


class EducationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.EducationRecord
        exclude = ["candidate"]
        read_only_fields = ["verification_status"]


class LanguageQualificationSerializer(serializers.ModelSerializer):
    qualification_type_name = serializers.CharField(source="qualification_type.name", read_only=True)

    class Meta:
        model = m.LanguageQualification
        exclude = ["candidate"]
        read_only_fields = ["verification_status"]


class SkillTestSerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source="sector.name", read_only=True)

    class Meta:
        model = m.SkillTest
        exclude = ["candidate"]
        read_only_fields = ["verification_status"]


class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.WorkExperience
        exclude = ["candidate"]
        read_only_fields = ["verification_status"]


class CandidateDocumentSerializer(serializers.ModelSerializer):
    document_type_name = serializers.CharField(source="document_type.name", read_only=True)

    class Meta:
        model = m.CandidateDocument
        fields = ["id", "document_type", "document_type_name", "original_filename",
                  "file", "mime_type", "file_size", "verification_status",
                  "verification_notes", "visibility_level", "uploaded_at"]
        read_only_fields = ["mime_type", "file_size", "verification_status",
                            "verification_notes", "original_filename"]


class StatusHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.CharField(source="changed_by.email", read_only=True)

    class Meta:
        model = m.CandidateStatusHistory
        fields = ["previous_status", "new_status", "reason", "changed_by_email", "changed_at"]


# ---- Candidate self / admin (full) profile ------------------------------
class CandidateProfileSerializer(serializers.ModelSerializer):
    """Full profile — for the candidate themselves and admin staff only."""
    passport_number = serializers.CharField(required=False, allow_blank=True)
    national_id = serializers.CharField(required=False, allow_blank=True)
    age = serializers.IntegerField(read_only=True)
    addresses = CandidateAddressSerializer(many=True, read_only=True)
    education_records = EducationRecordSerializer(many=True, read_only=True)
    language_qualifications = LanguageQualificationSerializer(many=True, read_only=True)
    skill_tests = SkillTestSerializer(many=True, read_only=True)
    work_experiences = WorkExperienceSerializer(many=True, read_only=True)
    documents = CandidateDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = m.CandidateProfile
        fields = [
            "id", "candidate_code", "full_name", "passport_name", "father_name",
            "mother_name", "date_of_birth", "age", "gender", "nationality",
            "marital_status", "blood_group", "national_id", "passport_number",
            "passport_issue_date", "passport_expiry_date", "passport_issuing_authority",
            "profile_photo", "profile_completion_percentage", "verification_status",
            "availability_status", "current_status", "submitted_at", "verified_at",
            "addresses", "education_records", "language_qualifications",
            "skill_tests", "work_experiences", "documents",
        ]
        read_only_fields = ["candidate_code", "profile_completion_percentage",
                            "verification_status", "current_status", "submitted_at",
                            "verified_at"]

    def update(self, instance, validated_data):
        passport = validated_data.pop("passport_number", None)
        nid = validated_data.pop("national_id", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if passport is not None:
            instance.passport_number = passport
        if nid is not None:
            instance.national_id = nid
        instance.save()
        return instance


# ---- Employer-visible summary (PRIVACY ENFORCED, SRS §17) ---------------
class CandidateEmployerCardSerializer(serializers.ModelSerializer):
    """Card view for employer search — NO contact/identity fields.
    See SRS §17: employer APIs must never return mobile, email, address,
    NID, passport, private documents or admin notes."""
    age = serializers.IntegerField(read_only=True)
    highest_japanese_level = serializers.SerializerMethodField()
    highest_education = serializers.SerializerMethodField()
    skill_test_status = serializers.SerializerMethodField()
    experience_summary = serializers.SerializerMethodField()
    preferred_programs = serializers.SerializerMethodField()
    preferred_sectors = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    verified = serializers.SerializerMethodField()

    class Meta:
        model = m.CandidateProfile
        fields = ["id", "candidate_code", "age", "gender", "highest_education",
                  "highest_japanese_level", "skill_test_status", "experience_summary",
                  "preferred_programs", "preferred_sectors", "availability_status",
                  "photo", "verified"]

    def get_highest_japanese_level(self, obj):
        return obj.highest_japanese_level

    def get_highest_education(self, obj):
        rec = obj.education_records.order_by("-passing_year").first()
        return rec.degree_name if rec else None

    def get_skill_test_status(self, obj):
        return "passed" if obj.skill_tests.filter(result_status="passed").exists() else "none"

    def get_experience_summary(self, obj):
        total = obj.work_experiences.count()
        return f"{total} record(s)" if total else "No experience"

    def get_preferred_programs(self, obj):
        return list(obj.program_preferences.values_list("code", flat=True))

    def get_preferred_sectors(self, obj):
        return list(obj.job_preferences.values_list("code", flat=True))

    def get_verified(self, obj):
        return obj.verification_status == "verified"

    def get_photo(self, obj):
        ep = self.context.get("employer")
        if ep and not ep.can_view_photos:
            return None
        return obj.profile_photo.url if obj.profile_photo else None


class CandidateEmployerDetailSerializer(CandidateEmployerCardSerializer):
    """Fuller employer-visible profile — still strips all sensitive data."""
    education = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()
    general_location = serializers.SerializerMethodField()

    class Meta(CandidateEmployerCardSerializer.Meta):
        fields = CandidateEmployerCardSerializer.Meta.fields + [
            "education", "languages", "skills", "experience", "general_location"]

    def get_education(self, obj):
        return EducationRecordSerializer(obj.education_records.all(), many=True).data

    def get_languages(self, obj):
        return LanguageQualificationSerializer(obj.language_qualifications.all(), many=True).data

    def get_skills(self, obj):
        return SkillTestSerializer(obj.skill_tests.all(), many=True).data

    def get_experience(self, obj):
        return WorkExperienceSerializer(obj.work_experiences.all(), many=True).data

    def get_general_location(self, obj):
        addr = obj.addresses.filter(address_type="present").first()
        # Only division/district level — never the exact street address.
        if addr and addr.district:
            return addr.district.name
        return None
