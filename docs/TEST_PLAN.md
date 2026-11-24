# Test Plan

## Functional tests

- Health endpoint responds successfully
- Unauthenticated users cannot access dashboard
- Valid credentials authenticate
- Invalid credentials are rejected
- Staff cannot access admin-only audit log
- Staff cannot create fleet records
- Manager can create a vehicle
- Invalid vehicle status is rejected
- Duplicate plates are rejected
- Security headers are present
- Password hashing does not store plaintext

## Manual security exercises (local test environment only)

- Submit a request without a CSRF token and verify rejection
- Attempt repeated login POSTs and verify rate limiting
- Attempt direct URL access to manager/admin routes as staff
- Enter HTML/script strings in text fields and confirm Jinja autoescaping
- Review the audit trail after state-changing actions

Never test against systems you do not own or have explicit permission to assess.