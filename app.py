from flask import Flask, render_template, request, redirect, session, flash, url_for
import mysql.connector
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key'

def has_role(*roles):
    return 'role' in session and session['role'] in roles


def get_db():
    try:
        connection = mysql.connector.connect(
            host='sql5.freesqldatabase.com',
            user='sql5776006',
            password='3A3vTevFhF',
            database='sql5776006',
            port=3306
        )
        print("✅ Connected to database successfully!")
        return connection
    except mysql.connector.Error as err:
        print(f"❌ Database connection failed: {err}")
        return None# ========== Authentication Routes ==========
@app.route('/')
def home():
    if 'user_id' not in session or not has_role('admin', 'staff'):
    	flash('Unauthorized', 'danger')
    	return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as total FROM Patients")
    total_patients = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM Doctors")
    total_doctors = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM Appointments WHERE status='Scheduled'")
    upcoming_appointments = cursor.fetchone()['total']
    conn.close()

    return render_template('dashboard.html',
                          total_patients=total_patients,
                          total_doctors=total_doctors,
                          upcoming_appointments=upcoming_appointments)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, password, role FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('home'))
        
        flash('Invalid username or password', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form.get('role', 'staff')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, hashed_pw, role)
            )
            conn.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
# ========== Patient Routes ==========
@app.route('/patients')
def patients():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT *, TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) AS age
        FROM Patients
    """)
    patients = cursor.fetchall()
    conn.close()
    return render_template('patients.html', patients=patients)

@app.route('/patients/add', methods=['GET', 'POST'])
def add_patient():
   if 'user_id' not in session or not has_role('admin', 'staff'):
    flash('Unauthorized', 'danger')
    return redirect(url_for('login'))


    if request.method == 'POST':
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Patients
            (first_name, last_name, date_of_birth, gender, blood_type,
             address, phone, email, emergency_contact_name, emergency_contact_phone, medical_history)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.form['first_name'],
            request.form['last_name'],
            request.form['date_of_birth'],
            request.form['gender'],
            request.form['blood_type'],
            request.form['address'],
            request.form['phone'],
            request.form['email'],
            request.form['emergency_contact_name'],
            request.form['emergency_contact_phone'],
            request.form['medical_history']
        ))
        conn.commit()
        conn.close()
        flash('Patient added successfully!', 'success')
        return redirect(url_for('patients'))

    return render_template('add_patient.html')

@app.route('/patients/edit/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            UPDATE Patients SET
            first_name=%s, last_name=%s, date_of_birth=%s, gender=%s, blood_type=%s,
            address=%s, phone=%s, email=%s, emergency_contact_name=%s, emergency_contact_phone=%s, medical_history=%s
            WHERE patient_id=%s
        """, (
            request.form['first_name'],
            request.form['last_name'],
            request.form['date_of_birth'],
            request.form['gender'],
            request.form['blood_type'],
            request.form['address'],
            request.form['phone'],
            request.form['email'],
            request.form['emergency_contact_name'],
            request.form['emergency_contact_phone'],
            request.form['medical_history'],
            patient_id
        ))
        conn.commit()
        conn.close()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('patients'))

    cursor.execute("SELECT * FROM Patients WHERE patient_id=%s", (patient_id,))
    patient = cursor.fetchone()
    conn.close()
    return render_template('edit_patient.html', patient=patient)

@app.route('/patients/delete/<int:patient_id>')
def delete_patient(patient_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Patients WHERE patient_id=%s", (patient_id,))
    conn.commit()
    conn.close()
    flash('Patient deleted!', 'success')
    return redirect(url_for('patients'))

# ========== Doctor Routes ==========
@app.route('/doctors')
def doctors():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Doctors")
    doctors = cursor.fetchall()
    conn.close()
    return render_template('doctors.html', doctors=doctors)

@app.route('/doctors/add', methods=['GET', 'POST'])
def add_doctor():
   if 'user_id' not in session or not has_role('admin'):
    flash('Unauthorized', 'danger')
    return redirect(url_for('login'))


    if request.method == 'POST':
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Doctors
            (first_name, last_name, specialization, phone, email, department, license_number, joining_date, availability_schedule)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.form['first_name'],
            request.form['last_name'],
            request.form['specialization'],
            request.form['phone'],
            request.form['email'],
            request.form.get('department'),
            request.form.get('license_number'),
            request.form.get('joining_date'),
            request.form.get('availability_schedule')
        ))
        conn.commit()
        conn.close()
        flash('Doctor added successfully!', 'success')
        return redirect(url_for('doctors'))

    return render_template('add_doctor.html')

