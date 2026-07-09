from django.urls import path
from . import views

urlpatterns = [
    path("homepage", views.public_homepage),
    path("statistics", views.public_statistics),
    path("programs", views.public_programs),
    path("job-sectors", views.public_job_sectors),
    path("japan-regions", views.public_japan_regions),
    path("reference", views.public_reference),
    path("contact", views.public_contact),
    path("pages/<slug:slug>", views.public_page),
]
