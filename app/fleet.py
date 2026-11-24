import os
import uuid
from io import BytesIO
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from PIL import Image, ImageOps, UnidentifiedImageError
from .extensions import db
from .models import Vehicle, Driver, Maintenance, MaintenancePhoto, Payment, AuditEvent, utcnow
from .security import roles_required

fleet_bp = Blueprint("fleet", __name__)
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024

def log_event(action, entity_type, entity_id=None, details=""):
    db.session.add(AuditEvent(
        actor_user_id=current_user.id, action=action, entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        details=details[:500], ip_address=request.remote_addr
    ))

def active_vehicles():
    return Vehicle.query.filter(Vehicle.archived_at.is_(None)).order_by(Vehicle.plate).all()

def sanitize_image(data, suffix):
    formats = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}
    try:
        with Image.open(BytesIO(data)) as source:
            if source.format != formats[suffix] or source.width * source.height > 25_000_000:
                raise ValueError("Unsupported or excessively large image.")
            source.verify()
        with Image.open(BytesIO(data)) as source:
            image = ImageOps.exif_transpose(source)
            image.thumbnail((4000, 4000))
            if formats[suffix] == "JPEG":
                image = image.convert("RGB")
            output = BytesIO()
            image.save(output, format=formats[suffix], optimize=True)
            cleaned = output.getvalue()
            if len(cleaned) > MAX_IMAGE_SIZE:
                raise ValueError("Processed photo exceeds the 5 MB limit.")
            return cleaned
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValueError("The uploaded file is not a valid supported image.") from error

def save_maintenance_images(maintenance):
    files = request.files.getlist("photos")
    uploads_dir = os.path.join(current_app.instance_path, "uploads")
    os.makedirs(uploads_dir, mode=0o700, exist_ok=True)
    for uploaded in files:
        if not uploaded or not uploaded.filename:
            continue
        original = Path(uploaded.filename).name[:180]
        suffix = Path(original).suffix.lower()
        if suffix not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError("Use only JPG, PNG, or WEBP photos.")
        data = uploaded.read(MAX_IMAGE_SIZE + 1)
        if not data or len(data) > MAX_IMAGE_SIZE:
            raise ValueError("Each photo must be no larger than 5 MB.")
        data = sanitize_image(data, suffix)
        filename = f"{uuid.uuid4().hex}{suffix}"
        target = os.path.join(uploads_dir, filename)
        with open(target, "xb") as destination:
            destination.write(data)
        db.session.add(MaintenancePhoto(
            maintenance=maintenance, filename=filename, original_name=original
        ))

@fleet_bp.get("/")
@login_required
def dashboard():
    vehicles = Vehicle.query.filter(Vehicle.archived_at.is_(None)).order_by(Vehicle.plate).all()
    drivers = Driver.query.filter(Driver.archived_at.is_(None)).order_by(Driver.full_name).all()
    maintenance = Maintenance.query.join(Vehicle).filter(Vehicle.archived_at.is_(None)).order_by(Maintenance.service_date.desc()).limit(5).all()
    payments = Payment.query.join(Driver).filter(Driver.archived_at.is_(None)).order_by(Payment.due_date.desc()).limit(5).all()
    return render_template("dashboard.html", vehicles=vehicles, drivers=drivers, maintenance=maintenance, payments=payments)

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
    if vehicle.archived_at:
        abort(404)
    status = request.form.get("status", "")
    if status not in {"available", "rented", "maintenance", "inactive"}:
        abort(400)
    old = vehicle.status
    vehicle.status = status
    log_event("vehicle_status_changed", "vehicle", vehicle.id, f"{old} -> {status}")
    db.session.commit()
    return redirect(url_for("fleet.dashboard"))

@fleet_bp.post("/vehicles/<int:vehicle_id>/archive")
@login_required
@roles_required("admin", "manager")
def archive_vehicle(vehicle_id):
    vehicle = db.session.get(Vehicle, vehicle_id) or abort(404)
    reason = request.form.get("reason", "").strip()
    if not reason or len(reason) > 250:
        flash("Enter a reason (for example, vehicle sold).", "error")
        return redirect(url_for("fleet.dashboard"))
    vehicle.archived_at = utcnow()
    vehicle.archive_reason = reason
    vehicle.status = "inactive"
    log_event("vehicle_archived", "vehicle", vehicle.id, f"{vehicle.plate}: {reason}")
    db.session.commit()
    flash("Vehicle archived. Its payment and maintenance history was preserved.", "success")
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

@fleet_bp.post("/drivers/<int:driver_id>/archive")
@login_required
@roles_required("admin", "manager")
def archive_driver(driver_id):
    driver = db.session.get(Driver, driver_id) or abort(404)
    reason = request.form.get("reason", "").strip()
    if not reason or len(reason) > 250:
        flash("Enter a reason (for example, contract ended).", "error")
        return redirect(url_for("fleet.dashboard"))
    driver.archived_at = utcnow()
    driver.archive_reason = reason
    driver.active = False
    log_event("driver_archived", "driver", driver.id, f"{driver.full_name}: {reason}")
    db.session.commit()
    flash("Driver archived. Their payment history was preserved.", "success")
    return redirect(url_for("fleet.dashboard"))

