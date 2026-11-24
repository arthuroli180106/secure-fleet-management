# Threat Model

## Scope

The application manages fleet, driver, maintenance, and payment-due records for a small rental business. The public repository must contain only synthetic data.

## Assets

- User accounts and password hashes
- Vehicle inventory and rental status
- Driver contact details
- Maintenance and payment records
- Audit history
- Application secret and database

## Trust boundaries

1. Browser to Flask application
2. Flask application to SQLite/database
3. Authenticated user roles inside the application
4. Application host and its environment variables

## Threat actors

- External attacker attempting credential stuffing or exploiting web input
- Malicious or compromised employee
- Unauthorized person using an unattended logged-in device
- Accidental administrator error

## Main threats and mitigations

| Threat | Impact | MVP mitigation |
|---|---|---|
| Password guessing | Account takeover | Argon2 hashing and login rate limit |
| CSRF | Unauthorized state changes | Flask-WTF CSRF protection |
| Privilege escalation | Unauthorized data changes | Server-side role checks |
| SQL injection | Data disclosure/modification | SQLAlchemy parameterized ORM |
| Session theft | Account misuse | HttpOnly, SameSite, Secure-in production cookies |
| Data tampering | Incorrect fleet/payment records | Audit events for key mutations |
| Sensitive data exposure | Privacy harm | Minimize collected fields; no card/bank credentials |
| Public repository leak | Business/customer exposure | Synthetic seed data; .env ignored |

## Residual risks

MFA, password reset, centralized immutable audit storage, database encryption-at-rest, production monitoring, backup restoration tests, and formal authorization review are not implemented in this MVP. Do not deploy with real personal data until these are addressed.