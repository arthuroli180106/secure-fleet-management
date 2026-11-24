from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database tables created.")

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