@app.route('/doctors/edit/<int:doctor_id>', methods=['GET', 'POST'])
def edit_doctor(doctor_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            UPDATE Doctors SET
            first_name=%s, last_name=%s, specialization=%s, phone=%s, email=%s,
            department=%s, license_number=%s, joining_date=%s, availability_schedule=%s
            WHERE doctor_id=%s
        """, (
            request.form['first_name'],
            request.form['last_name'],
            request.form['specialization'],
            request.form['phone'],
            request.form['email'],
            request.form.get('department'),
            request.form.get('license_number'),
            request.form.get('joining_date'),
            request.form.get('availability_schedule'),
            doctor_id
        ))
        conn.commit()
        conn.close()
        flash('Doctor updated successfully!', 'success')
        return redirect(url_for('doctors'))

    cursor.execute("SELECT * FROM Doctors WHERE doctor_id=%s", (doctor_id,))
    doctor = cursor.fetchone()
    conn.close()
    return render_template('edit_doctor.html', doctor=doctor)

@app.route('/doctors/delete/<int:doctor_id>')
def delete_doctor(doctor_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Doctors WHERE doctor_id=%s", (doctor_id,))
    conn.commit()
    conn.close()
    flash('Doctor deleted!', 'success')
    return redirect(url_for('doctors'))

# ========== Appointment Routes ==========
@app.route('/appointments')
def appointments():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.*, CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
               CONCAT(d.first_name, ' ', d.last_name) AS doctor_name
        FROM Appointments a
        JOIN Patients p ON a.patient_id = p.patient_id
        JOIN Doctors d ON a.doctor_id = d.doctor_id
    """)
    appointments = cursor.fetchall()
    conn.close()
    return render_template('appointments.html', appointments=appointments)

@app.route('/appointments/add', methods=['GET', 'POST'])
def add_appointment():
    if 'user_id' not in session or not has_role('admin'):
    	flash('Unauthorized', 'danger')
    	return redirect(url_for('login'))



    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            INSERT INTO Appointments
            (patient_id, doctor_id, appointment_date, appointment_time, purpose, status, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            request.form['patient_id'],
            request.form['doctor_id'],
            request.form['appointment_date'],
            request.form['appointment_time'],
            request.form.get('purpose'),
            request.form.get('status', 'Scheduled'),
            request.form.get('notes')
        ))
        conn.commit()
        conn.close()
        flash('Appointment added successfully!', 'success')
        return redirect(url_for('appointments'))

    cursor.execute("SELECT * FROM Patients")
    patients = cursor.fetchall()
    cursor.execute("SELECT * FROM Doctors")
    doctors = cursor.fetchall()
    conn.close()
    return render_template('add_appointment.html', patients=patients, doctors=doctors)

