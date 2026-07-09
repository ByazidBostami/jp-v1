"""End-to-end API smoke test + demo data generator."""
import os, django, json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test import Client
c = Client()

def call(method, path, token=None, **kw):
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
    fn = getattr(c, method)
    if kw.get("data") is not None and method in ("post", "put"):
        resp = fn(path, data=json.dumps(kw["data"]), content_type="application/json", **headers)
    else:
        resp = fn(path, **headers)
    try:
        body = resp.json()
    except Exception:
        body = {"_raw": resp.content[:200].decode(errors="ignore")}
    return resp.status_code, body

ok = 0; fail = 0
def check(label, cond):
    global ok, fail
    if cond: ok += 1; print(f"  PASS  {label}")
    else: fail += 1; print(f"  FAIL  {label}")

print("\n== Public ==")
s, b = call("get", "/api/v1/health"); check("health", s == 200)
s, b = call("get", "/api/v1/public/homepage")
check("homepage stats", s == 200 and "statistics" in b["data"])
s, b = call("get", "/api/v1/public/reference")
check("reference dropdowns", s == 200 and len(b["data"]["job_sectors"]) > 10)

print("\n== Candidate registration & profile ==")
import random
suffix = random.randint(1000, 9999)
s, b = call("post", "/api/v1/auth/candidate/register", data={
    "full_name": "Rahim Uddin", "email": f"rahim{suffix}@example.com",
    "mobile": "01712345678", "password": "Passw0rd!", "confirm_password": "Passw0rd!",
    "consent_privacy": True, "consent_terms": True})
check("candidate register", s == 201)
ctoken = b["data"]["tokens"]["access"]
cand_code = b["data"]["candidate_code"]
print(f"     candidate_code={cand_code}")

s, b = call("put", "/api/v1/candidate/profile", token=ctoken, data={
    "date_of_birth": "1998-05-10", "gender": "male", "passport_number": "BX1234567",
    "national_id": "1990123456789", "passport_name": "RAHIM UDDIN"})
check("update profile (encrypted fields)", s == 200 and b["data"]["passport_number"] == "BX1234567")

s, b = call("post", "/api/v1/candidate/education", token=ctoken, data={
    "degree_name": "HSC", "institution_name": "Dhaka College", "passing_year": 2016})
check("add education", s == 201)
s, b = call("post", "/api/v1/candidate/language-qualifications", token=ctoken, data={
    "level": "N4", "result_status": "passed", "score": "120"})
check("add JLPT N4", s == 201)
s, b = call("post", "/api/v1/candidate/addresses", token=ctoken, data={
    "address_type": "present", "area": "Mirpur", "postal_code": "1216"})
check("add address", s == 201)
s, b = call("get", "/api/v1/candidate/profile/completion", token=ctoken)
print(f"     completion={b['data']['profile_completion_percentage']}%")
s, b = call("post", "/api/v1/candidate/profile/submit", token=ctoken)
check("submit profile", s == 200)

print("\n== Admin verifies candidate ==")
s, b = call("post", "/api/v1/auth/login", data={
    "email": "admin@japancareer.jp", "password": "Admin@12345"})
check("admin login", s == 200)
atoken = b["data"]["tokens"]["access"]
s, b = call("get", "/api/v1/admin/candidates?verification_status=pending", token=atoken)
pend = [x for x in b["data"] if x["candidate_code"] == cand_code]
check("candidate appears in pending", len(pend) == 1)
cid = pend[0]["id"]
s, b = call("post", f"/api/v1/admin/candidates/{cid}/approve", token=atoken)
check("admin approve candidate", s == 200 and b["data"]["verification_status"] == "verified")

print("\n== Employer registration & approval ==")
s, b = call("post", "/api/v1/auth/employer/register", data={
    "company_name_english": "Sakura Manufacturing KK", "representative_name": "Taro Yamada",
    "contact_person_name": "Hanako Sato", "email": f"hr{suffix}@sakura.jp",
    "telephone": "0312345678", "password": "Passw0rd!", "confirm_password": "Passw0rd!",
    "consent_rules": True})
check("employer register", s == 201)
etoken = b["data"]["tokens"]["access"]
emp_code = b["data"]["employer_code"]

