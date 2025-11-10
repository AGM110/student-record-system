from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from collections import Counter
import re, json, csv, io, uuid

from utils.db import db
from utils.models import StudentModel

from utils.models import StudentModel, UserModel
import os
import os.path as op


app = Flask(__name__)


# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'  
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if os.getenv("SRMS_TESTING") == "1":
    # In tests,  an in-memory DB
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'students.db')
    print(">> Using DB:", app.config["SQLALCHEMY_DATABASE_URI"])


app.secret_key = 'aqsagm'
db.init_app(app)



###existing
app.config.update(
    MAIL_SERVER='sandbox.smtp.mailtrap.io',
    MAIL_PORT=587,
    MAIL_USERNAME='512f23da45dc4c',
    MAIL_PASSWORD='35ddc19771d6a1',
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_DEFAULT_SENDER='admin@mailtrap.io'
)



# ...existing 
# app.config.update(
#     MAIL_SERVER='sandbox.smtp.mailtrap.io',
#     MAIL_PORT=587,
#     MAIL_USERNAME='512f23da45dc4c',
#     MAIL_PASSWORD='35ddc19771d6a1',
#     MAIL_USE_TLS=True,
#     MAIL_USE_SSL=False,
#     MAIL_DEFAULT_SENDER='admin@mailtrap.io',
#     # Add these configurations
#     ADMIN_USERNAME='admin',
#     ADMIN_PASSWORD=generate_password_hash('aqsagm'),
#     SQLALCHEMY_TRACK_MODIFICATIONS=False
# )



mail = Mail(app)


COUNTRIES = [
    "Afghanistan","Albania","Algeria","Andorra","Angola","Antigua and Barbuda","Argentina","Armenia","Australia",
    "Austria","Austrian Empire*","Azerbaijan","Baden*","Bahamas, The","Bahrain","Bangladesh","Barbados","Bavaria*",
    "Belarus","Belgium","Belize","Benin (Dahomey)","Bolivia","Bosnia and Herzegovina","Botswana","Brazil","Brunei",
    "Brunswick and Lüneburg*","Bulgaria","Burkina Faso (Upper Volta)","Burma","Burundi","Cabo Verde","Cambodia",
    "Cameroon","Canada","Cayman Islands, The","Central African Republic","Central American Federation*","Chad","Chile",
    "China","Colombia","Comoros","Congo Free State, The*","Cook Islands","Costa Rica","Cote d’Ivoire (Ivory Coast)",
    "Croatia","Cuba","Cyprus","Czechia","Czechoslovakia*","Democratic Republic of the Congo","Denmark","Djibouti",
    "Dominica","Dominican Republic","Duchy of Parma, The*","East Germany (German Democratic Republic)*","Ecuador",
    "Egypt","El Salvador","Equatorial Guinea","Eritrea","Estonia","Eswatini","Ethiopia",
    "Federal Government of Germany (1848-49)*","Fiji","Finland","France","Gabon","Gambia, The","Georgia","Germany",
    "Ghana","Grand Duchy of Tuscany, The*","Greece","Grenada","Guatemala","Guinea","Guinea-Bissau","Guyana","Haiti",
    "Hanover*","Hanseatic Republics*","Hawaii*","Hesse*","Holy See","Honduras","Hungary","Iceland","India","Indonesia",
    "Iran","Iraq","Ireland","Israel","Italy","Jamaica","Japan","Jordan","Kazakhstan","Kenya",
    "Kingdom of Serbia/Yugoslavia*","Kiribati","Korea","Kosovo","Kuwait","Kyrgyzstan","Laos","Latvia","Lebanon",
    "Lesotho","Lew Chew (Loochoo)*","Liberia","Libya","Liechtenstein","Lithuania","Luxembourg","Madagascar","Malawi",
    "Malaysia","Maldives","Mali","Malta","Marshall Islands","Mauritania","Mauritius","Mecklenburg-Schwerin*",
    "Mecklenburg-Strelitz*","Mexico","Micronesia","Moldova","Monaco","Mongolia","Montenegro","Morocco","Mozambique",
    "Namibia","Nassau*","Nauru","Nepal","Netherlands, The","New Zealand","Nicaragua","Niger","Nigeria","Niue",
    "North German Confederation*","North German Union*","North Macedonia","Norway","Oldenburg*","Oman",
    "Orange Free State*","Pakistan","Palau","Panama","Papal States*","Papua New Guinea","Paraguay","Peru","Philippines",
    "Piedmont-Sardinia*","Poland","Portugal","Qatar","Republic of Genoa*","Republic of Korea (South Korea)",
    "Republic of the Congo","Romania","Russia","Rwanda","Saint Kitts and Nevis","Saint Lucia",
    "Saint Vincent and the Grenadines","Samoa","San Marino","Sao Tome and Principe","Saudi Arabia","Schaumburg-Lippe*",
    "Senegal","Serbia","Seychelles","Sierra Leone","Singapore","Slovakia","Slovenia","Solomon Islands, The","Somalia",
    "South Africa","South Sudan","Spain","Sri Lanka","Sudan","Suriname","Sweden","Switzerland","Syria","Taiwan",
    "Tajikistan","Tanzania","Texas*","Thailand","Timor-Leste","Togo","Tonga","Trinidad and Tobago","Tunisia","Turkey",
    "Turkmenistan","Tuvalu","Two Sicilies*","Uganda","Ukraine","Union of Soviet Socialist Republics*",
    "United Arab Emirates, The","United Kingdom, The","Uruguay","Uzbekistan","Vanuatu","Venezuela","Vietnam",
    "Württemberg*","Yemen","Zambia","Zimbabwe"
]
PROGRAMS = ["BSC", "MSC", "PHD", "MPHIL"]

