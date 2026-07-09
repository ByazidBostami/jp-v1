# JapanCareer.jp

A securely managed recruitment and education platform that connects **Japan‑ready candidates from Bangladesh** with **Japanese employers and education providers**. The platform is admin‑mediated by design: employers can discover and shortlist verified talent, but candidate contact details and private documents are never exposed to them — all contact, interviews, and placement are coordinated by the JapanCareer.jp team.

Built with **Django 4.2 + Django REST Framework** (backend) and **React 18 + Vite** (frontend).

> Developed by **SoftyIT** ([softyit.com](https://softyit.com)).

---

## Table of contents
1. What's implemented
2. Architecture
3. Quick start (local development)
4. Demo accounts
5. Configuration & environment variables
6. Production notes (MySQL, static, security)
7. Privacy model
8. Testing
9. Project scope & honest status

---

## 1. What's implemented

**Backend (`/backend`)** — 8 Django apps, 47 domain models, JWT auth, a uniform response envelope, role‑based permissions, and a full audit log.

- **Authentication & accounts** — custom email‑based `User`, roles (`super_admin`, `admin`, `verifier`, `interviewer`, `employer`, `candidate`), JWT access/refresh tokens with rotation and blacklisting, per‑action audit logging.
- **Reference data** — programs (TITP/SSW/ESD/JLS/Bachelor/Master), job sectors, education levels, qualification types, visa categories, industries, document types, and full Bangladesh (division→district) and Japan (region→prefecture) geography.
- **Candidates** — profile with the full status lifecycle (`new → incomplete → pending_verification → verified → shortlisted → interview_scheduled → interview_completed → selected → visa_processing → coe_processing → departure_ready → deployed`, plus `inactive`/`rejected`), education, language qualifications, skill tests, work experience, addresses, documents, program/sector preferences, profile‑completion scoring, and job applications.
- **Employers** — company profile with admin approval workflow, **privacy‑enforced candidate search**, shortlists, job postings, and interview requests.
- **Jobs** — posting → admin approval → publish lifecycle, requirements, and a public listing/detail API.
- **Interviews** — employer interview requests, admin approval and scheduling, candidate confirmation, and result recording that advances candidate status.
- **Admin portal** — dashboard summary, candidate verification (approve / reject / request correction / change status), employer approval, job approval/publishing, interview‑request management, document verification, and CSV/XLSX candidate reports.
- **Content** — homepage statistics (recomputed live), CMS pages, contact messages, and system settings.

**Frontend (`/frontend`)** — a React SPA with:

- Public site: home (live stats, programs, sectors, featured jobs), searchable job listing, job detail with application, about, contact.
- Auth: login and a combined candidate/employer registration.
- Three role dashboards: **candidate** (completion, applications, interviews, notifications, job search), **employer** (approval status, privacy‑safe talent search, job posting, shortlist, interviews), and **admin** (KPIs, candidate/employer/job/interview management, CSV export).

---

## 2. Architecture

```
japancareer/
├── backend/                 Django 4.2 + DRF API
│   ├── config/              settings, root urls, wsgi/asgi
│   ├── accounts/            users, roles, JWT, audit log, renderer, pagination
│   ├── reference/           lookup tables + `seed` management command
│   ├── candidates/          candidate profile & sub‑resources
│   ├── employers/           employer profile, candidate search, shortlists
│   ├── jobs/                job postings + public job API
│   ├── interviews/          interview requests & scheduling
│   ├── content/             homepage stats, CMS pages, contact, settings
│   ├── adminportal/         admin/verifier/interviewer endpoints + reports
│   ├── smoke_test.py        in‑process end‑to‑end test (34 checks)
│   └── requirements.txt
└── frontend/                React 18 + Vite SPA
    └── src/
        ├── api.js           envelope‑aware fetch client with JWT refresh
        ├── context/         auth provider
        ├── components/      nav, footer, layout, badges, guards
        └── pages/           public pages + 3 role dashboards
```

- **API base path:** `/api/v1`
- **Response envelope:** every response is `{ "success", "message", "data", "meta" }`. List endpoints put pagination in `meta`: `{ current_page, per_page, total, last_page }`.
- **Auth:** `Authorization: Bearer <access>`; refresh via `POST /api/v1/auth/refresh-token`.

---

## 3. Quick start (local development)

### Prerequisites
- Python 3.11+ (developed on 3.12)
- Node.js 18+ (developed on 22)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed              # reference data + demo accounts + demo job
python manage.py runserver         # http://127.0.0.1:8000
```

The API is now at `http://127.0.0.1:8000/api/v1/`. Health check: `GET /api/v1/health`.

### Frontend

```bash
cd frontend
npm install
npm run dev                        # http://127.0.0.1:5173
```

The dev server proxies `/api` to `http://127.0.0.1:8000`, so run the backend alongside it. For a production bundle: `npm run build` (outputs to `frontend/dist`).

---

## 4. Demo accounts

Created by `python manage.py seed`:

| Role      | Email                      | Password        |
|-----------|----------------------------|-----------------|
| Admin     | admin@japancareer.jp       | `Admin@12345`   |
| Candidate | candidate@example.com      | `Candidate@123` |
| Employer  | employer@example.com       | `Employer@123`  |

The seed also creates a verified demo candidate, an approved demo employer, and one published demo job so the homepage, job listing, and dashboards have data immediately.

---

## 5. Configuration & environment variables

Backend settings read from environment variables (a `.env` file in `backend/` is supported via `python-dotenv`). Common ones:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | dev key | Django secret — **set in production** |
| `DEBUG` | `True` | Set `False` in production |
| `ALLOWED_HOSTS` | `*` (dev) | Comma‑separated hostnames |
| `DB_ENGINE` | `sqlite` | Set `mysql` to use MySQL |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | — | MySQL connection |
| `CORS_ALLOWED_ORIGINS` | dev origins | Frontend origin(s) |
| `FIELD_ENCRYPTION_KEY` | — | Key for encrypting sensitive fields |

The frontend reads `VITE_API_BASE` (defaults to `/api/v1`) if you need to point it at a non‑proxied API.

---

## 6. Production notes

**Database (MySQL 8).** The settings support MySQL out of the box:

```bash
export DB_ENGINE=mysql
export DB_NAME=japancareer
export DB_USER=japancareer
export DB_PASSWORD=... DB_HOST=127.0.0.1 DB_PORT=3306
pip install mysqlclient
python manage.py migrate
```

**Field encryption.** Installing `cryptography` (included in `requirements.txt`) enables real Fernet encryption for sensitive fields; without it the code falls back to a lightweight keyed transform for development. Set `FIELD_ENCRYPTION_KEY` in production.

**Serving.** Run Django under Gunicorn/uWSGI behind Nginx; serve the built `frontend/dist` as static files and reverse‑proxy `/api` to the app server. Terminate TLS at Nginx, run `python manage.py collectstatic`, set `DEBUG=False`, a strong `SECRET_KEY`, and a locked‑down `ALLOWED_HOSTS`/`CORS_ALLOWED_ORIGINS`. Schedule regular database backups.

---

## 7. Privacy model

This is a core requirement, enforced at the serializer layer:

- Employer‑facing candidate endpoints use dedicated serializers that expose only qualifications (age, gender, education, Japanese level, skills, general location, availability) and **never** name, email, mobile, national ID, passport number, full address, or private documents.
- Every employer and every job posting requires admin approval before becoming active/visible.
- Interviews are requested by employers but approved, scheduled, and coordinated by admins.
- All privileged actions are written to an audit log.

The privacy guarantees are covered by automated checks in `smoke_test.py` (e.g. "card hides email", "card hides passport", "employer detail excludes contact").

---

## 8. Testing

An in‑process end‑to‑end test exercises the real URL routing, views, serializers, permissions, and database:

```bash
cd backend
python smoke_test.py
```

It runs 34 checks across registration, verification, privacy enforcement, job posting/approval/publishing, applications, the full interview workflow, the admin dashboard, and CSV export.

The frontend is verified to build cleanly with `npm run build`.

---

## 9. Project scope & honest status

This repository is a **runnable, well‑architected core** of the JapanCareer.jp platform. It implements the primary end‑to‑end journeys described in the SRS — registration, admin verification, privacy‑enforced employer search, the job posting/approval lifecycle, applications, the interview workflow, dashboards for all three roles, seeded demo data, and passing end‑to‑end tests — and is structured to support the full 100k+ candidate scale.

It is a Phase‑1 foundation, not the entire multi‑month build. Areas that a production rollout would still flesh out include: document upload/preview with virus scanning, notification delivery (email/SMS), the later visa/COE/departure stages of the pipeline as first‑class UI, granular admin permission management screens, exhaustive validation and localization (Japanese UI), rate‑limit/observability hardening, and a broader automated test suite beyond the end‑to‑end smoke test. These are natural next steps on top of the architecture already in place.
