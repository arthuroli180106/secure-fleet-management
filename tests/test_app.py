import io
from datetime import date
from app.extensions import db
from PIL import Image
from app.models import Vehicle, Driver, MaintenancePhoto

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

def test_vehicle_and_driver_can_be_archived_and_restored(client, app):
    with app.app_context():
        vehicle = Vehicle(plate="ARCH123", make="Honda", model="Civic", year=2021)
        driver = Driver(full_name="Test Driver")
        db.session.add_all([vehicle, driver])
        db.session.commit()
        vehicle_id, driver_id = vehicle.id, driver.id

    login(client, "manager@example.test", "Manager-Password-123!")
    response = client.post(f"/vehicles/{vehicle_id}/archive", data={"reason": "Vehicle sold"})
    assert response.status_code == 302
    response = client.post(f"/drivers/{driver_id}/archive", data={"reason": "Contract ended"})
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Vehicle, vehicle_id).archived_at is not None
        assert db.session.get(Driver, driver_id).archived_at is not None

    client.post(f"/vehicles/{vehicle_id}/restore")
    client.post(f"/drivers/{driver_id}/restore")
    with app.app_context():
        assert db.session.get(Vehicle, vehicle_id).archived_at is None
        assert db.session.get(Driver, driver_id).archived_at is None

def test_maintenance_accepts_and_protects_photo_upload(client, app):
    with app.app_context():
        vehicle = Vehicle(plate="PHOTO1", make="Ford", model="Ka", year=2020)
        db.session.add(vehicle)
        db.session.commit()
        vehicle_id = vehicle.id

    login(client, "manager@example.test", "Manager-Password-123!")
    png_stream = io.BytesIO()
    Image.new("RGB", (1, 1), (20, 40, 60)).save(png_stream, format="PNG")
    png_stream.seek(0)
    response = client.post("/maintenance/new", data={
        "vehicle_id": str(vehicle_id),
        "description": "Front bumper inspection",
        "cost": "150.00",
        "service_date": date.today().isoformat(),
        "photos": (png_stream, "front-bumper.png"),
    }, content_type="multipart/form-data")
    assert response.status_code == 302

    with app.app_context():
        photo = db.session.query(MaintenancePhoto).first()
        assert photo is not None
        photo_id = photo.id

    response = client.get(f"/maintenance-photos/{photo_id}")
    assert response.status_code == 200
    assert response.data.startswith(bytes.fromhex("89504E470D0A1A0A"))
