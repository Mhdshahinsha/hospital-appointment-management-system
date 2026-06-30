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

            # Store doctor_id in session
            if session["role"] == "Doctor":

                conn = get_connection()
                cur = conn.cursor()

                cur.execute("""
                    SELECT doctor_id
                    FROM doctors
                    WHERE email=%s
                """, (session["email"],))

                doctor = cur.fetchone()

                if doctor:
                    session["doctor_id"] = doctor[0]

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

from datetime import date

@app.route("/doctor")
def doctor_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Doctor":
        return redirect(url_for("login"))

    doctor_id = session["doctor_id"]

    conn = get_connection()
    cur = conn.cursor()

   
# Today's Appointments Count
    cur.execute("""
    SELECT COUNT(*)
    FROM appointments
    WHERE doctor_id=%s
    AND appointment_date=CURRENT_DATE
""", (doctor_id,))

    today_count = cur.fetchone()[0]

    # My Patients
    cur.execute("""
        SELECT COUNT(DISTINCT patient_id)
        FROM appointments
        WHERE doctor_id=%s
    """, (doctor_id,))

    patient_count = cur.fetchone()[0]

    # Pending Cases
    cur.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE doctor_id=%s
        AND status IN ('Pending','Confirmed')
    """, (doctor_id,))

    pending_count = cur.fetchone()[0]

    # Completed Today
    cur.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE doctor_id=%s
        AND appointment_date=CURRENT_DATE
        AND status='Completed'
    """, (doctor_id,))

    completed_today = cur.fetchone()[0]

    # Today's Appointment List
    cur.execute("""
        SELECT
            p.full_name,
            a.appointment_time,
            a.reason,
            a.status
        FROM appointments a

        JOIN patients p
        ON a.patient_id = p.patient_id

        WHERE a.doctor_id=%s
        AND a.appointment_date=CURRENT_DATE

        ORDER BY a.appointment_time
    """, (doctor_id,))

    appointments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "doctor_dashboard.html",
        today_count=today_count,
        patient_count=patient_count,
        pending_count=pending_count,
        completed_today=completed_today,
        appointments=appointments
    )


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

@app.route("/doctor_appointments")
def doctor_appointments():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Doctor":
        return redirect(url_for("login"))

    doctor_id = session["doctor_id"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.appointment_id,
            p.full_name,
            a.appointment_date,
            a.appointment_time,
            a.reason,
            a.status
        FROM appointments a

        JOIN patients p
        ON a.patient_id = p.patient_id

        WHERE a.doctor_id=%s

        ORDER BY
        a.appointment_date DESC,
        a.appointment_time
    """, (doctor_id,))

    appointments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "doctor_appointments.html",
        appointments=appointments
    )

@app.route("/start_consultation/<int:appointment_id>", methods=["GET", "POST"])
def start_consultation(appointment_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Doctor":
        return redirect(url_for("login"))

    doctor_id = session["doctor_id"]

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        diagnosis = request.form["diagnosis"]
        prescription = request.form["prescription"]
        treatment = request.form["treatment"]
        doctor_notes = request.form["doctor_notes"]

        # Get Patient ID
        cur.execute("""
            SELECT patient_id
            FROM appointments
            WHERE appointment_id=%s
        """, (appointment_id,))

        patient = cur.fetchone()

        if not patient:

            cur.close()
            conn.close()

            return "Appointment not found."

        patient_id = patient[0]

        # Check if Medical Record already exists
        cur.execute("""
            SELECT record_id
            FROM medical_records
            WHERE appointment_id=%s
        """, (appointment_id,))

        existing = cur.fetchone()

        if existing:

            cur.close()
            conn.close()

            return render_template(
                "start_consultation.html",
                appointment=None,
                error="Medical Record already exists for this appointment."
            )

        # Insert Medical Record
        cur.execute("""
            INSERT INTO medical_records
            (
                appointment_id,
                patient_id,
                doctor_id,
                diagnosis,
                prescription,
                treatment,
                doctor_notes
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            appointment_id,
            patient_id,
            doctor_id,
            diagnosis,
            prescription,
            treatment,
            doctor_notes
        ))

        # Automatically Complete Appointment
        cur.execute("""
            UPDATE appointments
            SET status='Completed'
            WHERE appointment_id=%s
        """, (appointment_id,))

        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("doctor_appointments"))

    # Load Appointment Details
    cur.execute("""
        SELECT
            a.appointment_id,
            p.full_name,
            d.doctor_name,
            a.appointment_date,
            a.appointment_time
        FROM appointments a

        JOIN patients p
            ON a.patient_id = p.patient_id

        JOIN doctors d
            ON a.doctor_id = d.doctor_id

        WHERE a.appointment_id=%s
        AND a.doctor_id=%s
    """,
    (
        appointment_id,
        doctor_id
    ))

    appointment = cur.fetchone()

    cur.close()
    conn.close()

    if not appointment:
        return "Appointment not found."

    return render_template(
        "start_consultation.html",
        appointment=appointment
    )


