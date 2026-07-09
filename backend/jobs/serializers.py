from rest_framework import serializers
from . import models as m


class JobRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.JobRequirement
        exclude = ["job", "created_at", "updated_at"]


class JobPublicSerializer(serializers.ModelSerializer):
    program_type_name = serializers.CharField(source="program_type.name", read_only=True)
    job_sector_name = serializers.CharField(source="job_sector.name", read_only=True)
    prefecture_name = serializers.CharField(source="work_prefecture.name", read_only=True)
    requirement = JobRequirementSerializer(read_only=True)

    class Meta:
        model = m.Job
        fields = ["id", "job_code", "title", "program_type", "program_type_name",
                  "job_sector", "job_sector_name", "work_prefecture", "prefecture_name",
                  "work_city", "description", "number_of_positions", "salary_min",
                  "salary_max", "salary_currency", "salary_type", "working_hours",
                  "accommodation_available", "food_support", "transportation_support",
                  "expected_joining_date", "application_deadline", "job_status",
                  "requirement", "published_at"]


class JobEmployerSerializer(serializers.ModelSerializer):
    requirement = JobRequirementSerializer(required=False)

    class Meta:
        model = m.Job
        exclude = ["employer", "approved_by", "approved_at", "deleted_at"]
        read_only_fields = ["job_code", "approval_status", "published_at"]

    def create(self, validated_data):
        req = validated_data.pop("requirement", None)
        job = m.Job.objects.create(**validated_data)
        if req:
            m.JobRequirement.objects.create(job=job, **req)
        else:
            m.JobRequirement.objects.create(job=job)
        return job

    def update(self, instance, validated_data):
        req = validated_data.pop("requirement", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if req is not None:
            m.JobRequirement.objects.update_or_create(job=instance, defaults=req)
        return instance


class JobApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    job_code = serializers.CharField(source="job.job_code", read_only=True)
    candidate_code = serializers.CharField(source="candidate.candidate_code", read_only=True)

    class Meta:
        model = m.JobApplication
        fields = ["id", "application_code", "job", "job_title", "job_code",
                  "candidate_code", "application_status", "candidate_notes",
                  "applied_at", "reviewed_at"]
        read_only_fields = ["application_code", "application_status", "reviewed_at"]


class ShortlistSerializer(serializers.ModelSerializer):
    candidate_code = serializers.CharField(source="candidate.candidate_code", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)

    class Meta:
        model = m.EmployerShortlist
        fields = ["id", "job", "job_title", "candidate", "candidate_code",
                  "employer_note", "shortlist_status", "created_at"]
        read_only_fields = ["shortlist_status"]
