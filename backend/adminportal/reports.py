import csv
import io
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import IsAdminStaff
from candidates.models import CandidateProfile

try:
    from openpyxl import Workbook
    HAS_XLSX = True
except Exception:
    HAS_XLSX = False


CANDIDATE_COLUMNS = [
    ("candidate_code", "Candidate Code"), ("full_name", "Full Name"),
    ("gender", "Gender"), ("nationality", "Nationality"),
    ("verification_status", "Verification"), ("current_status", "Status"),
    ("availability_status", "Availability"),
    ("profile_completion_percentage", "Completion %"),
]


def _candidate_rows(qs):
    rows = []
    for c in qs:
        rows.append([getattr(c, key) for key, _ in CANDIDATE_COLUMNS])
    return rows


@api_view(["GET"])
@permission_classes([IsAdminStaff])
def candidate_report(request):
    """Filterable candidate report; ?format=excel|csv|json (default json)."""
    qs = CandidateProfile.objects.filter(deleted_at__isnull=True)
    p = request.query_params
    for field in ["verification_status", "current_status", "availability_status"]:
        if p.get(field):
            qs = qs.filter(**{field: p[field]})

    fmt = p.get("output", "json")
    headers = [label for _, label in CANDIDATE_COLUMNS]
    rows = _candidate_rows(qs)

    if fmt == "csv":
        buff = io.StringIO()
        writer = csv.writer(buff)
        writer.writerow(headers)
        writer.writerows(rows)
        resp = HttpResponse(buff.getvalue(), content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="candidate_report.csv"'
        return resp

    if fmt == "excel" and HAS_XLSX:
        wb = Workbook()
        ws = wb.active
        ws.title = "Candidates"
        ws.append(headers)
        for row in rows:
            ws.append(row)
        buff = io.BytesIO()
        wb.save(buff)
        resp = HttpResponse(
            buff.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        resp["Content-Disposition"] = 'attachment; filename="candidate_report.xlsx"'
        return resp

    return Response({"headers": headers,
                     "rows": [dict(zip([k for k, _ in CANDIDATE_COLUMNS], r)) for r in rows],
                     "total": len(rows)})
