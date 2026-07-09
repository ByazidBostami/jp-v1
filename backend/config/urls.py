from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.http import JsonResponse
from jobs.views import PublicJobViewSet


def health(_request):
    return JsonResponse({"status": "ok", "service": "JapanCareer.jp API", "version": "v1"})


urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/v1/health", health),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/candidate/", include("candidates.urls")),
    path("api/v1/employer/", include("employers.urls")),
    path("api/v1/admin/", include("adminportal.urls")),
    path("api/v1/public/", include("content.urls")),
    path("api/v1/public/jobs", PublicJobViewSet.as_view({"get": "list"})),
    path("api/v1/public/jobs/<int:pk>", PublicJobViewSet.as_view({"get": "retrieve"})),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