FACULTIES = [
    "Faculty of Informatics","Faculty of Sciences","Faculty of Humanities","Faculty of Law","Faculty of Sports",
    "Faculty of Engineering","Faculty of Agriculture","Faculty of Social Sciences","Faculty of Medicine"
]




@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = UserModel.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        flash("Invalid username or password!", "error")

    return render_template("login.html")



@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/add", methods=["GET", "POST"])
def add_student():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        country = request.form.get('country')
        year = request.form.get('year', '')
        program = request.form.get('program')
        subject = request.form.get('subject')

        if not re.match("^[A-Za-z ]+$", name):
            flash("Name must contain only letters and spaces.", "error")
             

        elif not re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]+$", code):
              flash("Student code must contain both letters and numbers (alphanumeric).", "error")

        elif StudentModel.query.filter_by(code=code).first():
            flash("A student with this code already exists!", "error")
        elif not country:
            flash("Country must be selected.", "error")
        elif not (year.isdigit() and 1975 <= int(year) <= 2025):
            flash("Year must be between 1975 and 2025.", "error")
        elif program not in PROGRAMS:
            flash("Invalid program selected.", "error")
        elif subject not in FACULTIES:
            flash("Invalid subject selected.", "error")
        else:
            student = StudentModel(
                name=name, code=code, country=country, year=int(year),
                program=program, subject=subject
            )
            db.session.add(student)
            db.session.commit()
            flash("Student added successfully!", "success")
            return redirect(url_for("add_student"))

    return render_template("add_student.html", countries=COUNTRIES, faculties=FACULTIES)

@app.route("/confirm_delete", methods=["POST"])
def confirm_delete():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    code = request.form.get("code", "").strip()
    student = StudentModel.query.filter(
        db.func.lower(StudentModel.code) == code.lower()
    ).first()

    if not student:
        flash("Student not found!", "error")
        return redirect(url_for("delete_student"))

    return render_template("confirm_delete.html", student=student)

@app.route("/delete_confirmed", methods=["POST"])
def delete_confirmed():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    code = request.form.get("code", "").strip()
    student = StudentModel.query.filter(
        db.func.lower(StudentModel.code) == code.lower()
    ).first()

    if not student:
        flash("Student not found or could not be deleted.", "error")
        return redirect(url_for("delete_student"))

    db.session.delete(student)
    db.session.commit()
    flash("Student deleted successfully!", "success")
    return redirect(url_for("delete_student"))

