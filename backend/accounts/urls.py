from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path("candidate/register", views.candidate_register),
    path("employer/register", views.employer_register),
    path("login", views.login),
    path("logout", views.logout),
    path("refresh-token", TokenRefreshView.as_view()),
    path("me", views.me),
    path("verify-email", views.verify_email),
    path("forgot-password", views.forgot_password),
    path("reset-password", views.reset_password),
    path("send-mobile-otp", views.send_mobile_otp),
    path("verify-mobile-otp", views.verify_mobile_otp),
]
