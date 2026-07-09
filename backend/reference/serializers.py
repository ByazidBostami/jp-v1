from rest_framework import serializers
from . import models


class SimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProgramType
        fields = ["id", "name", "code"]


def simple(model_cls, extra=None):
    fields = ["id", "name", "code"] + (extra or [])
    meta = type("Meta", (), {"model": model_cls, "fields": fields})
    return type(f"{model_cls.__name__}Serializer", (serializers.ModelSerializer,), {"Meta": meta})


ProgramTypeSerializer = simple(models.ProgramType, ["description", "display_order"])
JobSectorSerializer = simple(models.JobSector, ["description", "display_order"])
IndustrySerializer = simple(models.Industry)
EducationLevelSerializer = simple(models.EducationLevel)
QualificationTypeSerializer = simple(models.QualificationType)
VisaCategorySerializer = simple(models.VisaCategory)
DocumentTypeSerializer = simple(models.DocumentType, ["is_required"])


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.District
        fields = ["id", "name", "division"]


class DivisionSerializer(serializers.ModelSerializer):
    districts = DistrictSerializer(many=True, read_only=True)

    class Meta:
        model = models.Division
        fields = ["id", "name", "districts"]


class PrefectureSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Prefecture
        fields = ["id", "name", "region"]


class JapanRegionSerializer(serializers.ModelSerializer):
    prefectures = PrefectureSerializer(many=True, read_only=True)

    class Meta:
        model = models.JapanRegion
        fields = ["id", "name", "prefectures"]