@app.route("/update", methods=["GET", "POST"])
def update_student():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    student = None
    if request.method == "POST":
        code = request.form.get("code", "").strip()

        if "name" not in request.form:
            student = StudentModel.query.filter(
                db.func.lower(StudentModel.code) == code.lower()
            ).first()
            if not student:
                flash("Student not found!", "error")

    
        else:
            name = request.form.get("name", "").strip()
            country = request.form.get("country")
            year = request.form.get("year", "")
            program = request.form.get("program")
            subject = request.form.get("subject")

            student = StudentModel.query.filter(
                db.func.lower(StudentModel.code) == code.lower()
            ).first()

            if not student:
                flash("Student not found to update.", "error")
            elif not re.match("^[A-Za-z ]+$", name):
                flash("Name must contain only letters and spaces.", "error")
            elif not country:
                flash("Country must be selected.", "error")
            elif not (year.isdigit() and 1975 <= int(year) <= 2025):
                flash("Year must be between 1975 and 2025.", "error")
            elif program not in PROGRAMS:
                flash("Invalid program selected.", "error")
            elif subject not in FACULTIES:
                flash("Invalid subject selected.", "error")
            else:
                student.name = name
                student.country = country
                student.year = int(year)
                student.program = program
                student.subject = subject
                db.session.commit()
                flash("Student updated successfully!", "success")

    return render_template("update_student.html", student=student,
                           countries=COUNTRIES, faculties=FACULTIES)

@app.route("/delete", methods=["GET", "POST"])
def delete_student():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    student = None
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        action = request.form.get("action")

        if not code:
            flash("Please enter a student code.", "error")
        else:
            student = StudentModel.query.filter(
                db.func.lower(StudentModel.code) == code.lower()
            ).first()

            if action == "search" and not student:
                flash("Student not found!", "error")

    return render_template("delete_student.html", student=student)

@app.route("/view")
def view_students():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    students = StudentModel.query.all()
    return render_template("view_student.html", students=students)

