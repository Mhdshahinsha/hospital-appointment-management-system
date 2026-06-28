from datetime import datetime
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

            # Store patient_id in session
            if session["role"] == "Patient":

                conn = get_connection()
                cur = conn.cursor()

                cur.execute("""
                    SELECT patient_id
                    FROM patients
                    WHERE email=%s
                """, (session["email"],))

                patient = cur.fetchone()

                if patient:
                    session["patient_id"] = patient[0]

                cur.close()
                conn.close()

            # Redirect according to role
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

    return render_template("register.html")


@app.route("/forgot-password")
def forgot_password():

    return render_template("forget_password.html")


@app.route("/admin")
def admin_dashboard():

    # Check Login
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only Admin
    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    # -------------------------
    # Total Doctors
    # -------------------------

    cur.execute("""
        SELECT COUNT(*)
        FROM doctors
    """)
    doctor_count = cur.fetchone()[0]

    # -------------------------
    # Total Patients
    # -------------------------

    cur.execute("""
        SELECT COUNT(*)
        FROM patients
    """)
    patient_count = cur.fetchone()[0]

    # -------------------------
    # Total Appointments
    # -------------------------

    cur.execute("""
        SELECT COUNT(*)
        FROM appointments
    """)
    appointment_count = cur.fetchone()[0]

    # -------------------------
    # Total Revenue
    # (Temporary)
    # -------------------------

    total_revenue = 0

    # -------------------------
    # Recent Appointments
    # -------------------------

    cur.execute("""
        SELECT
            p.full_name,
            d.doctor_name,
            a.appointment_date,
            a.appointment_time,
            a.status

        FROM appointments a

        JOIN patients p
            ON a.patient_id = p.patient_id

        JOIN doctors d
            ON a.doctor_id = d.doctor_id

        ORDER BY
            a.created_at DESC

        LIMIT 5
    """)

    recent_appointments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "admin_dashboard.html",

        name=session["full_name"],

        doctor_count=doctor_count,

        patient_count=patient_count,

        appointment_count=appointment_count,

        total_revenue=total_revenue,

        recent_appointments=recent_appointments
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
        available_days = ",".join(
        request.form.getlist("available_days")
        )

        start_time = request.form["start_time"]

        end_time = request.form["end_time"]

        available_time = f"{start_time}-{end_time}"    
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

@app.route("/edit_doctor/<int:doctor_id>", methods=["GET", "POST"])
def edit_doctor(doctor_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        doctor_name = request.form["doctor_name"]
        phone = request.form["phone"]
        gender = request.form["gender"]
        department = request.form["department"]
        specialization = request.form["specialization"]
        qualification = request.form["qualification"]
        experience = request.form["experience"]
        consultation_fee = request.form["consultation_fee"]
        available_days = ",".join(
    	request.form.getlist("available_days")
	)

        start_time = request.form["start_time"]
        end_time = request.form["end_time"]

        available_time = f"{start_time}-{end_time}"
        status = request.form["status"]

        # Get doctor's email
        cur.execute(
            "SELECT email FROM doctors WHERE doctor_id=%s",
            (doctor_id,)
        )

        email = cur.fetchone()[0]

        # Update doctors table
        cur.execute("""
            UPDATE doctors
            SET
                doctor_name=%s,
                phone=%s,
                gender=%s,
                department=%s,
                specialization=%s,
                qualification=%s,
                experience=%s,
                consultation_fee=%s,
                available_days=%s,
                available_time=%s,
                status=%s
            WHERE doctor_id=%s
        """,
        (
            doctor_name,
            phone,
            gender,
            department,
            specialization,
            qualification,
            experience,
            consultation_fee,
            available_days,
            available_time,
            status,
            doctor_id
        ))

        # Update users table
        cur.execute("""
            UPDATE users
            SET
                full_name=%s,
                phone=%s
            WHERE email=%s
        """,
        (
            doctor_name,
            phone,
            email
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("doctors"))

    cur.execute(
        "SELECT * FROM doctors WHERE doctor_id=%s",
        (doctor_id,)
    )

    doctor = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "edit_doctor.html",
        doctor=doctor
    )

@app.route("/delete_doctor/<int:doctor_id>")
def delete_doctor(doctor_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    # Get doctor's email
    cur.execute(
        "SELECT email FROM doctors WHERE doctor_id=%s",
        (doctor_id,)
    )

    doctor = cur.fetchone()

    if doctor:

        email = doctor[0]

        # Delete from doctors table
        cur.execute(
            "DELETE FROM doctors WHERE doctor_id=%s",
            (doctor_id,)
        )

        # Delete login account
        cur.execute(
            "DELETE FROM users WHERE email=%s",
            (email,)
        )

        conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("doctors"))

@app.route("/patient")
def patient_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Patient":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    patient_id = session["patient_id"]

    # Total Appointments
    cur.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE patient_id=%s
    """, (patient_id,))
    appointment_count = cur.fetchone()[0]

    # Upcoming Visits
    cur.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE patient_id=%s
        AND appointment_date >= CURRENT_DATE
    """, (patient_id,))
    upcoming_visits = cur.fetchone()[0]

    # Recent Appointments
    cur.execute("""
        SELECT
            d.doctor_name,
            a.appointment_date,
            a.appointment_time,
            a.status

        FROM appointments a

        JOIN doctors d
        ON a.doctor_id = d.doctor_id

        WHERE a.patient_id=%s

        ORDER BY
            a.appointment_date DESC,
            a.appointment_time DESC

        LIMIT 5
    """, (patient_id,))

    appointments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "patient_dashboard.html",
        appointment_count=appointment_count,
        upcoming_visits=upcoming_visits,
        appointments=appointments
    )