@app.route('/appointments/edit/<int:appointment_id>', methods=['GET', 'POST'])
def edit_appointment(appointment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            UPDATE Appointments SET
            patient_id=%s, doctor_id=%s, appointment_date=%s, appointment_time=%s,
            purpose=%s, status=%s, notes=%s
            WHERE appointment_id=%s
        """, (
            request.form['patient_id'],
            request.form['doctor_id'],
            request.form['appointment_date'],
            request.form['appointment_time'],
            request.form.get('purpose'),
            request.form.get('status'),
            request.form.get('notes'),
            appointment_id
        ))
        conn.commit()
        conn.close()
        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('appointments'))

    cursor.execute("""
        SELECT * FROM Appointments WHERE appointment_id=%s
    """, (appointment_id,))
    appointment = cursor.fetchone()
    cursor.execute("SELECT * FROM Patients")
    patients = cursor.fetchall()
    cursor.execute("SELECT * FROM Doctors")
    doctors = cursor.fetchall()
    conn.close()
    return render_template('edit_appointment.html', 
                         appointment=appointment,
                         patients=patients,
                         doctors=doctors)

@app.route('/appointments/delete/<int:appointment_id>')
def delete_appointment(appointment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Appointments WHERE appointment_id=%s", (appointment_id,))
    conn.commit()
    conn.close()
    flash('Appointment deleted!', 'success')
    return redirect(url_for('appointments'))

# ========== Billing Routes ==========
@app.route('/billing')
def billing():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
               a.appointment_date, a.appointment_time
        FROM Billing b
        JOIN Patients p ON b.patient_id = p.patient_id
        LEFT JOIN Appointments a ON b.appointment_id = a.appointment_id
    """)
    bills = cursor.fetchall()
    conn.close()
    return render_template('billing.html', bills=bills)

@app.route('/billing/add', methods=['GET', 'POST'])
def add_billing():
    if 'user_id' not in session or not has_role('admin', 'staff'):
    	flash('Unauthorized', 'danger')
    	return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            INSERT INTO Billing 
            (patient_id, appointment_id, total_amount, paid_amount, billing_date, due_date, 
             status, payment_method, insurance_claim)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.form['patient_id'],
            request.form.get('appointment_id'),
            request.form['total_amount'],
            request.form.get('paid_amount', 0),
            request.form['billing_date'],
            request.form['due_date'],
            request.form.get('status', 'Unpaid'),
            request.form.get('payment_method'),
            request.form.get('insurance_claim', False)
        ))
        conn.commit()
        conn.close()
        flash('Billing record added!', 'success')
        return redirect(url_for('billing'))

    cursor.execute("SELECT * FROM Patients")
    patients = cursor.fetchall()
    cursor.execute("SELECT * FROM Appointments")
    appointments = cursor.fetchall()
    conn.close()
    return render_template('add_billing.html', patients=patients, appointments=appointments)

@app.route('/billing/edit/<int:bill_id>', methods=['GET', 'POST'])
def edit_billing(bill_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            UPDATE Billing SET
            patient_id=%s, appointment_id=%s, total_amount=%s, paid_amount=%s,
            billing_date=%s, due_date=%s, status=%s, payment_method=%s, insurance_claim=%s
            WHERE bill_id=%s
        """, (
            request.form['patient_id'],
            request.form.get('appointment_id'),
            request.form['total_amount'],
            request.form['paid_amount'],
            request.form['billing_date'],
            request.form['due_date'],
            request.form['status'],
            request.form.get('payment_method'),
            request.form.get('insurance_claim', False),
            bill_id
        ))
        conn.commit()
        conn.close()
        flash('Billing record updated!', 'success')
        return redirect(url_for('billing'))

    cursor.execute("SELECT * FROM Billing WHERE bill_id=%s", (bill_id,))
    bill = cursor.fetchone()
    cursor.execute("SELECT * FROM Patients")
    patients = cursor.fetchall()
    cursor.execute("SELECT * FROM Appointments")
    appointments = cursor.fetchall()
    conn.close()
    return render_template('edit_billing.html', 
                         bill=bill,
                         patients=patients,
                         appointments=appointments)

@app.route('/billing/delete/<int:bill_id>')
def delete_billing(bill_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Billing WHERE bill_id=%s", (bill_id,))
    conn.commit()
    conn.close()
    flash('Billing record deleted!', 'success')
    return redirect(url_for('billing'))

# ========== Medical Records Routes ==========
@app.route('/medical_records')
def medical_records():
   if 'user_id' not in session or not has_role('admin', 'staff'):
    flash('Unauthorized', 'danger')
    return redirect(url_for('medical_records'))
    return redirect(url_for('login'))


    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.*, 
               CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
               CONCAT(d.first_name, ' ', d.last_name) AS doctor_name,
               p.patient_id, d.doctor_id
        FROM MedicalRecords m
        JOIN Patients p ON m.patient_id = p.patient_id
        JOIN Doctors d ON m.doctor_id = d.doctor_id
        ORDER BY m.visit_date DESC
    """)
    records = cursor.fetchall()
    conn.close()
    return render_template('medical_records.html', records=records)