@app.route("/export")
def export_students():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    data = StudentModel.query.order_by(StudentModel.name.asc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Code", "Country", "Year", "Program", "Subject"])
    for s in data:
        writer.writerow([s.name, s.code, s.country, s.year, s.program, s.subject])
    output.seek(0)
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=students.csv"})

@app.route("/statistics")
def view_statistics():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    total = db.session.query(func.count(StudentModel.id)).scalar()

    def agg(col):
        return dict(db.session.query(col, func.count()).group_by(col).all())

    programs = agg(StudentModel.program)
    years = {int(y): c for y, c in db.session.query(StudentModel.year, func.count()).group_by(StudentModel.year).all()}
    countries = agg(StudentModel.country)
    subjects = agg(StudentModel.subject)

    return render_template("view_statistics.html",
                           total=total, programs=programs, years=years,
                           countries=countries, subjects=subjects)



@app.route("/sort", methods=["GET"])
def sort_students():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    sort_by = request.args.get("sort_by")          
    order = request.args.get("order", "asc")       

    q = StudentModel.query
    if sort_by in ("name", "year"):
        col = StudentModel.name if sort_by == "name" else StudentModel.year
        q = q.order_by(col.desc() if order == "desc" else col.asc())

    students = q.all()
    return render_template("sort_students.html", students=students, sort_by=sort_by, order=order)


@app.route("/filter", methods=["GET"])
def filter_students():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    name = request.args.get("name", "").strip()
    code = request.args.get("code", "").strip()
    year = request.args.get("year", "").strip()
    country = request.args.get("country", "")
    program = request.args.get("program", "")

    q = StudentModel.query
    if name:
        q = q.filter(StudentModel.name.ilike(f"%{name}%"))
    if code:
        q = q.filter(StudentModel.code.ilike(f"%{code}%"))
    if year and year.isdigit():
        q = q.filter(StudentModel.year == int(year))
    if country:
        q = q.filter(StudentModel.country == country)
    if program:
        q = q.filter(StudentModel.program == program)

    students = q.all()
    return render_template(
        "filter_students.html",
        students=students,
        programs=PROGRAMS,
        countries=COUNTRIES,
        params={"name": name, "code": code, "year": year, "country": country, "program": program}
    )


@app.route("/export_sort")
def export_sort():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    sort_by = request.args.get("sort_by")
    order = request.args.get("order", "asc")

    q = StudentModel.query
    if sort_by in ("name", "year"):
        col = StudentModel.name if sort_by == "name" else StudentModel.year
        q = q.order_by(col.desc() if order == "desc" else col.asc())

    rows = q.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Code", "Country", "Year", "Program", "Subject"])
    for s in rows:
        writer.writerow([s.name, s.code, s.country, s.year, s.program, s.subject])
    output.seek(0)
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=sorted_students.csv"})



@app.route("/export_filter")
def export_filter():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    name = request.args.get("name", "").strip()
    code = request.args.get("code", "").strip()
    year = request.args.get("year", "").strip()
    country = request.args.get("country", "")
    program = request.args.get("program", "")

    q = StudentModel.query
    if name:
        q = q.filter(StudentModel.name.ilike(f"%{name}%"))
    if code:
        q = q.filter(StudentModel.code.ilike(f"%{code}%"))
    if year and year.isdigit():
        q = q.filter(StudentModel.year == int(year))
    if country:
        q = q.filter(StudentModel.country == country)
    if program:
        q = q.filter(StudentModel.program == program)

    rows = q.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Code", "Country", "Year", "Program", "Subject"])
    for s in rows:
        writer.writerow([s.name, s.code, s.country, s.year, s.program, s.subject])
    output.seek(0)
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=filtered_students.csv"})


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]

        user = UserModel.query.filter_by(username=username, email=email).first()
        if not user:
            flash("No matching user found", "error")
        else:
            token = str(uuid.uuid4())
            user.reset_token = token
            db.session.commit()

            reset_link = url_for("reset_password", token=token, _external=True, _scheme="http")
            msg = Message("Reset Your Password", recipients=[email], body=f"Click to reset: {reset_link}")
            mail.send(msg)

            flash("Reset link sent to your email!", "success")
            return redirect(url_for("login"))

    return render_template("forgot_password.html")



@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = UserModel.query.filter_by(reset_token=token).first()
    if not user:
        flash("Invalid or expired reset token", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        new_pass = request.form["new_password"]
        confirm_pass = request.form["confirm_password"]

        if new_pass != confirm_pass:
            flash("Passwords do not match", "error")
        else:
            user.password = generate_password_hash(new_pass)
            user.reset_token = None
            db.session.commit()
            flash("Password updated successfully!", "success")
            return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)


from collections import Counter 

@app.route("/data_analysis")
def data_analysis():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    rows = StudentModel.query.with_entities(
        StudentModel.country, StudentModel.program, StudentModel.subject, StudentModel.year
    ).all()

    if not rows:
        return render_template(
            "data_analysis.html",
            avg_per_year=0,
            common_country="N/A",
            program_ratios={},
            top_faculties=[]
        )

    countries = [r.country for r in rows]
    programs  = [r.program for r in rows]
    subjects  = [r.subject for r in rows]
    years     = [int(r.year) for r in rows if r.year is not None]

    total = len(rows)
    avg_per_year = round(total / len(set(years)), 2) if years else 0
    common_country = Counter(countries).most_common(1)[0][0] if countries else "N/A"
    prog_counts = Counter(programs)
    program_ratios = {
        p: round((prog_counts.get(p, 0) / total) * 100, 2)
        for p in ["BSC", "MSC", "PHD", "MPHIL"]
    }
    top_faculties = Counter(subjects).most_common(3)

    return render_template(
        "data_analysis.html",
        avg_per_year=avg_per_year,
        common_country=common_country,
        program_ratios=program_ratios,
        top_faculties=top_faculties
    )

# with app.app_context():
#     db.create_all()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
