from datetime import datetime, timezone
from flask_login import UserMixin
from .extensions import db
from .security import hash_password, verify_password

def utcnow():
    return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        return verify_password(self.password_hash, password)

    @property
    def is_active(self):
        return self.active

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(16), unique=True, nullable=False, index=True)
    make = db.Column(db.String(60), nullable=False)
    model = db.Column(db.String(60), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="available")
    notes = db.Column(db.String(500), nullable=True)
    archived_at = db.Column(db.DateTime(timezone=True), nullable=True)
    archive_reason = db.Column(db.String(250), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(254), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    archived_at = db.Column(db.DateTime(timezone=True), nullable=True)
    archive_reason = db.Column(db.String(250), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

class Maintenance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    cost = db.Column(db.Numeric(10, 2), nullable=False)
    service_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="scheduled")
    vehicle = db.relationship("Vehicle", backref="maintenance_records")

class MaintenancePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    maintenance_id = db.Column(db.Integer, db.ForeignKey("maintenance.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = db.Column(db.String(80), nullable=False, unique=True)
    original_name = db.Column(db.String(180), nullable=False)
    uploaded_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    maintenance = db.relationship("Maintenance", backref=db.backref("photos", cascade="all, delete-orphan"))

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("driver.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    reference = db.Column(db.String(80), nullable=True)
    driver = db.relationship("Driver", backref="payments")

class AuditEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    action = db.Column(db.String(80), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.String(40), nullable=True)
    details = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    actor = db.relationship("User")
