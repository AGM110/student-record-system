

import io
import csv
import pytest
from werkzeug.security import generate_password_hash



import os
os.environ["SRMS_TESTING"] = "1" 


from app import app as flask_app
from utils.db import db
from utils.models import StudentModel, UserModel






@pytest.fixture(scope="function")
def app():
    """
    Configure a fresh in-memory app + DB for every test function.
    Seeds a single admin user.
    """
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite://",
        MAIL_SUPPRESS_SEND=True,    
        WTF_CSRF_ENABLED=False,
        SERVER_NAME="localhost",     
    )
    # with flask_app.app_context():
    #     db.drop_all()
    #     db.create_all()


    
    with flask_app.app_context():
        url = str(db.engine.url)
        dbname = db.engine.url.database
        assert url.startswith("sqlite://") and dbname in (None, "", ":memory:"), \
            f"Refusing to run tests on real DB: {url}"

        db.drop_all()
        db.create_all()


        admin = UserModel(
            username="admin",
            email="admin@example.com",
            password=generate_password_hash("secret123"),
        )
        db.session.add(admin)
        db.session.commit()

    yield flask_app

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Flask test client bound to the test app."""
    return app.test_client()


def login_as(client, username="admin", password="secret123"):
    """Helper: log in and follow redirects to the dashboard."""
    return client.post(
        "/", data={"username": username, "password": password}, follow_redirects=True
    )


def create_student(
    name="Alice Smith",
    code="S001",
    country="Hungary",
    year=2024,
    program="BSC",
    subject="Faculty of Informatics",
):
    """Helper: create and commit a StudentModel row."""
    student = StudentModel(
        name=name,
        code=code,
        country=country,
        year=year,
        program=program,
        subject=subject,
    )
    db.session.add(student)
    db.session.commit()
    return student



def test_login_success(client, app):
    response = login_as(client)
    assert response.status_code == 200
    assert b"ADMIN DASHBOARD" in response.data


def test_login_failure(client):
    response = client.post("/", data={"username": "admin", "password": "wrong"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_auth_required_redirect(client):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code in (301, 302)
    assert response.headers["Location"].endswith("/")



def test_add_student_validation_name(client, app):
    login_as(client)
    payload = {
        "name": "Bob123",
        "code": "C100",
        "country": "Hungary",
        "year": "2024",
        "program": "BSC",
        "subject": "Faculty of Informatics",
    }
    response = client.post("/add", data=payload, follow_redirects=True)
    assert b"Name must contain only letters and spaces" in response.data


def test_add_student_success(client, app):
    """Accept and persist a valid student."""
    login_as(client)
    payload = {
        "name": "Bob Marley",
        "code": "C101",
        "country": "Hungary",
        "year": "2024",
        "program": "BSC",
        "subject": "Faculty of Informatics",
    }
    response = client.post("/add", data=payload, follow_redirects=True)
    assert b"Student added successfully" in response.data

    with app.app_context():
        student = StudentModel.query.filter_by(code="C101").first()
        assert student is not None
        assert student.name == "Bob Marley"



def test_view_students_listed(client, app):
    """View page shows created students."""
    login_as(client)
    with app.app_context():
        create_student(name="Alice", code="A1")
        create_student(name="Ben", code="B2")

    response = client.get("/view")
    assert response.status_code == 200
    assert b"Alice" in response.data and b"Ben" in response.data


def test_update_student_success(client, app):
    """Update an existing student and verify persisted values."""
    login_as(client)
    with app.app_context():
        create_student(
            name="Carol", code="C200", country="Hungary", year=2024,
            program="BSC", subject="Faculty of Informatics"
        )

    search_response = client.post("/update", data={"code": "C200"}, follow_redirects=True)
    assert search_response.status_code == 200
    assert b"UPDATE STUDENT" in search_response.data

    update_payload = {
        "code": "C200",
        "name": "Carol Updated",
        "country": "Hungary",
        "year": "2024",
        "program": "MSC",
        "subject": "Faculty of Sciences",
    }
    update_response = client.post("/update", data=update_payload, follow_redirects=True)
    assert b"Student updated successfully" in update_response.data

    with app.app_context():
        student = StudentModel.query.filter_by(code="C200").first()
        assert student.name == "Carol Updated"
        assert student.program == "MSC"
        assert student.subject == "Faculty of Sciences"




def test_delete_student_flow(client, app):
    """Delete flow: search → confirm → delete."""
    login_as(client)
    with app.app_context():
        create_student(name="Dan", code="D300")

  
    response = client.post("/delete", data={"code": "D300", "action": "search"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Delete Student" in response.data or b"DELETE STUDENT" in response.data

    confirm = client.post("/confirm_delete", data={"code": "D300"}, follow_redirects=True)
    assert b"Are you sure you want to delete" in confirm.data

    final = client.post("/delete_confirmed", data={"code": "D300"}, follow_redirects=True)
    assert b"Student deleted successfully" in final.data

    with app.app_context():
        assert StudentModel.query.filter_by(code="D300").first() is None

def test_export_students_csv_headers(client, app):
    """CSV export returns correct headers and mimetype."""
    login_as(client)
    with app.app_context():
        create_student(name="Eva", code="E1")
    response = client.get("/export")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"

    csv_text = response.data.decode()
    header = next(csv.reader(io.StringIO(csv_text)))
    assert header == ["Name", "Code", "Country", "Year", "Program", "Subject"]

def test_statistics_page_renders_and_counts(client, app):
    """Statistics page renders and shows a total count label."""
    login_as(client)
    with app.app_context():
        create_student(name="Fay", code="F1", program="BSC")
        create_student(name="Gus", code="G1", program="MSC")

    response = client.get("/statistics")
    assert response.status_code == 200
    assert b"Total Students" in response.data


def test_sort_students_by_name_asc(client, app):
    """Sorting by name ascending places A before Z."""
    login_as(client)
    with app.app_context():
        create_student(name="Zed", code="Z9")
        create_student(name="Amy", code="A0")

    response = client.get("/sort?sort_by=name&order=asc")
    assert response.status_code == 200

    html = response.data.decode()
    assert html.index("Amy") < html.index("Zed")


def test_filter_students_by_program(client, app):
    """Filter by program=MSC hides non-MSC rows."""
    login_as(client)
    with app.app_context():
        create_student(name="Ivy", code="I1", program="MSC")
        create_student(name="Jay", code="J2", program="BSC")

    response = client.get("/filter?program=MSC")
    html = response.data.decode()
    assert "Ivy" in html and "Jay" not in html


def test_forgot_password_generates_token_and_email_suppressed(client, app):
    """Forgot password creates a token and (suppressed) email send."""
    response = client.post(
        "/forgot_password",
        data={"username": "admin", "email": "admin@example.com"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Reset link sent to your email" in response.data

    with app.app_context():
        user = UserModel.query.filter_by(username="admin").first()
        assert user.reset_token is not None


def test_reset_password_success(client, app):
    """Successful password reset clears the token."""
    with app.app_context():
        user = UserModel.query.filter_by(username="admin").first()
        user.reset_token = "tok123"
        db.session.commit()

    form = client.get("/reset_password/tok123")
    assert form.status_code == 200


    response = client.post(
        "/reset_password/tok123",
        data={"new_password": "NewP@ssw0rd", "confirm_password": "NewP@ssw0rd"},
        follow_redirects=True,
    )
    assert b"Password updated successfully" in response.data

    with app.app_context():
        user = UserModel.query.filter_by(username="admin").first()
        assert user.reset_token is None


def test_validation_year_bounds(client, app):
    """Reject year below lower bound."""
    login_as(client)
    payload = {
        "name": "Kim Possible",
        "code": "K100",
        "country": "Hungary",
        "year": "1974",  
        "program": "BSC",
        "subject": "Faculty of Informatics",
    }
    response = client.post("/add", data=payload, follow_redirects=True)
    assert b"Year must be between 1975 and 2025" in response.data


def test_html_escaping_in_view(client, app):
    """Ensure potentially dangerous names are escaped in the table."""
    login_as(client)
    malicious = "<script>alert(1)</script>"
    with app.app_context():
        create_student(name=malicious, code="XSS1")

    response = client.get("/view")
    assert response.status_code == 200
    html = response.data.decode()
    assert malicious not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html



def test_add_student_invalid_code_non_alnum(client, app):
    """Reject student codes containing non-alphanumeric chars."""
    login_as(client)
    payload = {
        "name": "Valid Name",
        "code": "ABC-123", 
        "country": "Hungary",
        "year": "2024",
        "program": "BSC",
        "subject": "Faculty of Informatics",
    }
    response = client.post("/add", data=payload, follow_redirects=True)
    assert b"Student code must contain both letters and numbers" in response.data



def test_add_student_duplicate_code_rejected(client, app):
    """Reject duplicate student code."""
    login_as(client)
    with app.app_context():
        create_student(name="First", code="DUP1")

    payload = {
        "name": "Second",
        "code": "DUP1",  
        "country": "Hungary",
        "year": "2024",
        "program": "BSC",
        "subject": "Faculty of Informatics",
    }
    response = client.post("/add", data=payload, follow_redirects=True)
    assert b"A student with this code already exists" in response.data


def test_add_student_invalid_program_and_subject(client, app):
    """Reject invalid program and invalid subject choices."""
    login_as(client)

    bad_program = {
        "name": "Adam Alpha",
        "code": "P999",
        "country": "Hungary",
        "year": "2024",
        "program": "MBA",  
        "subject": "Faculty of Informatics",
    }
    r1 = client.post("/add", data=bad_program, follow_redirects=True)
    assert b"Invalid program selected" in r1.data

    bad_subject = {
        "name": "Beta Bravo",
        "code": "S999",
        "country": "Hungary",
        "year": "2024",
        "program": "BSC",
        "subject": "Unknown Faculty", 
    }
    r2 = client.post("/add", data=bad_subject, follow_redirects=True)
    assert b"Invalid subject selected" in r2.data


def test_add_student_year_upper_bound(client, app):
    """Reject year above upper bound."""
    login_as(client)
    payload = {
        "name": "Upper Bound",
        "code": "Y2026",
        "country": "Hungary",
        "year": "2026",  
        "program": "BSC",
        "subject": "Faculty of Informatics",
    }
    response = client.post("/add", data=payload, follow_redirects=True)
    assert b"Year must be between 1975 and 2025" in response.data


def test_update_student_validation_rejects_bad_name(client, app):
    """Update should reject invalid names."""
    login_as(client)
    with app.app_context():
        create_student(name="Clean Name", code="UP100", program="BSC", subject="Faculty of Informatics")

    client.post("/update", data={"code": "UP100"}, follow_redirects=True)

 
    bad_update = {
        "code": "UP100",
        "name": "Dirty123",
        "country": "Hungary",
        "year": "2024",
        "program": "MSC",
        "subject": "Faculty of Sciences",
    }
    response = client.post("/update", data=bad_update, follow_redirects=True)
    assert b"Name must contain only letters and spaces" in response.data


def test_delete_nonexistent_student_messages(client, app):
    """Deleting a non-existent student shows user-friendly messages."""
    login_as(client)

    not_found_search = client.post("/delete", data={"code": "NOPE", "action": "search"}, follow_redirects=True)
    assert b"Student not found" in not_found_search.data

    not_found_delete = client.post("/delete_confirmed", data={"code": "NOPE"}, follow_redirects=True)
    assert b"Student not found or could not be deleted" in not_found_delete.data

def test_export_filter_csv_contains_only_filtered_rows(client, app):
    """Exported filtered CSV should only include rows that match the filter."""
    login_as(client)
    with app.app_context():
        create_student(name="MSC One", code="M1", program="MSC")
        create_student(name="BSC One", code="B1", program="BSC")

    response = client.get("/export_filter?program=MSC")
    assert response.status_code == 200

    csv_text = response.data.decode()
    rows = list(csv.reader(io.StringIO(csv_text)))
    assert rows[0] == ["Name", "Code", "Country", "Year", "Program", "Subject"]

    data_rows = rows[1:]
    assert len(data_rows) == 1
    first_row = data_rows[0]
    assert first_row[0] == "MSC One"
    assert first_row[4] == "MSC"  


def test_export_sort_csv_sorted_by_year_desc(client, app):
    """Sorted export by year (desc) should list newest first."""
    login_as(client)
    with app.app_context():
        create_student(name="Old", code="Y1", year=2000)
        create_student(name="New", code="Y2", year=2024)

    response = client.get("/export_sort?sort_by=year&order=desc")
    assert response.status_code == 200

    lines = response.data.decode().splitlines()
    assert lines[1].startswith("New,")
    assert lines[2].startswith("Old,")


def test_statistics_exact_group_counts(client, app):
    """Statistics page should reflect groups that exist in DB."""
    login_as(client)
    with app.app_context():
        create_student(name="S1", code="ST1", program="BSC", country="Hungary", subject="Faculty of Informatics", year=2024)
        create_student(name="S2", code="ST2", program="MSC", country="Germany", subject="Faculty of Sciences", year=2023)
        create_student(name="S3", code="ST3", program="BSC", country="Hungary", subject="Faculty of Informatics", year=2022)

    response = client.get("/statistics")
    html = response.data.decode()
    assert "Total Students" in html
    assert "BSC" in html and "MSC" in html
    assert "Hungary" in html and "Germany" in html


def test_data_analysis_metrics_rendered(client, app):
    """Data analysis page shows expected metric sections."""
    login_as(client)
    with app.app_context():
        create_student(name="A", code="DA1", year=2024, program="BSC", country="Hungary", subject="Faculty of Informatics")
        create_student(name="B", code="DA2", year=2024, program="MSC", country="Hungary", subject="Faculty of Informatics")
        create_student(name="C", code="DA3", year=2023, program="PHD", country="Germany", subject="Faculty of Sciences")

    response = client.get("/data_analysis")
    html = response.data.decode()
    assert "Average Students/Year" in html
    assert "Most Common Country" in html
    assert "Program Ratios" in html
    assert "Top Faculties" in html


def test_filter_multiple_criteria_year_and_country(client, app):
    """Filter: combine year and country; only exact matches remain."""
    login_as(client)
    with app.app_context():
        create_student(name="YYH", code="C1", year=2024, country="Hungary", program="BSC", subject="Faculty of Informatics")
        create_student(name="YYG", code="C2", year=2024, country="Germany", program="BSC", subject="Faculty of Informatics")
        create_student(name="OLH", code="C3", year=2023, country="Hungary", program="BSC", subject="Faculty of Informatics")

    response = client.get("/filter?year=2024&country=Hungary")
    html = response.data.decode()
    assert "YYH" in html
    assert "YYG" not in html
    assert "OLH" not in html


def test_logout_clears_session_and_blocks_dashboard(client, app):
    """Logout should clear session and block subsequent dashboard access."""
    login_as(client)
    ok = client.get("/dashboard")
    assert ok.status_code == 200

    client.get("/logout", follow_redirects=True)

    blocked = client.get("/dashboard", follow_redirects=False)
    assert blocked.status_code in (301, 302)
    assert blocked.headers["Location"].endswith("/")


def test_reset_password_mismatch_shows_error(client, app):
    """Mismatched passwords on reset show a helpful error."""
    with app.app_context():
        user = UserModel.query.filter_by(username="admin").first()
        user.reset_token = "tok-mismatch"
        db.session.commit()

    response = client.post(
        "/reset_password/tok-mismatch",
        data={"new_password": "A1b2c3!", "confirm_password": "DIFFERENT"},
        follow_redirects=True,
    )
    assert b"Passwords do not match" in response.data


def test_filter_by_partial_name_case_insensitive(client, app):
    """Filtering by name should be partial and case-insensitive (ILIKE)."""
    login_as(client)
    with app.app_context():
        create_student(name="Alice Smith", code="N1", program="BSC", country="Hungary", subject="Faculty of Informatics", year=2024)
        create_student(name="ALI Johnson", code="N2", program="MSC", country="Germany", subject="Faculty of Sciences", year=2023)
        create_student(name="Bob Brown", code="N3", program="BSC", country="Hungary", subject="Faculty of Informatics", year=2022)

    response = client.get("/filter?name=ali")
    html = response.data.decode()
    assert "Alice Smith" in html
    assert "ALI Johnson" in html
    assert "Bob Brown" not in html