@app.route("/patients")
def patients():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    search = request.args.get("search", "")

    conn = get_connection()
    cur = conn.cursor()

    if search:

        cur.execute("""
            SELECT *
            FROM patients
            WHERE
                full_name ILIKE %s OR
                email ILIKE %s OR
                phone ILIKE %s
            ORDER BY patient_id
        """,
        (
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        ))

    else:

        cur.execute("""
            SELECT *
            FROM patients
            ORDER BY patient_id
        """)

    patients = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "patients.html",
        patients=patients
    )


@app.route("/add_patient", methods=["GET", "POST"])
def add_patient():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        age = request.form["age"]
        gender = request.form["gender"]
        address = request.form["address"]

        conn = get_connection()
        cur = conn.cursor()

        # Check duplicate email
        cur.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        if cur.fetchone():

            cur.close()
            conn.close()

            return render_template(
                "add_patients.html",
                error="Email already exists."
            )

        # Insert login account
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
            "Patient"
        ))

        # Insert patient details
        cur.execute("""
            INSERT INTO patients
            (
                full_name,
                age,
                gender,
                email,
                phone,
                address
            )

            VALUES
            (%s,%s,%s,%s,%s,%s)
        """,
        (
            full_name,
            age,
            gender,
            email,
            phone,
            address
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("patients"))

    return render_template("add_patients.html")

@app.route("/edit_patient/<int:patient_id>", methods=["GET", "POST"])
def edit_patient(patient_id):

    # Check Login
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only Admin can edit
    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    # --------------------------
    # UPDATE PATIENT
    # --------------------------

    if request.method == "POST":

        full_name = request.form["full_name"]
        age = request.form["age"]
        gender = request.form["gender"]
        phone = request.form["phone"]
        address = request.form["address"]

        # Get Email from Patients table
        cur.execute(
            "SELECT email FROM patients WHERE patient_id=%s",
            (patient_id,)
        )

        patient = cur.fetchone()

        if patient is None:

            cur.close()
            conn.close()

            return redirect(url_for("patients"))

        email = patient[0]

        # Update Patients Table
        cur.execute("""
            UPDATE patients
            SET
                full_name=%s,
                age=%s,
                gender=%s,
                phone=%s,
                address=%s
            WHERE patient_id=%s
        """,
        (
            full_name,
            age,
            gender,
            phone,
            address,
            patient_id
        ))

        # Update Users Table
        cur.execute("""
            UPDATE users
            SET
                full_name=%s,
                phone=%s
            WHERE email=%s
        """,
        (
            full_name,
            phone,
            email
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("patients"))

    # --------------------------
    # LOAD PATIENT DETAILS
    # --------------------------

    cur.execute(
        "SELECT * FROM patients WHERE patient_id=%s",
        (patient_id,)
    )

    patient = cur.fetchone()

    cur.close()
    conn.close()

    if patient is None:
        return redirect(url_for("patients"))

    return render_template(
        "edit_patients.html",
        patient=patient
    )

@app.route("/delete_patient/<int:patient_id>")
def delete_patient(patient_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    # Get patient's email
    cur.execute(
        "SELECT email FROM patients WHERE patient_id=%s",
        (patient_id,)
    )

    patient = cur.fetchone()

    if patient:

        email = patient[0]

        # Delete from patients table
        cur.execute(
            "DELETE FROM patients WHERE patient_id=%s",
            (patient_id,)
        )

        # Delete login account
        cur.execute(
            "DELETE FROM users WHERE email=%s",
            (email,)
        )

        conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("patients"))


@app.route("/appointments")
def appointments():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.appointment_id,
            p.full_name,
            d.doctor_name,
            a.appointment_date,
            a.appointment_time,
            a.reason,
            a.status

        FROM appointments a

        JOIN patients p
            ON a.patient_id = p.patient_id

        JOIN doctors d
            ON a.doctor_id = d.doctor_id

        ORDER BY a.appointment_date,
                 a.appointment_time
    """)

    appointments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "appointments.html",
        appointments=appointments
    )

@app.route("/add_appointment", methods=["GET", "POST"])
def add_appointment():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    # Load Patients
    cur.execute("""
        SELECT patient_id, full_name
        FROM patients
        ORDER BY full_name
    """)
    patients = cur.fetchall()

    # Load Doctors
    cur.execute("""
        SELECT doctor_id, doctor_name
        FROM doctors
        ORDER BY doctor_name
    """)
    doctors = cur.fetchall()

    if request.method == "POST":

        patient_id = request.form["patient_id"]
        doctor_id = request.form["doctor_id"]
        appointment_date = request.form["appointment_date"]
        appointment_time = request.form["appointment_time"]
        reason = request.form["reason"]
        status = request.form["status"]

        # ---------------------------------
        # Get Doctor Availability
        # ---------------------------------

        cur.execute("""
            SELECT
                available_days,
                available_time
            FROM doctors
            WHERE doctor_id=%s
        """, (doctor_id,))

        doctor = cur.fetchone()

        if doctor is None:

            cur.close()
            conn.close()

            return render_template(
                "add_appointment.html",
                patients=patients,
                doctors=doctors,
                error="Doctor not found."
            )

        available_days = doctor[0]
        available_time = doctor[1]

        # ---------------------------------
        # Check Doctor Working Day
        # ---------------------------------

        appointment_day = datetime.strptime(
            appointment_date,
            "%Y-%m-%d"
        ).strftime("%A")

        days_list = [
            day.strip()
            for day in available_days.split(",")
        ]

        if appointment_day not in days_list:

            cur.close()
            conn.close()

            return render_template(
                "add_appointment.html",
                patients=patients,
                doctors=doctors,
                error=f"Doctor is not available on {appointment_day}."
            )

        # ---------------------------------
        # Check Doctor Working Time
        # ---------------------------------

        start_time, end_time = available_time.split("-")

        if appointment_time < start_time or appointment_time > end_time:

            cur.close()
            conn.close()

            return render_template(
                "add_appointment.html",
                patients=patients,
                doctors=doctors,
                error=f"Doctor is available only between {start_time} and {end_time}."
            )

        # ---------------------------------
        # Check Duplicate Appointment
        # ---------------------------------

        cur.execute("""
            SELECT appointment_id
            FROM appointments
            WHERE doctor_id=%s
            AND appointment_date=%s
            AND appointment_time=%s
        """,
        (
            doctor_id,
            appointment_date,
            appointment_time
        ))

        existing = cur.fetchone()

        if existing:

            cur.close()
            conn.close()

            return render_template(
                "add_appointment.html",
                patients=patients,
                doctors=doctors,
                error="This doctor already has an appointment at the selected date and time."
            )

        # ---------------------------------
        # Insert Appointment
        # ---------------------------------

        cur.execute("""
            INSERT INTO appointments
            (
                patient_id,
                doctor_id,
                appointment_date,
                appointment_time,
                reason,
                status
            )
            VALUES
            (%s,%s,%s,%s,%s,%s)
        """,
        (
            patient_id,
            doctor_id,
            appointment_date,
            appointment_time,
            reason,
            status
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("appointments"))

    cur.close()
    conn.close()

    return render_template(
        "add_appointment.html",
        patients=patients,
        doctors=doctors
    )


@app.route("/edit_appointment/<int:appointment_id>", methods=["GET", "POST"])
def edit_appointment(appointment_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    # Load Patients
    cur.execute("""
        SELECT patient_id, full_name
        FROM patients
        ORDER BY full_name
    """)
    patients = cur.fetchall()

    # Load Doctors
    cur.execute("""
        SELECT doctor_id, doctor_name
        FROM doctors
        ORDER BY doctor_name
    """)
    doctors = cur.fetchall()

    # Load Current Appointment
    cur.execute("""
        SELECT *
        FROM appointments
        WHERE appointment_id=%s
    """, (appointment_id,))

    appointment = cur.fetchone()

    if not appointment:
        cur.close()
        conn.close()
        return redirect(url_for("appointments"))

    if request.method == "POST":

        patient_id = request.form["patient_id"]
        doctor_id = request.form["doctor_id"]
        appointment_date = request.form["appointment_date"]
        appointment_time = request.form["appointment_time"]
        reason = request.form["reason"]
        status = request.form["status"]

        # Check Duplicate Appointment
        cur.execute("""
            SELECT appointment_id
            FROM appointments
            WHERE doctor_id=%s
            AND appointment_date=%s
            AND appointment_time=%s
            AND appointment_id<>%s
        """,
        (
            doctor_id,
            appointment_date,
            appointment_time,
            appointment_id
        ))

        existing = cur.fetchone()

        if existing:

            cur.close()
            conn.close()

            return render_template(
                "edit_appointment.html",
                appointment=appointment,
                patients=patients,
                doctors=doctors,
                error="This doctor already has an appointment at the selected date and time."
            )

        # Update Appointment
        cur.execute("""
            UPDATE appointments
            SET
                patient_id=%s,
                doctor_id=%s,
                appointment_date=%s,
                appointment_time=%s,
                reason=%s,
                status=%s
            WHERE appointment_id=%s
        """,
        (
            patient_id,
            doctor_id,
            appointment_date,
            appointment_time,
            reason,
            status,
            appointment_id
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("appointments"))

    cur.close()
    conn.close()

    return render_template(
        "edit_appointment.html",
        appointment=appointment,
        patients=patients,
        doctors=doctors
    )



@app.route("/delete_appointment/<int:appointment_id>")
def delete_appointment(appointment_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM appointments
        WHERE appointment_id = %s
    """, (appointment_id,))

    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("appointments"))


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
