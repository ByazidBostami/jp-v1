from django.contrib import admin
from .models import CandidateProfile

@admin.register(CandidateProfile)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("candidate_code", "full_name", "verification_status", "current_status")
    list_filter = ("verification_status", "current_status", "availability_status")
    search_fields = ("candidate_code", "full_name")
