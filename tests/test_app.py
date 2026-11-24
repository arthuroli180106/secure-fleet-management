from app.models import Vehicle

def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)

def test_health_and_security_headers(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in response.headers

def test_dashboard_requires_login(client):
    response = client.get("/")
    assert response.status_code in (302, 401)

def test_valid_login(client):
    response = login(client, "admin@example.test", "Admin-Password-123!")
    assert response.status_code == 200
    assert b"Fleet dashboard" in response.data

def test_invalid_login_rejected(client):
    response = login(client, "admin@example.test", "wrong")
    assert b"Invalid email or password" in response.data

def test_staff_cannot_open_audit_log(client):
    login(client, "staff@example.test", "Staff-Password-123!")
    response = client.get("/audit")
    assert response.status_code == 403

def test_staff_cannot_create_vehicle(client):
    login(client, "staff@example.test", "Staff-Password-123!")
    response = client.get("/vehicles/new")
    assert response.status_code == 403

def test_manager_can_create_vehicle(client, app):
    login(client, "manager@example.test", "Manager-Password-123!")
    response = client.post("/vehicles/new", data={
        "plate": "DEMO123", "make": "Toyota", "model": "Corolla",
        "year": "2022", "status": "available"
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert Vehicle.query.filter_by(plate="DEMO123").first() is not None

def test_invalid_vehicle_status_rejected(client):
    login(client, "manager@example.test", "Manager-Password-123!")
    response = client.post("/vehicles/new", data={
        "plate": "DEMO124", "make": "Toyota", "model": "Corolla",
        "year": "2022", "status": "hacked"
    })
    assert response.status_code == 400