@fleet_bp.get("/archive")
@login_required
@roles_required("admin", "manager")
def archive_list():
    vehicles = Vehicle.query.filter(Vehicle.archived_at.is_not(None)).order_by(Vehicle.archived_at.desc()).all()
    drivers = Driver.query.filter(Driver.archived_at.is_not(None)).order_by(Driver.archived_at.desc()).all()
    return render_template("archive.html", vehicles=vehicles, drivers=drivers)

@fleet_bp.post("/vehicles/<int:vehicle_id>/restore")
@login_required
@roles_required("admin", "manager")
def restore_vehicle(vehicle_id):
    vehicle = db.session.get(Vehicle, vehicle_id) or abort(404)
    vehicle.archived_at = None
    vehicle.archive_reason = None
    vehicle.status = "available"
    log_event("vehicle_restored", "vehicle", vehicle.id, f"Vehicle {vehicle.plate} restored")
    db.session.commit()
    return redirect(url_for("fleet.archive_list"))

@fleet_bp.post("/drivers/<int:driver_id>/restore")
@login_required
@roles_required("admin", "manager")
def restore_driver(driver_id):
    driver = db.session.get(Driver, driver_id) or abort(404)
    driver.archived_at = None
    driver.archive_reason = None
    driver.active = True
    log_event("driver_restored", "driver", driver.id, f"Driver {driver.full_name} restored")
    db.session.commit()
    return redirect(url_for("fleet.archive_list"))

@fleet_bp.route("/maintenance/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def new_maintenance():
    vehicles = active_vehicles()
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
        if not vehicle or vehicle.archived_at or not description or len(description) > 300 or cost < 0 or cost > Decimal("99999999.99"):
            flash("Please provide valid maintenance details.", "error")
            return render_template("maintenance_form.html", vehicles=vehicles)
        item = Maintenance(vehicle=vehicle, description=description, cost=cost, service_date=service_date)
        db.session.add(item)
        try:
            db.session.flush()
            save_maintenance_images(item)
            log_event("maintenance_created", "maintenance", item.id, f"Vehicle {vehicle.plate}; photos: {len(item.photos)}")
            db.session.commit()
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
            return render_template("maintenance_form.html", vehicles=vehicles)
        except OSError:
            db.session.rollback()
            flash("The photos could not be saved. Please try again.", "error")
            return render_template("maintenance_form.html", vehicles=vehicles)
        return redirect(url_for("fleet.maintenance_detail", maintenance_id=item.id))
    return render_template("maintenance_form.html", vehicles=vehicles)

@fleet_bp.get("/maintenance/<int:maintenance_id>")
@login_required
def maintenance_detail(maintenance_id):
    item = db.session.get(Maintenance, maintenance_id) or abort(404)
    return render_template("maintenance_detail.html", item=item)

@fleet_bp.post("/maintenance/<int:maintenance_id>/photos")
@login_required
@roles_required("admin", "manager")
def add_maintenance_photos(maintenance_id):
    item = db.session.get(Maintenance, maintenance_id) or abort(404)
    try:
        save_maintenance_images(item)
        if not item.photos:
            flash("Choose at least one photo.", "error")
        else:
            log_event("maintenance_photos_added", "maintenance", item.id, f"Photos attached to {item.vehicle.plate}")
            db.session.commit()
            flash("Photos uploaded.", "success")
    except ValueError as error:
        db.session.rollback()
        flash(str(error), "error")
    except OSError:
        db.session.rollback()
        flash("The photos could not be saved. Please try again.", "error")
    return redirect(url_for("fleet.maintenance_detail", maintenance_id=item.id))

@fleet_bp.get("/maintenance-photos/<int:photo_id>")
@login_required
def maintenance_photo(photo_id):
    photo = db.session.get(MaintenancePhoto, photo_id) or abort(404)
    return send_from_directory(os.path.join(current_app.instance_path, "uploads"), photo.filename)

@fleet_bp.route("/payments/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def new_payment():
    drivers = Driver.query.filter(Driver.archived_at.is_(None)).order_by(Driver.full_name).all()
    if request.method == "POST":
        try:
            driver_id = int(request.form.get("driver_id", "0"))
            amount = Decimal(request.form.get("amount", "0"))
            due_date = date.fromisoformat(request.form.get("due_date", ""))
        except (ValueError, InvalidOperation):
            flash("Please provide valid payment details.", "error")
            return render_template("payment_form.html", drivers=drivers)
        driver = db.session.get(Driver, driver_id)
        if not driver or driver.archived_at or amount <= 0 or amount > Decimal("99999999.99"):
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
