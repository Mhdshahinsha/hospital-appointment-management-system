from flask import Flask, render_template, request, redirect, url_for, session
from db import get_connection

app = Flask(__name__)

app.secret_key = "hospital_secret_key_2026"

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT *
            FROM users
            WHERE email=%s
            AND password=%s
        """, (email, password))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:

            session["user_id"] = user[0]
            session["full_name"] = user[1]
            session["email"] = user[2]
            session["role"] = user[5]

            if session["role"] == "Admin":
                return redirect(url_for("admin_dashboard"))

            elif session["role"] == "Doctor":
                return redirect(url_for("doctor_dashboard"))

            else:
                return redirect(url_for("patient_dashboard"))

        else:

            return render_template(
                "login.html",
                error="Invalid Email or Password"
            )

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        role = request.form["role"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        existing_user = cur.fetchone()

        if existing_user:

            cur.close()
            conn.close()

            return render_template(
                "register.html",
                error="Email already exists."
            )

        cur.execute("""
            INSERT INTO users
            (
                full_name,
                email,
                phone,
                password,
                role
            )

            VALUES
            (%s,%s,%s,%s,%s)

        """,
        (
            full_name,
            email,
            phone,
            password,
            role
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/forgot-password")
def forgot_password():

    return render_template("forget_password.html")


@app.route("/admin")
def admin_dashboard():

    if "user_id" not in session:

        return redirect(url_for("login"))

    if session["role"] != "Admin":

        return redirect(url_for("login"))

    return render_template(
        "admin_dashboard.html",
        name=session["full_name"]
    )

@app.route("/doctors")
def doctors():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""

        SELECT *

        FROM doctors

        ORDER BY doctor_id

    """)

    doctors = cur.fetchall()

    cur.close()

    conn.close()

    return render_template(

        "doctors.html",

        doctors=doctors

    )

@app.route("/doctor")
def doctor_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Doctor":
        return redirect(url_for("login"))

    return render_template("doctor_dashboard.html")

@app.route("/add_doctor", methods=["GET", "POST"])
def add_doctor():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    if request.method == "POST":

        doctor_name = request.form["doctor_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        gender = request.form["gender"]
        department = request.form["department"]
        specialization = request.form["specialization"]
        qualification = request.form["qualification"]
        experience = request.form["experience"]
        consultation_fee = request.form["consultation_fee"]
        available_days = request.form["available_days"]
        available_time = request.form["available_time"]
        status = request.form["status"]

        conn = get_connection()
        cur = conn.cursor()

        # Check whether email already exists
        cur.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        if cur.fetchone():

            cur.close()
            conn.close()

            return render_template(
                "add_doctor.html",
                error="Email already exists."
            )

        # Insert into users table
        cur.execute(
            """
            INSERT INTO users
            (
                full_name,
                email,
                phone,
                password,
                role
            )

            VALUES
            (%s,%s,%s,%s,%s)
            """,
            (
                doctor_name,
                email,
                phone,
                password,
                "Doctor"
            )
        )

        # Insert into doctors table
        cur.execute(
            """
            INSERT INTO doctors
            (
                doctor_name,
                email,
                phone,
                gender,
                department,
                specialization,
                qualification,
                experience,
                consultation_fee,
                available_days,
                available_time,
                status
            )

            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                doctor_name,
                email,
                phone,
                gender,
                department,
                specialization,
                qualification,
                experience,
                consultation_fee,
                available_days,
                available_time,
                status
            )
        )

        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("doctors"))

    return render_template("add_doctor.html")

@app.route("/patient")
def patient_dashboard():

    if "user_id" not in session:

        return redirect(url_for("login"))

    if session["role"] != "Patient":


        return redirect(url_for("login"))

    return render_template(
        "patient_dashboard.html",
        name=session["full_name"]
    )

@app.route("/patients")
def patients():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM users
        WHERE role='Patient'
        ORDER BY user_id
    """)

    patients = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "patients.html",
        patients=patients
    )

@app.route("/appointments")
def appointments():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("appointments.html")


@app.route("/bills")
def bills():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("bills.html")

 
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

if __name__ == "__main__":

    app.run(debug=True)
