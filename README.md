# KitCalendar

A small, local-first Django equipment reservation board for one school, club or team. Members request a camera, projector or other shared item. An administrator approves the request, records checkout, and records its return with condition notes.

**Local prototype, not a hosted service or a production-ready lending platform.** It has no paid APIs, email, SMS, reminders, deposits, external calendar connections or cloud deployment. Dates are a list, not a month-grid calendar. Existing tools in this category already exist; this is an independent, deliberately small implementation, not a claim of invention.

## Quick start

Python 3.10+ is required. Tested with Python 3.10 and Django 5.2.19.

```sh
python -m venv .venv
# Linux / macOS:
. .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Open http://127.0.0.1:8000 and sign in with the account you just created. The superuser is also a staff administrator. Add physical items from the board. Each row represents one unit, so use names such as `Camera 01` and `Camera 02`, not a quantity field.

Create a member from another terminal with the same environment active:

```sh
python manage.py add_member alex
python manage.py changepassword alex
```

The command never assigns a shared default password. Account creation is local-administrator-only. There is no public signup or password reset email. Django's password prompts and validators are used for passwords you choose.

### Optional fictional demo

Use an empty database after `migrate`:

```sh
python manage.py seed_demo
python manage.py changepassword demo-admin
python manage.py changepassword demo-member
python manage.py runserver 127.0.0.1:8000
```

All seeded equipment, users and reservations are fictional. The seed command creates no usable passwords. It refuses to run when either demo username already exists, rather than modifying an account. Do not use demo data in a real shared installation.

## Workflow and rules

- Members can request active equipment for today or later. Dates include **both** the start and return day. A return on Friday means the next reservation starts Saturday.
- Pending, approved and checked-out reservations hold dates. Overlaps are blocked even while requests wait for approval. Administrators should decline stale pending requests; they do not expire automatically.
- An administrator can approve or decline pending requests. Approval rechecks availability and rejects past start dates.
- Checkout is allowed only within the approved date window. An overdue physical checkout blocks a later checkout of that same unit until its return is recorded.
- Administrators can record optional handover and return condition notes. Only checked-out items can be returned.
- Owners and administrators can cancel pending or approved requests. Checked-out items must be returned, not cancelled. Returned, declined and cancelled reservations release their dates.
- The dashboard reports checked-out items due today or overdue. It does not send reminders.
- Members see their own request purposes, condition notes and borrower details. All signed-in members see the equipment's reserved dates and status, without other borrowers' names or notes. Administrators can see all requests and notes.
- Django login, POST-only changes, CSRF protection and template autoescaping are used. There are no third-party frontend resources or analytics.

## Local storage and limits

The SQLite database `db.sqlite3` stores accounts, password hashes, reservations and notes in the project directory. It is excluded from Git. Keep backups yourself and protect your computer and database. Never commit a real database or real borrower data. The browser and local server communicate locally; no external service is contacted by the app.

The default time zone is `Asia/Kolkata`; set `KITCALENDAR_TIME_ZONE` to a valid IANA zone before starting if your organization uses another. Reservation dates are day-level and interpreted in that configured zone.

Every reservation mutation first writes to an equipment row inside one transaction. This serializes conflicting SQLite writers before the availability check. Busy-database errors are shown as retryable failures, not silently accepted reservations. This is a small-installation design, not a distributed or high-volume booking system. Direct database edits can bypass application overlap rules. There is no immutable audit log, bulk inventory editing, recurring bookings, quantities, waitlist or automatic expiry.

Do **not** expose Django's development server to the internet or use these defaults for customer data. Production use needs its own deployment/security work: a random `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, configured hosts, HTTPS, secure cookies, a production server, backup/restore practice, login rate limiting, access review and operational testing. The development key in settings is deliberately public and only for localhost. This repository does not provide or authorize a hosted deployment.

## Tests

```sh
python manage.py test
python manage.py check
```

Tests cover date boundaries, overlap protection, lifecycle transitions, permissions, private-note visibility, CSRF, escaped text, equipment creation and condition notes. They are not a security audit or a multi-server stress test.

## Project layout

- `board/models.py`: equipment and reservation records, date constraint
- `board/services.py`: transactional booking and state transitions
- `board/views.py`, `board/forms.py`: authenticated request handling
- `board/templates/`: responsive server-rendered UI, no JavaScript dependency
- `board/management/commands/`: optional demo and local member creation
- `board/tests.py`: automated regression tests

## Background and alternatives

The problem is described in [Snipe-IT's dated reservation request](https://github.com/grokability/snipe-it/issues/5081) and [future checkout request](https://github.com/grokability/snipe-it/issues/11356). Those issue authors did not request, endorse or test this project.

For existing solutions, compare [Toolshed](https://github.com/acwilsondev/toolshed) and [SnipeScheduler](https://github.com/JSY-Ben/SnipeScheduler). This project is not affiliated with those projects and does not reuse their source code.

## License

Original code is available under the [MIT License](LICENSE). Django has its own license. The MIT license here does not replace dependency or third-party content licenses and grants no trademark rights.
