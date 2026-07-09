from django.contrib import admin
from .models import Job, JobApplication

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("job_code", "title", "approval_status", "job_status")
    list_filter = ("approval_status", "job_status")

admin.site.register(JobApplication)
