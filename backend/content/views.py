from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from . import models as m
from . import serializers as s
from .services import recompute_homepage_statistics
from reference import models as ref
from reference import serializers as refs


class ContactThrottle(ScopedRateThrottle):
    scope = "contact"


# ---------------- Public ----------------
@api_view(["GET"])
@permission_classes([AllowAny])
def public_homepage(request):
    recompute_homepage_statistics()
    stats = m.HomepageStatistic.objects.filter(is_visible=True)
    return Response({
        "statistics": s.HomepageStatisticSerializer(stats, many=True).data,
        "programs": refs.ProgramTypeSerializer(
            ref.ProgramType.objects.filter(is_active=True), many=True).data,
        "job_sectors": refs.JobSectorSerializer(
            ref.JobSector.objects.filter(is_active=True), many=True).data,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def public_statistics(request):
    recompute_homepage_statistics()
    stats = m.HomepageStatistic.objects.filter(is_visible=True)
    return Response(s.HomepageStatisticSerializer(stats, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_programs(request):
    return Response(refs.ProgramTypeSerializer(
        ref.ProgramType.objects.filter(is_active=True), many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_job_sectors(request):
    return Response(refs.JobSectorSerializer(
        ref.JobSector.objects.filter(is_active=True), many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_japan_regions(request):
    return Response(refs.JapanRegionSerializer(
        ref.JapanRegion.objects.prefetch_related("prefectures").all(), many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_reference(request):
    """One call for all dropdowns the registration forms need."""
    return Response({
        "programs": refs.ProgramTypeSerializer(ref.ProgramType.objects.filter(is_active=True), many=True).data,
        "job_sectors": refs.JobSectorSerializer(ref.JobSector.objects.filter(is_active=True), many=True).data,
        "education_levels": refs.EducationLevelSerializer(ref.EducationLevel.objects.all(), many=True).data,
        "qualification_types": refs.QualificationTypeSerializer(ref.QualificationType.objects.all(), many=True).data,
        "industries": refs.IndustrySerializer(ref.Industry.objects.all(), many=True).data,
        "visa_categories": refs.VisaCategorySerializer(ref.VisaCategory.objects.all(), many=True).data,
        "document_types": refs.DocumentTypeSerializer(ref.DocumentType.objects.filter(is_active=True), many=True).data,
        "divisions": refs.DivisionSerializer(ref.Division.objects.prefetch_related("districts"), many=True).data,
        "japan_regions": refs.JapanRegionSerializer(ref.JapanRegion.objects.prefetch_related("prefectures"), many=True).data,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ContactThrottle])
def public_contact(request):
    ser = s.ContactMessageSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    ser.save()
    return Response({"detail": "Your message has been received. We will respond shortly."},
                    status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_page(request, slug):
    page = m.ContentPage.objects.filter(slug=slug, status="published").first()
    if not page:
        return Response({"detail": "Page not found."}, status=404)
    return Response(s.ContentPageSerializer(page).data)


# ---------------- Notifications (any authenticated user) ----------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_notifications(request):
    qs = m.Notification.objects.filter(user=request.user)[:50]
    unread = m.Notification.objects.filter(user=request.user, read_at__isnull=True).count()
    return Response({"unread": unread,
                     "items": s.NotificationSerializer(qs, many=True).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_read(request, notification_id):
    m.Notification.objects.filter(id=notification_id, user=request.user).update(
        read_at=timezone.now())
    return Response({"detail": "Marked as read."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    m.Notification.objects.filter(user=request.user, read_at__isnull=True).update(
        read_at=timezone.now())
    return Response({"detail": "All notifications marked as read."})