# employer not yet approved -> search should be forbidden
s, b = call("get", "/api/v1/employer/candidates", token=etoken)
check("unapproved employer blocked from search", s == 403)

s, b = call("get", "/api/v1/admin/employers?approval_status=pending", token=atoken)
eid = [x for x in b["data"] if x["employer_code"] == emp_code][0]["id"]
s, b = call("post", f"/api/v1/admin/employers/{eid}/approve", token=atoken)
check("admin approve employer", s == 200)

print("\n== PRIVACY: employer candidate search ==")
s, b = call("get", "/api/v1/employer/candidates", token=etoken)
check("approved employer can search", s == 200)
card = b["data"][0] if b["data"] else {}
check("card has candidate_code", "candidate_code" in card)
check("card hides email", "email" not in card and "mobile" not in card)
check("card hides passport", "passport_number" not in card and "national_id" not in card)
# detail view
s, b = call("get", f"/api/v1/employer/candidates/{cid}", token=etoken)
check("employer detail excludes contact", s == 200 and "email" not in b["data"]
      and "passport_number" not in b["data"])

print("\n== Job posting, approval, application ==")
sectors = call("get", "/api/v1/public/job-sectors")[1]["data"]
s, b = call("post", "/api/v1/employer/jobs", token=etoken, data={
    "title": "Food Manufacturing Worker", "description": "Assembly line work in Aichi.",
    "number_of_positions": 5, "job_sector": sectors[5]["id"], "salary_min": 180000,
    "salary_max": 220000, "requirement": {"minimum_age": 18, "maximum_age": 35,
    "japanese_level": "N4"}})
check("employer create job", s == 201)
jid = b["data"]["id"]
s, b = call("post", f"/api/v1/employer/jobs/{jid}/submit", token=etoken)
check("submit job for approval", s == 200)
s, b = call("post", f"/api/v1/admin/jobs/{jid}/approve", token=atoken)
check("admin approve job", s == 200)
s, b = call("post", f"/api/v1/admin/jobs/{jid}/publish", token=atoken)
check("admin publish job", s == 200)
s, b = call("get", "/api/v1/public/jobs")
check("job visible on public listing", s == 200 and b["meta"]["total"] >= 1)
s, b = call("post", f"/api/v1/candidate/jobs/{jid}/apply", token=ctoken)
check("verified candidate applies", s == 201)

print("\n== Interview workflow ==")
s, b = call("post", "/api/v1/employer/shortlists", token=etoken, data={
    "job": jid, "candidate": cid, "employer_note": "Strong N4"})
check("employer shortlist candidate", s == 201)
s, b = call("post", "/api/v1/employer/interview-requests", token=etoken, data={
    "job": jid, "preferred_dates": "2026-08-01", "interview_mode": "online",
    "candidate_ids": [cid]})
check("employer request interview", s == 201)
reqid = b["data"]["id"]
s, b = call("post", f"/api/v1/admin/interview-requests/{reqid}/approve", token=atoken)
check("admin approve interview request", s == 200)
s, b = call("post", "/api/v1/admin/interviews", token=atoken, data={
    "interview_request": reqid, "employer": eid, "job": jid,
    "interview_date": "2026-08-05", "start_time": "10:00",
    "interview_mode": "online", "meeting_platform": "zoom",
    "meeting_url": "https://zoom.us/j/123", "candidate_ids": [cid]})
check("admin schedule interview", s == 201)
ivid = b["data"]["id"]
s, b = call("get", "/api/v1/candidate/interviews", token=ctoken)
check("candidate sees interview", s == 200 and len(b["data"]) >= 1)
s, b = call("post", f"/api/v1/admin/interviews/{ivid}/results", token=atoken, data={
    "results": [{"candidate_id": cid, "result": "selected", "attendance": "present"}]})
check("admin record results -> selected", s == 200)

print("\n== Reports & dashboard ==")
s, b = call("get", "/api/v1/admin/dashboard/summary", token=atoken)
check("admin dashboard", s == 200 and "summary" in b["data"])
s, b = call("get", "/api/v1/admin/reports/candidates?output=csv", token=atoken)
check("candidate CSV export", s == 200)

print(f"\n=========== {ok} passed, {fail} failed ===========")
