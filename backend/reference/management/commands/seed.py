"""Seeds roles, permissions, reference data and demo accounts.
Run: python manage.py seed
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from accounts.models import Role, User
from reference import models as ref
from content.models import HomepageStatistic, ContentPage, SystemSetting

ROLES = [
    ("super_admin", "Super Administrator"), ("admin", "Administrator"),
    ("verifier", "Verifier"), ("interviewer", "Interviewer"),
    ("employer", "Employer"), ("candidate", "Candidate"),
]
PROGRAMS = [("TITP", "TITP"), ("ESD", "ESD"), ("SSW", "SSW"),
            ("Japanese Language School", "JLS"), ("Bachelor's Program", "BACHELOR"),
            ("Master's Program", "MASTER")]
SECTORS = ["Caregiving", "Agriculture", "Construction", "Automobile Repair and Maintenance",
           "Food Service", "Food Manufacturing", "Building Cleaning",
           "Accommodation and Hospitality", "Industrial Manufacturing", "Driving",
           "Aviation", "Railway", "Forestry", "Fisheries", "Nursing", "Engineering",
           "Information Technology"]
EDU_LEVELS = ["Below SSC", "SSC", "HSC", "Diploma", "Bachelor", "Master"]
QUALIFICATIONS = [("JLPT", "JLPT"), ("JFT-Basic", "JFT"), ("NAT-Test", "NAT"), ("JLCT", "JLCT")]
VISAS = [("SSW (i)", "SSW1"), ("SSW (ii)", "SSW2"), ("TITP", "TITP"),
         ("Student", "STUDENT"), ("Engineer/Specialist", "ENGINEER")]
INDUSTRIES = ["Manufacturing", "Healthcare", "Construction", "Agriculture",
              "Hospitality", "IT", "Logistics", "Food"]
DOC_TYPES = [("Passport", "PASSPORT", True), ("National ID", "NID", True),
             ("Photograph", "PHOTO", True), ("CV", "CV", True),
             ("Educational Certificate", "EDU_CERT", False),
             ("Academic Transcript", "TRANSCRIPT", False),
             ("Japanese Certificate", "JP_CERT", False),
             ("Skill Certificate", "SKILL_CERT", False),
             ("Police Clearance", "POLICE", False), ("Medical Certificate", "MEDICAL", False)]
JAPAN_REGIONS = {
    "Hokkaido": ["Hokkaido"],
    "Tohoku": ["Aomori", "Iwate", "Miyagi", "Akita", "Yamagata", "Fukushima"],
    "Kanto": ["Tokyo", "Kanagawa", "Saitama", "Chiba", "Ibaraki", "Tochigi", "Gunma"],
    "Chubu": ["Aichi", "Shizuoka", "Nagano", "Niigata", "Gifu"],
    "Kansai": ["Osaka", "Kyoto", "Hyogo", "Nara", "Shiga", "Wakayama"],
    "Chugoku": ["Hiroshima", "Okayama", "Yamaguchi", "Shimane", "Tottori"],
    "Shikoku": ["Ehime", "Kagawa", "Tokushima", "Kochi"],
    "Kyushu": ["Fukuoka", "Kumamoto", "Nagasaki", "Kagoshima", "Oita", "Miyazaki", "Saga"],
    "Okinawa": ["Okinawa"],
}
BD_DIVISIONS = {
    "Dhaka": ["Dhaka", "Gazipur", "Narayanganj", "Tangail", "Munshiganj"],
    "Chattogram": ["Chattogram", "Cox's Bazar", "Cumilla", "Feni"],
    "Rajshahi": ["Rajshahi", "Bogura", "Pabna", "Natore"],
    "Khulna": ["Khulna", "Jessore", "Satkhira"],
    "Sylhet": ["Sylhet", "Moulvibazar", "Habiganj"],
    "Barishal": ["Barishal", "Bhola", "Patuakhali"],
    "Rangpur": ["Rangpur", "Dinajpur", "Kurigram"],
    "Mymensingh": ["Mymensingh", "Jamalpur", "Netrokona"],
}


class Command(BaseCommand):
    help = "Seed reference data and demo accounts"

    @transaction.atomic
    def handle(self, *args, **opts):
        for code, name in ROLES:
            Role.objects.get_or_create(code=code, defaults={"name": name})
        self.stdout.write("Roles seeded")

        for i, (name, code) in enumerate(PROGRAMS):
            ref.ProgramType.objects.get_or_create(code=code, defaults={"name": name, "display_order": i})
        for i, name in enumerate(SECTORS):
            code = name.upper().replace(" ", "_")[:40]
            ref.JobSector.objects.get_or_create(code=code, defaults={"name": name, "display_order": i})
        for i, name in enumerate(EDU_LEVELS):
            ref.EducationLevel.objects.get_or_create(code=name.upper().replace(" ", "_"),
                                                     defaults={"name": name, "display_order": i})
        for name, code in QUALIFICATIONS:
            ref.QualificationType.objects.get_or_create(code=code, defaults={"name": name})
        for name, code in VISAS:
            ref.VisaCategory.objects.get_or_create(code=code, defaults={"name": name})
        for name in INDUSTRIES:
            ref.Industry.objects.get_or_create(code=name.upper(), defaults={"name": name})
        for name, code, req in DOC_TYPES:
            ref.DocumentType.objects.get_or_create(
                code=code, defaults={"name": name, "is_required": req})
        self.stdout.write("Reference lists seeded")

        bd, _ = ref.Country.objects.get_or_create(iso_code="BGD", defaults={"name": "Bangladesh"})
        ref.Country.objects.get_or_create(iso_code="JPN", defaults={"name": "Japan"})
        for dname, districts in BD_DIVISIONS.items():
            div, _ = ref.Division.objects.get_or_create(name=dname, country=bd)
            for dist in districts:
                ref.District.objects.get_or_create(name=dist, division=div)
        for i, (rname, prefs) in enumerate(JAPAN_REGIONS.items()):
            region, _ = ref.JapanRegion.objects.get_or_create(name=rname, defaults={"display_order": i})
            for p in prefs:
                ref.Prefecture.objects.get_or_create(name=p, region=region)
        self.stdout.write("Geography seeded")

        # Content + settings
        for key, val in [("site_name", "JapanCareer.jp"),
                         ("developer_credit", "Developed by SoftyIT (softyit.com)"),
                         ("contact_email", "info@japancareer.jp")]:
            SystemSetting.objects.get_or_create(
                setting_key=key, defaults={"setting_group": "general", "setting_value": val,
                                           "is_public": True})
        ContentPage.objects.get_or_create(
            slug="about", language_code="en",
            defaults={"title": "About JapanCareer.jp", "page_type": "about",
                      "status": "published", "published_at": timezone.now(),
                      "content": "JapanCareer.jp connects Japan-ready candidates from "
                                 "Bangladesh with Japanese employers and education providers "
                                 "through a securely managed, privacy-first platform."})

        # Demo accounts
        admin_role = Role.objects.get(code="super_admin")
        if not User.objects.filter(email="admin@japancareer.jp").exists():
            User.objects.create_superuser(
                email="admin@japancareer.jp", password="Admin@12345",
                role=admin_role, mobile="0000000000")
            self.stdout.write("Demo admin: admin@japancareer.jp / Admin@12345")

        # Demo candidate (verified) + employer (approved) + published job
        self._demo_records()

        HomepageStatistic.objects.all().delete()
        from content.services import recompute_homepage_statistics
        recompute_homepage_statistics()
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def _demo_records(self):
        from candidates.models import (CandidateProfile, CandidateAddress, EducationRecord,
                                        LanguageQualification, SkillTest,
                                        CandidateProgramPreference, CandidateJobPreference)
        from employers.models import EmployerProfile
        from jobs.models import Job, JobRequirement

        cand_role = Role.objects.get(code="candidate")
        emp_role = Role.objects.get(code="employer")

        if not User.objects.filter(email="candidate@example.com").exists():
            u = User.objects.create_user(email="candidate@example.com", password="Candidate@123",
                                         mobile="+8801700000000", role=cand_role,
                                         account_status=User.ACTIVE)
            c = CandidateProfile.objects.create(
                user=u, full_name="Rahim Uddin", passport_name="RAHIM UDDIN",
                date_of_birth="1999-05-10", gender="male", nationality="Bangladeshi",
                passport_issuing_authority="DIP Dhaka",
                verification_status="verified", current_status="verified",
                verified_at=timezone.now())
            c.passport_number = "A01234567"
            c.national_id = "1990123456789"
            c.save()
            dist = ref.District.objects.filter(name="Dhaka").first()
            CandidateAddress.objects.create(
                candidate=c, address_type="present", area="Kafrul", district=dist,
                division=dist.division if dist else None,
                country=ref.Country.objects.filter(iso_code="BGD").first(), postal_code="1206")
            EducationRecord.objects.create(
                candidate=c, degree_name="HSC", institution_name="Dhaka College",
                passing_year=2018, result_type="GPA", result_value="4.50",
                verification_status="verified")
            LanguageQualification.objects.create(
                candidate=c, qualification_type=ref.QualificationType.objects.get(code="JLPT"),
                level="N4", result_status="passed", score="120", verification_status="verified")
            care = ref.JobSector.objects.filter(name="Caregiving").first()
            SkillTest.objects.create(candidate=c, sector=care, test_name="SSW Skills (Care)",
                                     result_status="passed", verification_status="verified")
            CandidateProgramPreference.objects.create(
                candidate=c, program_type=ref.ProgramType.objects.get(code="SSW"))
            if care:
                CandidateJobPreference.objects.create(candidate=c, job_sector=care)
            c.recompute_completion()
            self.stdout.write("Demo candidate: candidate@example.com / Candidate@123")

        if not User.objects.filter(email="employer@example.com").exists():
            u = User.objects.create_user(email="employer@example.com", password="Employer@123",
                                         mobile="+81300000000", role=emp_role,
                                         account_status=User.ACTIVE)
            emp = EmployerProfile.objects.create(
                user=u, company_name_english="Sakura Care Co., Ltd.",
                company_name_japanese="さくらケア株式会社", representative_name="Taro Yamada",
                contact_person_name="Hanako Sato", telephone="+81300000000",
                company_email="employer@example.com", approval_status="approved",
                approved_at=timezone.now())
            job = Job.objects.create(
                employer=emp, title="Caregiver (SSW)",
                program_type=ref.ProgramType.objects.get(code="SSW"),
                job_sector=ref.JobSector.objects.filter(name="Caregiving").first(),
                work_prefecture=ref.Prefecture.objects.filter(name="Osaka").first(),
                work_city="Osaka", description="Caregiving role at a licensed facility in Osaka.",
                number_of_positions=5, salary_min=180000, salary_max=220000,
                salary_currency="JPY", salary_type="monthly", working_hours="8 hrs/day",
                accommodation_available=True, food_support="Subsidised",
                approval_status="published", job_status="open", published_at=timezone.now())
            JobRequirement.objects.create(
                job=job, minimum_age=20, maximum_age=35, japanese_level="N4",
                skill_test_required=True, gender_preference="any")
            self.stdout.write("Demo employer: employer@example.com / Employer@123")