@app.route("/view_medical_record/<int:appointment_id>")
def view_medical_record(appointment_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Doctor":
        return redirect(url_for("login"))

    doctor_id = session["doctor_id"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            mr.record_id,
            p.full_name,
            d.doctor_name,
            mr.diagnosis,
            mr.prescription,
            mr.treatment,
            mr.doctor_notes,
            mr.created_at
        FROM medical_records mr

        JOIN patients p
            ON mr.patient_id = p.patient_id

        JOIN doctors d
            ON mr.doctor_id = d.doctor_id

        WHERE mr.appointment_id=%s
        AND mr.doctor_id=%s
    """,
    (
        appointment_id,
        doctor_id
    ))

    record = cur.fetchone()

    cur.close()
    conn.close()

    if not record:
        return "Medical Record not found."

    return render_template(
        "view_medical_record.html",
        record=record
    )


@app.route("/update_doctor_appointment_status/<int:appointment_id>",
           methods=["GET","POST"])
def update_doctor_appointment_status(appointment_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Doctor":
        return redirect(url_for("login"))

    doctor_id = session["doctor_id"]

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        status = request.form["status"]

        cur.execute("""
            UPDATE appointments
            SET status=%s
            WHERE appointment_id=%s
            AND doctor_id=%s
        """,
        (
            status,
            appointment_id,
            doctor_id
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("doctor_appointments"))

    cur.execute("""
        SELECT
            appointment_id,
            appointment_date,
            appointment_time,
            status
        FROM appointments
        WHERE appointment_id=%s
        AND doctor_id=%s
    """,
    (
        appointment_id,
        doctor_id
    ))

    appointment = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "update_doctor_appointment.html",
        appointment=appointment
    )


@app.route("/doctor_patients")
def doctor_patients():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Doctor":
        return redirect(url_for("login"))

    doctor_id = session["doctor_id"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT
            p.patient_id,
            p.full_name,
            p.gender,
            p.phone,
            p.email
        FROM patients p

        JOIN appointments a
        ON p.patient_id = a.patient_id

        WHERE a.doctor_id=%s

        ORDER BY p.full_name
    """, (doctor_id,))

    patients = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "doctor_patients.html",
        patients=patients
    )

@app.route("/view_patient/<int:patient_id>")
def view_patient(patient_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Doctor":
        return redirect(url_for("login"))

    doctor_id = session["doctor_id"]

    conn = get_connection()
    cur = conn.cursor()

    # Patient Details
    cur.execute("""
        SELECT
            patient_id,
            full_name,
            email,
            phone,
            gender,
            age,
            address
        FROM patients
        WHERE patient_id=%s
    """, (patient_id,))

    patient = cur.fetchone()

    # Appointment History with this doctor
    cur.execute("""
        SELECT
            appointment_date,
            appointment_time,
            reason,
            status
        FROM appointments
        WHERE patient_id=%s
        AND doctor_id=%s
        ORDER BY appointment_date DESC
    """,
    (
        patient_id,
        doctor_id
    ))

    history = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "view_patient.html",
        patient=patient,
        history=history
    )


@app.route("/doctor_schedule")
def doctor_schedule():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Doctor":
        return redirect(url_for("login"))

    doctor_id = session["doctor_id"]

    conn = get_connection()
    cur = conn.cursor()

    # Doctor Schedule
    cur.execute("""
        SELECT
            doctor_name,
            department,
            available_days,
            available_time
        FROM doctors
        WHERE doctor_id=%s
    """, (doctor_id,))

    doctor = cur.fetchone()

    # Today's Appointments
    cur.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE doctor_id=%s
        AND appointment_date=CURRENT_DATE
    """, (doctor_id,))

    today_count = cur.fetchone()[0]

    # Upcoming Appointments
    cur.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE doctor_id=%s
        AND appointment_date>=CURRENT_DATE
        AND status IN ('Pending','Confirmed')
    """, (doctor_id,))

    upcoming_count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        "doctor_schedule.html",
        doctor=doctor,
        today_count=today_count,
        upcoming_count=upcoming_count
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
    
    cur.execute("""
    SELECT COALESCE(SUM(total_amount), 0)
    FROM bills
    WHERE patient_id=%s
    AND payment_status='Pending'
    """, (patient_id,))

    pending_bill_amount = cur.fetchone()[0]

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
        appointments=appointments,
        pending_bill_amount=pending_bill_amount
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

@app.route("/patient_bills")
def patient_bills():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Patient":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            b.bill_id,
            d.doctor_name,
            a.appointment_date,
            b.total_amount,
            b.payment_status
        FROM bills b

        JOIN doctors d
        ON b.doctor_id = d.doctor_id

        JOIN appointments a
        ON b.appointment_id = a.appointment_id

        WHERE b.patient_id=%s

        ORDER BY b.created_at DESC
    """,
    (
        session["patient_id"],
    ))

    bills = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "patient_bill.html",
        bills=bills
    )


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
    a.status,
    b.bill_id
FROM appointments a

JOIN patients p
ON a.patient_id = p.patient_id

JOIN doctors d
ON a.doctor_id = d.doctor_id

LEFT JOIN bills b
ON a.appointment_id = b.appointment_id

ORDER BY a.appointment_id DESC
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
            "Pending"
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
        status="pending"
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

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            b.bill_id,
            p.full_name,
            d.doctor_name,
            b.total_amount,
            b.payment_status,
            b.created_at
        FROM bills b
        JOIN patients p
            ON b.patient_id = p.patient_id
        JOIN doctors d
            ON b.doctor_id = d.doctor_id
        ORDER BY b.bill_id DESC
    """)

    bills = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "bills.html",
        bills=bills
    )


