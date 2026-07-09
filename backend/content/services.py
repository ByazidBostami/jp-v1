"""Recomputes cached homepage statistics from live database records."""
from django.utils import timezone
from .models import HomepageStatistic


def recompute_homepage_statistics():
    from candidates.models import CandidateProfile, LanguageQualification, SkillTest
    from employers.models import EmployerProfile
    from jobs.models import Job
    from interviews.models import InterviewCandidate

    verified = CandidateProfile.objects.filter(verification_status="verified")
    values = {
        "total_candidates": CandidateProfile.objects.count(),
        "verified_candidates": verified.count(),
        "jlpt_n5": LanguageQualification.objects.filter(level="N5", result_status="passed").count(),
        "jlpt_n4": LanguageQualification.objects.filter(level="N4", result_status="passed").count(),
        "jlpt_n3_plus": LanguageQualification.objects.filter(
            level__in=["N3", "N2", "N1"], result_status="passed").count(),
        "skill_test_passed": SkillTest.objects.filter(result_status="passed").values("candidate").distinct().count(),
        "registered_employers": EmployerProfile.objects.filter(approval_status="approved").count(),
        "active_jobs": Job.objects.filter(approval_status="published", job_status="open").count(),
        "successful_placements": InterviewCandidate.objects.filter(final_status="selected").count(),
    }
    labels = {
        "total_candidates": "Total Registered Candidates",
        "verified_candidates": "Verified Candidates",
        "jlpt_n5": "JLPT N5 Candidates",
        "jlpt_n4": "JLPT N4 Candidates",
        "jlpt_n3_plus": "JLPT N3 and Above",
        "skill_test_passed": "Skill Test Passed Candidates",
        "registered_employers": "Registered Employers",
        "active_jobs": "Active Job Openings",
        "successful_placements": "Successful Placements",
    }
    order = list(labels.keys())
    for code, val in values.items():
        HomepageStatistic.objects.update_or_create(
            statistic_code=code,
            defaults={"statistic_label": labels[code], "calculated_value": val,
                      "last_calculated_at": timezone.now(),
                      "display_order": order.index(code)})
    return values
