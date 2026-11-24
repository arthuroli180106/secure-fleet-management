import pytest
from app import create_app
from app.extensions import db
from app.models import User

@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "RATELIMIT_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        admin = User(email="admin@example.test", role="admin")
        admin.set_password("Admin-Password-123!")
        manager = User(email="manager@example.test", role="manager")
        manager.set_password("Manager-Password-123!")
        staff = User(email="staff@example.test", role="staff")
        staff.set_password("Staff-Password-123!")
        db.session.add_all([admin, manager, staff])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()