@app.route("/add_bill/<int:appointment_id>", methods=["GET", "POST"])
def add_bill(appointment_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    # Load appointment details
    cur.execute("""
        SELECT
            a.appointment_id,
            p.patient_id,
            p.full_name,
            d.doctor_id,
            d.doctor_name,
            d.consultation_fee
        FROM appointments a
        JOIN patients p
            ON a.patient_id = p.patient_id
        JOIN doctors d
            ON a.doctor_id = d.doctor_id
        WHERE a.appointment_id=%s
    """, (appointment_id,))

    bill = cur.fetchone()

    if request.method == "POST":

        patient_id = bill[1]
        doctor_id = bill[3]

        consultation_fee = request.form["consultation_fee"]
        medicine_charge = request.form["medicine_charge"]
        lab_charge = request.form["lab_charge"]
        other_charge = request.form["other_charge"]
        discount = request.form["discount"]
        total_amount = request.form["total_amount"]
        payment_status = request.form["payment_status"]

        # Check if bill already exists
        cur.execute("""
            SELECT bill_id
            FROM bills
            WHERE appointment_id=%s
        """, (appointment_id,))

        existing = cur.fetchone()

        if existing:

            cur.close()
            conn.close()

            return render_template(
                "add_bill.html",
                bill=bill,
                error="Bill already generated for this appointment."
            )

        # Save Bill
        cur.execute("""
            INSERT INTO bills
            (
                patient_id,
                doctor_id,
                appointment_id,
                consultation_fee,
                medicine_charge,
                lab_charge,
                other_charge,
                discount,
                total_amount,
                payment_status
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            patient_id,
            doctor_id,
            appointment_id,
            consultation_fee,
            medicine_charge,
            lab_charge,
            other_charge,
            discount,
            total_amount,
            payment_status
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("bills"))

    cur.close()
    conn.close()

    return render_template(
        "add_bill.html",
        bill=bill
    )


@app.route("/view_bill/<int:bill_id>")
def view_bill(bill_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            b.bill_id,
            p.full_name,
            d.doctor_name,
            a.appointment_date,
            b.consultation_fee,
            b.medicine_charge,
            b.lab_charge,
            b.other_charge,
            b.discount,
            b.total_amount,
            b.payment_status,
            b.created_at
        FROM bills b
        JOIN patients p
            ON b.patient_id = p.patient_id
        JOIN doctors d
            ON b.doctor_id = d.doctor_id
        JOIN appointments a
            ON b.appointment_id = a.appointment_id
        WHERE b.bill_id=%s
    """, (bill_id,))

    bill = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "view_bill.html",
        bill=bill
    )


@app.route("/edit_bill/<int:bill_id>", methods=["GET", "POST"])
def edit_bill(bill_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        medicine_charge = request.form["medicine_charge"]
        lab_charge = request.form["lab_charge"]
        other_charge = request.form["other_charge"]
        discount = request.form["discount"]
        payment_status = request.form["payment_status"]

        # Get consultation fee
        cur.execute("""
            SELECT consultation_fee
            FROM bills
            WHERE bill_id=%s
        """, (bill_id,))

        consultation_fee = float(cur.fetchone()[0])

        total_amount = (
            consultation_fee
            + float(medicine_charge)
            + float(lab_charge)
            + float(other_charge)
            - float(discount)
        )

        cur.execute("""
            UPDATE bills
            SET
                medicine_charge=%s,
                lab_charge=%s,
                other_charge=%s,
                discount=%s,
                total_amount=%s,
                payment_status=%s
            WHERE bill_id=%s
        """,
        (
            medicine_charge,
            lab_charge,
            other_charge,
            discount,
            total_amount,
            payment_status,
            bill_id
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("bills"))

    cur.execute("""
    SELECT
        a.appointment_id,
        p.patient_id,
        p.full_name,
        d.doctor_id,
        d.doctor_name,
        b.consultation_fee,
        b.medicine_charge,
        b.lab_charge,
        b.other_charge,
        b.discount,
        b.total_amount,
        b.payment_status
    FROM bills b

    JOIN patients p
        ON b.patient_id = p.patient_id

    JOIN doctors d
        ON b.doctor_id = d.doctor_id

    JOIN appointments a
        ON b.appointment_id = a.appointment_id

    WHERE b.bill_id=%s
""", (bill_id,))
    bill = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "edit_bill.html",
        bill=bill
    )


@app.route("/delete_bill/<int:bill_id>")
def delete_bill(bill_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM bills
        WHERE bill_id=%s
    """, (bill_id,))

    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("bills"))

 
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

if __name__ == "__main__":

    app.run(debug=True)
