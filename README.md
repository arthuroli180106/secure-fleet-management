# Secure Fleet Management System

A security-focused fleet management application built for a small vehicle-rental business. This is a portfolio project and a local-first MVP, using fictional seed data only.

## Features

- User authentication with Argon2 password hashing
- Role-based access control: `admin`, `manager`, and `staff`
- CSRF protection, secure session settings, login rate limiting
- Fleet inventory and vehicle status tracking
- Archive and restore vehicles (for example, when sold) and drivers (when a contract ends), with an audit trail and preserved financial/maintenance history
- Maintenance records with protected JPG, PNG, and WEBP photo attachments
- Payment records (amounts only; no bank/card details)
- Append-only-style audit event recording for important actions
- Input validation and server-side authorization
- Automated tests with pytest

## Technology

Python 3.11+, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Limiter, Argon2, SQLite, pytest.

## Quick start

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\\Scripts\\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
flask --app run.py init-db
flask --app run.py upgrade-db
flask --app run.py seed-demo
flask --app run.py run --debug
```

If you already have a local copy, pull the latest code and run `flask --app run.py upgrade-db` before restarting the app. This adds the archive fields and photo table while preserving existing records.

Open http://127.0.0.1:5000.

Demo accounts (change immediately; local demo only):
- Admin: `admin@example.test` / `ChangeMe-Admin-123!`
- Manager: `manager@example.test` / `ChangeMe-Manager-123!`
- Staff: `staff@example.test` / `ChangeMe-Staff-123!`

Do not use demo credentials in a deployed environment.

## Photo uploads

Photos are limited to JPG, PNG, and WEBP, with a 5 MB per-file limit. They are stored in the local `instance/uploads/` folder and served only to authenticated users. The instance folder is excluded from Git. Configure private persistent storage, backups, malware scanning, and retention rules before production use.

## Pix integration status

Pix automation is not enabled yet. It requires an official API from the bank or payment provider receiving the Pix payments, plus a verified webhook and reconciliation rules. Never put bank passwords, private keys, or API secrets in GitHub. The exact provider must be selected before implementing the connector.

## Environment variables

See `.env.example`. A unique `SECRET_KEY` is required outside development. Set `SESSION_COOKIE_SECURE=true` and serve only behind HTTPS in production.

## Security design

See:
- [Threat model](docs/THREAT_MODEL.md)
- [Security controls](docs/SECURITY_CONTROLS.md)
- [Test plan](docs/TEST_PLAN.md)
- [Deployment checklist](docs/DEPLOYMENT.md)

### Important limitations

This MVP is not yet production-ready. Before real business use, add a managed production database, HTTPS reverse proxy, centralized backups, monitoring/alerting, account recovery, MFA, data-retention rules, and a formal privacy review. Do not store government IDs, full payment-card data, bank credentials, or unnecessary sensitive personal information. Use fictional data in the public GitHub repository.

## Project structure

```text
secure-fleet-management/
├── app/
│   ├── __init__.py
│   ├── auth.py
│   ├── extensions.py
│   ├── models.py
│   ├── security.py
│   ├── fleet.py
│   ├── templates/
│   └── static/
├── docs/
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── run.py
```

## Portfolio description

**Secure Fleet Management System** — Built a Flask-based fleet management application with role-based access control, Argon2 password hashing, CSRF protection, rate-limited authentication, audit logging, secure maintenance photo uploads, vehicle/driver lifecycle management, input validation, and automated security-focused tests.
