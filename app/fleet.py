from datetime import date
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from .extensions import db
from .models import Vehicle, Driver, Maintenance, Payment, AuditEvent
from .security import roles_required

fleet_bp = Blueprint("fleet", __name__)

def log_event(action, entity_type, entity_id=None, details=""):
    db.session.add(AuditEvent(
        actor_user_id=current_user.id, action=action, entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        details=details[:500], ip_address=request.remote_addr
    ))

@fleet_bp.get("/")
@login_required
def dashboard():
    return render_template("dashboard.html",
        vehicles=Vehicle.query.order_by(Vehicle.plate).all(),
        drivers=Driver.query.order_by(Driver.full_name).all(),
        maintenance=Maintenance.query.order_by(Maintenance.service_date.desc()).limit(5).all(),
        payments=Payment.query.order_by(Payment.due_date.desc()).limit(5).all())

@fleet_bp.route("/vehicles/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def new_vehicle():
    if request.method == "POST":
        plate = request.form.get("plate", "").strip().upper()
        make = request.form.get("make", "").strip()
        model = request.form.get("model", "").strip()
        try:
            year = int(request.form.get("year", "0"))
        except ValueError:
            year = 0
        status = request.form.get("status", "available")
        if not (2 <= len(plate) <= 16 and make and model and 1990 <= year <= date.today().year + 1):
            flash("Please provide valid vehicle details.", "error")
            return render_template("vehicle_form.html")
        if status not in {"available", "rented", "maintenance", "inactive"}:
            abort(400)
        vehicle = Vehicle(plate=plate, make=make, model=model, year=year, status=status)
        db.session.add(vehicle)
        try:
            db.session.flush()
            log_event("vehicle_created", "vehicle", vehicle.id, f"Vehicle {plate} created")
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("A vehicle with that plate already exists.", "error")
            return render_template("vehicle_form.html")
        return redirect(url_for("fleet.dashboard"))
    return render_template("vehicle_form.html")

@fleet_bp.post("/vehicles/<int:vehicle_id>/status")
@login_required
@roles_required("admin", "manager")
def update_vehicle_status(vehicle_id):
    vehicle = db.session.get(Vehicle, vehicle_id) or abort(404)
    status = request.form.get("status", "")
    if status not in {"available", "rented", "maintenance", "inactive"}:
        abort(400)
    old = vehicle.status
    vehicle.status = status
    log_event("vehicle_status_changed", "vehicle", vehicle.id, f"{old} -> {status}")
    db.session.commit()
    return redirect(url_for("fleet.dashboard"))

@fleet_bp.route("/drivers/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def new_driver():
    if request.method == "POST":
        name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower() or None
        phone = request.form.get("phone", "").strip() or None
        if not name or len(name) > 120 or (email and len(email) > 254):
            flash("Please provide valid driver details.", "error")
            return render_template("driver_form.html")
        driver = Driver(full_name=name, email=email, phone=phone)
        db.session.add(driver)
        db.session.flush()
        log_event("driver_created", "driver", driver.id, "Driver record created")
        db.session.commit()
        return redirect(url_for("fleet.dashboard"))
    return render_template("driver_form.html")

@fleet_bp.route("/maintenance/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def new_maintenance():
    vehicles = Vehicle.query.order_by(Vehicle.plate).all()
    if request.method == "POST":
        try:
            vehicle_id = int(request.form.get("vehicle_id", "0"))
            cost = Decimal(request.form.get("cost", "0"))
            service_date = date.fromisoformat(request.form.get("service_date", ""))
        except (ValueError, InvalidOperation):
            flash("Please provide valid maintenance details.", "error")
            return render_template("maintenance_form.html", vehicles=vehicles)
        vehicle = db.session.get(Vehicle, vehicle_id)
        description = request.form.get("description", "").strip()
        if not vehicle or not description or len(description) > 300 or cost < 0 or cost > Decimal("99999999.99"):
            flash("Please provide valid maintenance details.", "error")
            return render_template("maintenance_form.html", vehicles=vehicles)
        item = Maintenance(vehicle=vehicle, description=description, cost=cost, service_date=service_date)
        db.session.add(item)
        db.session.flush()
        log_event("maintenance_created", "maintenance", item.id, f"Vehicle {vehicle.plate}")
        db.session.commit()
        return redirect(url_for("fleet.dashboard"))
    return render_template("maintenance_form.html", vehicles=vehicles)

@fleet_bp.route("/payments/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def new_payment():
    drivers = Driver.query.order_by(Driver.full_name).all()
    if request.method == "POST":
        try:
            driver_id = int(request.form.get("driver_id", "0"))
            amount = Decimal(request.form.get("amount", "0"))
            due_date = date.fromisoformat(request.form.get("due_date", ""))
        except (ValueError, InvalidOperation):
            flash("Please provide valid payment details.", "error")
            return render_template("payment_form.html", drivers=drivers)
        driver = db.session.get(Driver, driver_id)
        if not driver or amount <= 0 or amount > Decimal("99999999.99"):
            flash("Please provide valid payment details.", "error")
            return render_template("payment_form.html", drivers=drivers)
        payment = Payment(driver=driver, amount=amount, due_date=due_date)
        db.session.add(payment)
        db.session.flush()
        log_event("payment_created", "payment", payment.id, "Payment record created")
        db.session.commit()
        return redirect(url_for("fleet.dashboard"))
    return render_template("payment_form.html", drivers=drivers)

@fleet_bp.get("/audit")
@login_required
@roles_required("admin")
def audit_log():
    events = AuditEvent.query.order_by(AuditEvent.created_at.desc()).limit(200).all()
    return render_template("audit.html", events=events)
