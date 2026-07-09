from django.urls import path
from rest_framework.routers import SimpleRouter
from . import views
from jobs import views as job_views
from interviews import views as iv_views
from content import views as content_views

router = SimpleRouter(trailing_slash=False)
router.register("addresses", views.AddressViewSet, basename="addr")
router.register("education", views.EducationViewSet, basename="edu")
router.register("language-qualifications", views.LanguageViewSet, basename="lang")
router.register("skill-tests", views.SkillTestViewSet, basename="skill")
router.register("work-experiences", views.WorkExperienceViewSet, basename="work")
router.register("documents", views.DocumentViewSet, basename="doc")

urlpatterns = [
    path("profile", views.profile),
    path("profile/completion", views.completion),
    path("profile/submit", views.submit_profile),
    # Jobs & applications
    path("jobs", job_views.candidate_jobs),
    path("jobs/<int:job_id>/apply", job_views.apply_job),
    path("applications", job_views.candidate_applications),
    path("applications/<int:application_id>/withdraw", job_views.withdraw_application),
    # Interviews
    path("interviews", iv_views.candidate_interviews),
    path("interviews/<int:interview_id>/confirm", iv_views.confirm_interview),
    # Notifications
    path("notifications", content_views.my_notifications),
    path("notifications/read-all", content_views.mark_all_read),
    path("notifications/<int:notification_id>/read", content_views.mark_read),
] + router.urls
