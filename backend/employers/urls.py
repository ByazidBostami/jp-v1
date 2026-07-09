from django.urls import path
from rest_framework.routers import SimpleRouter
from . import views
from jobs import views as job_views
from interviews import views as iv_views

router = SimpleRouter(trailing_slash=False)
router.register("documents", views.EmployerDocumentViewSet, basename="empdoc")
router.register("jobs", job_views.EmployerJobViewSet, basename="empjob")
router.register("shortlists", job_views.ShortlistViewSet, basename="shortlist")

urlpatterns = [
    path("profile", views.profile),
    path("approval-status", views.approval_status),
    path("candidates", views.EmployerCandidateSearch.as_view()),
    path("candidates/<int:pk>", views.EmployerCandidateDetail.as_view()),
    path("jobs/<int:job_id>/submit", job_views.submit_job),
    path("interview-requests", iv_views.employer_interview_requests),
    path("interviews", iv_views.employer_interviews),
    path("interviews/<int:interview_id>/feedback", iv_views.employer_feedback),
] + router.urls
