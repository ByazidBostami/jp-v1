from django.urls import path
from . import views, reports

urlpatterns = [
    # Candidate management
    path("candidates", views.AdminCandidateList.as_view()),
    path("candidates/export", reports.candidate_report),
    path("candidates/<int:candidate_id>", views.admin_candidate_detail),
    path("candidates/<int:candidate_id>/approve", views.admin_candidate_approve),
    path("candidates/<int:candidate_id>/reject", views.admin_candidate_reject),
    path("candidates/<int:candidate_id>/request-correction", views.admin_candidate_request_correction),
    path("candidates/<int:candidate_id>/change-status", views.admin_candidate_change_status),
    path("candidates/<int:candidate_id>/status-history", views.admin_candidate_status_history),
    path("documents/<int:document_id>/verify", views.admin_document_verify),
    # Employer management
    path("employers", views.AdminEmployerList.as_view()),
    path("employers/<int:employer_id>/approve", views.admin_employer_approve),
    path("employers/<int:employer_id>/reject", views.admin_employer_reject),
    path("employers/<int:employer_id>/suspend", views.admin_employer_suspend),
    path("employers/<int:employer_id>/permissions", views.admin_employer_permissions),
    # Job management
    path("jobs", views.AdminJobList.as_view()),
    path("jobs/<int:job_id>/<str:action>", views.admin_job_action),
    # Interview management
    path("interview-requests", views.admin_interview_requests),
    path("interview-requests/<int:request_id>/<str:action>", views.admin_interview_request_action),
    path("interviews", views.admin_interviews),
    path("interviews/<int:interview_id>/results", views.admin_interview_results),
    # Dashboard & reports
    path("dashboard/summary", views.admin_dashboard),
    path("reports/candidates", reports.candidate_report),
]
