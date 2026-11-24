# Security Controls

- **Authentication:** Argon2 password hashing; no plaintext password storage.
- **Authorization:** server-side role checks on write operations; audit log is admin-only.
- **CSRF:** Flask-WTF protection on forms.
- **Rate limiting:** login endpoint limited to five POST attempts per minute per client IP.
- **Session cookies:** HttpOnly and SameSite=Lax; Secure must be enabled behind HTTPS in production.
- **Headers:** CSP, frame denial, MIME sniffing protection, referrer policy, permissions policy; HSTS when secure-cookie mode is enabled.
- **Input validation:** length, allowed status, date, numeric and foreign-key checks.
- **Database access:** SQLAlchemy ORM.
- **Audit trail:** records authentication outcomes and key create/update events.

## Planned next controls

1. MFA (TOTP or WebAuthn)
2. Password reset with single-use expiring tokens
3. Stronger audit integrity (external append-only storage)
4. PostgreSQL with least-privilege database credentials
5. Encrypted backups and tested restore procedure
6. Centralized logs and alerting (e.g. Wazuh)
7. Automated dependency and secret scanning in CI