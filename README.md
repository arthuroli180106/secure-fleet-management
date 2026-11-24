# Secure Fleet Management System

A security-focused fleet management application built for a small vehicle-rental business. This is a portfolio project and a local-first MVP, using fictional seed data only.

## Features

- User authentication with Argon2 password hashing
- Role-based access control: `admin`, `manager`, and `staff`
- CSRF protection, secure session settings, login rate limiting
- Fleet inventory and vehicle status tracking
- Driver records
- Maintenance records
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
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
flask --app run.py init-db
flask --app run.py seed-demo
flask --app run.py run --debug
```

Open http://127.0.0.1:5000.

Demo accounts (change immediately; local demo only):
- Admin: `admin@example.test` / `ChangeMe-Admin-123!`
- Manager: `manager@example.test` / `ChangeMe-Manager-123!`
- Staff: `staff@example.test` / `ChangeMe-Staff-123!`

Do not use demo credentials in a deployed environment.

## Environment variables

See `.env.example`. A unique `SECRET_KEY` is required outside development. Set `FLASK_ENV=production`, `SESSION_COOKIE_SECURE=true`, and serve only behind HTTPS in production.

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

**Secure Fleet Management System** — Built a Flask-based fleet management application with role-based access control, Argon2 password hashing, CSRF protection, rate-limited authentication, audit logging, input validation, and automated security-focused tests.
