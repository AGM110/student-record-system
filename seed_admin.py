# from app import app
# from utils.db import db
# from utils.models import UserModel
# from werkzeug.security import generate_password_hash

# ##new
# from sqlalchemy import text
# print(">> Seed script DB:", db.engine.url.database)
# print(">> Users before seed:", db.session.execute(text("SELECT COUNT(*) FROM users")).scalar() if db.inspect(db.engine).has_table("users") else 0)
# ##new

# app.app_context().push()

# if not UserModel.query.filter_by(username="admin").first():
#     db.session.add(UserModel(
#         username="admin",
#         email="admin@mailtrap.io",
#         password=generate_password_hash("secret123")
#     ))
#     db.session.commit()

# print("Users:", [(u.id, u.username) for u in UserModel.query.all()])




# seed_admin.py
from app import app
from utils.db import db
from utils.models import UserModel
from werkzeug.security import generate_password_hash
from sqlalchemy import inspect, text

with app.app_context():
    db.create_all()
    print(">> Seed script DB:", db.engine.url.database)

    insp = inspect(db.engine)
    user_count = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar() if insp.has_table("users") else 0
    print(">> Users before seed:", user_count)

    if not UserModel.query.filter_by(username="admin").first():
        db.session.add(UserModel(
            username="admin",
            email="admin@mailtrap.io",
            password=generate_password_hash("secret123")
        ))
        db.session.commit()
        print(">> Admin user created.")

    print("Users:", [(u.id, u.username) for u in UserModel.query.all()])

