# Deployment Checklist

This project is intended for local development and portfolio demonstration.

Before production:
- [ ] Replace demo accounts and remove demo seed credentials
- [ ] Set a long random `SECRET_KEY` through a secret manager
- [ ] Use PostgreSQL and a dedicated least-privilege database user
- [ ] Set `SESSION_COOKIE_SECURE=true`
- [ ] Terminate HTTPS at a correctly configured reverse proxy
- [ ] Disable debug mode
- [ ] Configure persistent rate-limit storage (Redis)
- [ ] Configure encrypted, off-site backups and test restores
- [ ] Add MFA and secure account recovery
- [ ] Configure centralized monitoring and alerting
- [ ] Establish retention, access review, and incident response procedures
- [ ] Complete privacy and legal review before storing real driver/customer data
