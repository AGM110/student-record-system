
from utils.db import db

class StudentModel(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(32), nullable=False, unique=True, index=True)
    country = db.Column(db.String(80), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    program = db.Column(db.String(16), nullable=False) 
    subject = db.Column(db.String(120), nullable=False)

    def to_dict(self):
        return {
            "name": self.name,
            "code": self.code,
            "country": self.country,
            "year": str(self.year),
            "program": self.program,
            "subject": self.subject,
        }

class UserModel(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  
    reset_token = db.Column(db.String(64), nullable=True) 