@app.route('/medical_records/view/<int:record_id>')
def view_medical_record(record_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.*, 
               CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
               CONCAT(d.first_name, ' ', d.last_name) AS doctor_name
        FROM MedicalRecords m
        JOIN Patients p ON m.patient_id = p.patient_id
        JOIN Doctors d ON m.doctor_id = d.doctor_id
        WHERE m.record_id = %s
    """, (record_id,))
    record = cursor.fetchone()
    conn.close()
    
    if not record:
        flash('Medical record not found', 'danger')
        return redirect(url_for('medical_records'))
    
    return render_template('view_medical_record.html', record=record)

@app.route('/medical_records/add', methods=['GET', 'POST'])
def add_medical_record():
    if 'user_id' not in session or not has_role('admin', 'doctor'):
        flash('Unauthorized', 'danger')
        return redirect(url_for('medical_records'))
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            cursor.execute("""
                INSERT INTO MedicalRecords
                (patient_id, doctor_id, diagnosis, prescription, notes, follow_up_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                request.form['patient_id'],
                request.form['doctor_id'],
                request.form['diagnosis'],
                request.form['prescription'],
                request.form['notes'],
                request.form.get('follow_up_date') or None
            ))
            conn.commit()
            flash('Medical record added successfully!', 'success')
            return redirect(url_for('medical_records'))
        except Exception as e:
            conn.rollback()
            flash(f'Error adding record: {str(e)}', 'danger')
        finally:
            conn.close()

    cursor.execute("SELECT patient_id, CONCAT(first_name, ' ', last_name) AS name FROM Patients")
    patients = cursor.fetchall()
    cursor.execute("SELECT doctor_id, CONCAT(first_name, ' ', last_name) AS name FROM Doctors")
    doctors = cursor.fetchall()
    conn.close()
    return render_template('add_medical_record.html', 
                         patients=patients, 
                         doctors=doctors)

@app.route('/medical_records/edit/<int:record_id>', methods=['GET', 'POST'])
def edit_medical_record(record_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            cursor.execute("""
                UPDATE MedicalRecords SET
                patient_id = %s,
                doctor_id = %s,
                diagnosis = %s,
                prescription = %s,
                notes = %s,
                follow_up_date = %s
                WHERE record_id = %s
            """, (
                request.form['patient_id'],
                request.form['doctor_id'],
                request.form['diagnosis'],
                request.form['prescription'],
                request.form['notes'],
                request.form.get('follow_up_date') or None,
                record_id
            ))
            conn.commit()
            flash('Medical record updated successfully!', 'success')
            return redirect(url_for('medical_records'))
        except Exception as e:
            conn.rollback()
            flash(f'Error updating record: {str(e)}', 'danger')
        finally:
            conn.close()

    cursor.execute("SELECT * FROM MedicalRecords WHERE record_id = %s", (record_id,))
    record = cursor.fetchone()
    cursor.execute("SELECT patient_id, CONCAT(first_name, ' ', last_name) AS name FROM Patients")
    patients = cursor.fetchall()
    cursor.execute("SELECT doctor_id, CONCAT(first_name, ' ', last_name) AS name FROM Doctors")
    doctors = cursor.fetchall()
    conn.close()
    
    if not record:
        flash('Medical record not found', 'danger')
        return redirect(url_for('medical_records'))
    
    return render_template('edit_medical_record.html', 
                         record=record,
                         patients=patients,
                         doctors=doctors)

@app.route('/medical_records/delete/<int:record_id>', methods=['POST'])
def delete_medical_record(record_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM MedicalRecords WHERE record_id = %s", (record_id,))
        conn.commit()
        flash('Medical record deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting record: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('medical_records'))
# ========== Run Server ==========
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=10000)