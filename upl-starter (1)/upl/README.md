# Ultra Project Library — upgrade starter (Django)

Your live site serves `/static/images/...`, `/material/80` and uses Cloudinary for images, which looks like a Python
(Flask/Django) app. This starter uses **Django + PostgreSQL**, so existing data can be imported with `inspectdb`.
Confirm the real stack with whoever hosts/built the site before you start (see Phase 1).

## What is in this starter
| Area | File |
|---|---|
| Secure settings (env-only secrets, HTTPS, cookies, CSP, lockout) | `upl/settings.py` |
| Roles, user | `apps/accounts/models.py` |
| Site settings (WhatsApp, social links), audit log | `apps/core/` |
| Documents/SourceCode/Material/Course + moderation states | `apps/catalog/models.py` |
| Upload validation (extension, magic bytes, size, double-ext, random names) | `apps/catalog/validators.py` |
| Protected download (entitlement-checked, logged, rate-limited) | `apps/catalog/views.py` |
| Paystack init + server-side verify + idempotent fulfilment | `apps/payments/services.py` |
| Webhook with HMAC-SHA512 check | `apps/payments/views.py` |
| Purchase emails to author + UPL (Celery) | `apps/payments/tasks.py` |
| One-on-one hosts, slots, double-booking guard | `apps/bookings/models.py` |
| NYSC/IT/Job placements + applications | `apps/placements/` |
| Subscription plans (admin-configurable) | `apps/subscriptions/models.py` |
| Homepage with WhatsApp service buttons | `templates/home.html`, `apps/core/utils.py` |

Added in round 2: register, email verification (signed, 3-day link), login/logout/password reset, verified-only upload,
document upload form with rights declaration, basic dashboard, base CSS (mobile-first).

NOT yet built (follow the phases): source-code/material/course/placement upload forms, full user dashboard, admin
analytics charts, reviews, favourites, notifications UI, search, SEO sitemaps, legal pages, booking checkout views,
subscription checkout, org accounts. Models for most are present or trivial to add in the same pattern.

## Run locally
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env     # fill in values; use Paystack TEST keys first
    python manage.py makemigrations accounts core catalog payments bookings placements subscriptions
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver
(Add the standard `manage.py` and `upl/wsgi.py` from `django-admin startproject` if missing. Run `celery -A upl worker`.)
In admin > Site settings add keys: `whatsapp_number` (234xxxxxxxxxx), `whatsapp_group_url`, `telegram_url`,
`instagram_url`, `facebook_url`, `linkedin_url`, `youtube_url`.

## The process (do it in this order)
**Phase 1 – Audit and backup (before touching anything).** Export the full database (mysqldump/pg_dump) and
download all Cloudinary/file assets. Record: language/framework, DB engine, tables (`general_request`, materials,
projects, users), how admin login works, where files are stored. Rotate the admin password now: the old default
credential must not remain in production.
**Phase 2 – Staging.** Create a staging subdomain (e.g. staging.ultraprojectlibrary.com) with a copy of the data.
Never develop against production.
**Phase 3 – Data migration.** `python manage.py inspectdb > legacy.py` against the old DB, write a one-off script
mapping old projects → `Document` (status approved, price 0 if they were FREE), old materials → `Material`,
old general_request → a `GeneralRequest` model (add `created_at` and show it in admin with date filters). Keep old
URLs working with redirects (`/material/80` → new slug) to protect SEO.
**Phase 4 – Security base.** Auth (email verification, reset), axes lockout, admin 2FA (django-otp TOTP), HTTPS.
**Phase 5 – Documents → payments → downloads.** Upload form with the declaration checkbox, admin approval, Paystack
test mode end to end: pay, webhook, entitlement, download. Test replaying the webhook and tampering with amounts.
**Phase 6 – Source code, materials, courses.** Same moderation pattern; GitHub link is revealed only after payment.
**Phase 7 – Placements and applications**, then **one-on-one booking** (hold slot 15 min, pay, confirm).
**Phase 8 – Subscriptions, dashboards, analytics, notifications, reviews.**
**Phase 9 – UI polish**, SEO (sitemap, robots, OG tags, JSON-LD), accessibility, performance.
**Phase 10 – Security testing** (below) and load testing. **Phase 11 – Go-live**: run on staging with live Paystack
keys and a ₦100 item, then switch DNS, enable backups, Sentry, uptime monitoring.

## Security checklist before launch
- `DJANGO_DEBUG=False`; secrets only in environment; `python manage.py check --deploy` is clean
- Paid files in private storage (outside web root or private S3/R2 bucket); no public `/uploads/` route
- Webhook rejects bad signature; replay does not create a second entitlement (unique constraints + idempotent code)
- Amount always read from DB; try tampering with price, order id, download token, slot id (IDOR tests)
- Upload tests: `.php`, `shell.php.pdf`, renamed `.exe`, oversized file, path traversal filename
- Rate limits on login, purchase, download; axes lockout works; admin needs 2FA
- Backups: nightly encrypted `pg_dump` + file store snapshot to off-server storage; test a restore
- Payout/bank details never in public templates or API responses (encrypt the column at rest)

## Hosting
Ubuntu VPS or a PaaS: Nginx → Gunicorn, PostgreSQL, Redis, Celery worker, Let's Encrypt HTTPS, Cloudflare in front.
Use a Nigerian gateway (Paystack shown; Flutterwave is similar) and a transactional email provider (e.g. Brevo, Postmark, SES).
