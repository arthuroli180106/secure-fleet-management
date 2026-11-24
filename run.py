from sqlalchemy import inspect, text
from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database tables created.")

@app.cli.command("upgrade-db")
def upgrade_db():
    """Apply the small SQLite schema update needed by existing local installs."""
    db.create_all()
    inspector = inspect(db.engine)
    if db.engine.dialect.name == "sqlite":
        additions = {
            "vehicle": {
                "archived_at": "DATETIME",
                "archive_reason": "VARCHAR(250)",
            },
            "driver": {
                "archived_at": "DATETIME",
                "archive_reason": "VARCHAR(250)",
            },
        }
        for table, columns in additions.items():
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, sql_type in columns.items():
                if name not in existing:
                    db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}"))
        db.session.commit()
    elif db.engine.dialect.name != "sqlite":
        raise RuntimeError("Run the project's production database migrations for this database engine.")
    print("Database upgraded. Existing vehicle, driver, payment, and maintenance records were preserved.")

@app.cli.command("seed-demo")
def seed_demo():
    db.create_all()
    demo_users = [
        ("admin@example.test", "ChangeMe-Admin-123!", "admin"),
        ("manager@example.test", "ChangeMe-Manager-123!", "manager"),
        ("staff@example.test", "ChangeMe-Staff-123!", "staff"),
    ]
    for email, password, role in demo_users:
        if not User.query.filter_by(email=email).first():
            user = User(email=email, role=role, active=True)
            user.set_password(password)
            db.session.add(user)
    db.session.commit()
    print("Demo users created if absent. Change demo passwords before any deployment.")

if __name__ == "__main__":
    app.run()
