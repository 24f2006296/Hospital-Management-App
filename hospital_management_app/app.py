from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, redirect, url_for, flash, session
from flask import Flask
from datetime import datetime, date, timedelta
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital_management.db'
app.config['SECRET_KEY'] = 'secret_key_420'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ----------------------------Models---------------------------- #



class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # e.g., '
    status = db.Column(db.String(20), default='active', nullable=False)   #active/block
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow )

    # Relationships
    doctor = db.relationship('Doctor', back_populates='user', uselist=False)
    patient = db.relationship('Patient', back_populates='user', uselist=False)

    # Password hashing method
    def set_password(self, password):
        #Set password for the user 
        self.password = password

    # Password verification method
    def check_password(self, password):
        return self.password == password


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    # Relationship: Ek department ke kai doctors ho sakte hain
    doctors = db.relationship('Doctor', back_populates ='department')

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationship
    appointments = db.relationship('Appointment', back_populates='patient')
    user = db.relationship('User', back_populates='patient')


class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    specialization_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    experience = db.Column(db.Integer, nullable=True)
    phone_number = db.Column(db.String(15), nullable=False)

    # Relationships
    appointments = db.relationship('Appointment', back_populates='doctor')
    department = db.relationship('Department', back_populates='doctors')
    user = db.relationship('User', back_populates='doctor')


class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    appointment_status = db.Column(db.String(50), default='Booked', nullable=False)  # e.g., 'Booked', 'Completed', 'Cancelled'

    # Relationships
    treatments = db.relationship('Treatment', back_populates='appointment', uselist=False)
    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')


class Availability(db.Model):
    __tablename__ = 'availabilities'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    available_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    # Relationship
    doctor = db.relationship('Doctor', backref='availabilities')



class Treatment(db.Model):
    __tablename__ = 'treatments'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    treatment_date = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    diagnosis = db.Column(db.String(200), nullable=False)
    prescription = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.String(500), nullable=True) # Additional notes for patient treatment by doctor
    
    # Relationship
    appointment = db.relationship('Appointment', back_populates='treatments')


    #----------------------------------------------------------------#

    

    #--------------Admin Data--------------#
def create_admin():
    db.create_all()
    if not User.query.filter_by(email='admin@hospital.com').first():
        admin_user = User(
            username='admin',
            email='admin@hospital.com',
            role='admin')
        
        admin_user.set_password('Admin@123') #Admin password
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created.")

#---------------------------------routes---------------------------------#

@app.route('/')
def home():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'doctor':
            return redirect(url_for('doctor_dashboard'))
        elif role == 'patient':
            return redirect(url_for('patient_dashboard'))
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    #if user already login , redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        phone = request.form['phone']

        # check if user already exists
        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            flash('Username or Email already exists.', 'error')
            return redirect(url_for('register'))
        # Creat new user
        new_user = User(
            username=username,
            email=email,
            role='patient')
        
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        # create new paient details
        new_patient = Patient(
            name=name,
            phone_number=phone,
            user_id=new_user.id)
        db.session.add(new_patient)
        db.session.commit()

        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    #if user already login , redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password", "error")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    flash("Logout successfully!.", "success")
    return redirect(url_for('login'))

# refer to correct dashboard
@app.route('/dashboard')
def dashboard():
    
    if 'user_id' not in session:
        flash("Pehle login karein.", "error")
        return redirect(url_for('login'))

    if session['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif session['role'] == 'doctor':
        return redirect(url_for('doctor_dashboard'))
    elif session['role'] == 'patient':
        return redirect(url_for('patient_dashboard'))
    else:
        return redirect(url_for('logout'))

@app.route('/admin/dashboard')
def admin_dashboard():
    # access only for dmin
    if 'user_id' not in session or session.get('role') != 'admin' :
        flash("access denied!", "error")
        return redirect(url_for('login'))
    # search function
    doctor_search_query = request.args.get('doctor_search')
    patient_search_query = request.args.get('patient_search')
    # doctor list
    if doctor_search_query:
        doctors = Doctor.query.join(User).filter(
                (Doctor.name.ilike(f'%{doctor_search_query}%')) |
                (User.username.ilike(f'%{doctor_search_query}%'))
        ).all()
        
    else:
        doctors = Doctor.query.all()
    # patient list
    if patient_search_query:
        patients = Patient.query.join(User).filter(
                (Patient.name.ilike(f'%{patient_search_query}%')) |
                (User.username.ilike(f'%{patient_search_query}%'))
            ).all()
    else:
        patients = Patient.query.all()
    # appointments list
    appointments = Appointment.query.all()

    # stats for dashboard
    stats = {
        'doctor_count': Doctor.query.count(),
        'patient_count': Patient.query.count(),
        'appointment_count': Appointment.query.count()
    }

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        doctors=doctors,
        patients=patients,
        appointments=appointments
    )

@app.route('/admin/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    # admin access only
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("access denied!", "error")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        spec_name = request.form['specialization']
        email = request.form['email']
        experience = request.form['experience']
        phone = request.form['contact']
        password = request.form['password']

        username = email.split('@')[0] # genarate username from email

        # check if email or username already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return render_template('add_doctor.html')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('add_doctor.html')
        
        department = Department.query.filter_by(name=spec_name).first()
        if not department:
            department = Department(name=spec_name)
            db.session.add(department)
            db.session.commit()

        # create user for doctor
        new_user = User(
            username=username,
            email=email,
            role='doctor')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # create doctor details
        new_doctor = Doctor(
            name=name,
            phone_number=phone,
            experience=int(experience), 
            specialization_id=department.id, 
            user_id=new_user.id 
            )
        db.session.add(new_doctor)
        db.session.commit()
        flash('Doctor added successfully', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_doctor.html')


@app.route('/admin/block_doctor/<int:doctor_id>')
def block_doctor(doctor_id):
    if 'user_id' not in session or session.get('role') != 'admin' :
        return redirect(url_for('login'))
    try:
        doctor = Doctor.query.get(doctor_id)
        user = doctor.user

        if user.status == 'active':
            user.status = 'blocked'
            flash("Doctor blocked successfully.", "success")
        else:
            user.status = 'active'
            flash("Doctor unblocked successfully.", "success")
        
        db.session.commit()
    except Exception as e:
        flash("Unexpected error.", "error")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/block_patient/<int:patient_id>')
def block_patient(patient_id):
    if 'user_id' not in session or session.get('role') != 'admin' :
        return redirect(url_for('login'))
    try:
        patient = Patient.query.get(patient_id)
        user = patient.user

        if user.status == 'active':
            user.status = 'blocked'
            flash("Patient blocked successfully.", "success")
        else:
            user.status = 'active'
            flash("Patient unblocked successfully.", "success")
        
        db.session.commit()
    except Exception as e:
        flash("Unexpected error.", "error")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete_doctor/<int:doctor_id>')
def delete_doctor(doctor_id):
    if 'user_id' not in session or session.get('role') != 'admin' :
        return redirect(url_for('login'))
    
    try:
        doctor = Doctor.query.get(doctor_id)
        user = doctor.user

        db.session.delete(doctor)
        db.session.delete(user)
        db.session.commit()
        flash("Doctor deleted successfully.", "success")

    except Exception as e:
        flash("Unexpected error.", "error")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_patient/<int:patient_id>')
def delete_patient(patient_id):
    if 'user_id' not in session or session.get('role') != 'admin' :
        return redirect(url_for('login'))
    
    try:
        patient = Patient.query.get(patient_id)
        user = patient.user
        db.session.delete(patient)
        db.session.delete(user)

        db.session.commit()
        flash("Patient deleted successfully.", "success")

    except Exception as e:
        flash("Unexpected error.", "error")
    return redirect(url_for('admin_dashboard'))



@app.route('/admin/edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
def edit_doctor(doctor_id):
    if 'user_id' not in session or session.get('role') != 'admin' :
        return redirect(url_for('login'))
    doctor = Doctor.query.get(doctor_id)

    if request.method == 'POST':
        try:
            doctor.name = request.form['name']
            doctor.phone_number = request.form['phone']
            doctor.experience = request.form['experience']
            spec_name = request.form['specialization']
            department = Department.query.filter_by(name=spec_name).first()
            if not department:
                department = Department(name=spec_name)
                db.session.add(department)
                db.session.commit()
            doctor.specialization_id = department.id
            db.session.commit()
            flash("Doctor details updated successfully.", "success")
            return redirect(url_for('admin_dashboard'))
        
        except Exception as e:
            flash("Unexpected error.", "error") 
        return render_template('edit_doctor.html', doctor=doctor)
    return render_template('edit_doctor.html', doctor=doctor)

@app.route('/admin/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    if 'user_id' not in session or session.get('role') != 'admin' :
        return redirect(url_for('login'))
    patient = Patient.query.get(patient_id)

    if request.method == 'POST':
        try:
            patient.name = request.form['name']
            patient.phone_number = request.form['phone']
            db.session.commit()
            flash("Patient details updated successfully.", "success")
            return redirect(url_for('admin_dashboard'))
        
        except Exception as e:
            flash("Unexpected error.", "error") 
        return render_template('edit_patient.html', patient=patient)
    return render_template('edit_patient.html', patient=patient)


@app.route('/patient/dashboard')
def patient_dashboard():
    # access for patient only
    if 'user_id' not in session or session.get('role') != 'patient':
        flash("Access denied!", "error")
        return redirect(url_for('logout'))
    
    # try to fetch logged-in patient
    patient = Patient.query.filter_by(user_id=session['user_id']).first()
    if not patient:
        flash("Not Found", "error")
        return redirect(url_for('login'))
    
    # doctor search logic
    doctor_search_query = request.args.get('doctor_search')
    if doctor_search_query:
        doctors = Doctor.query.join(Department).filter(
            (Doctor.name.ilike(f'%{doctor_search_query}%')) |
            (Department.name.ilike(f'%{doctor_search_query}%'))
        ).all()
    else:
        doctors = Doctor.query.all()

    # fetch appointments and treatment details
    appointments = Appointment.query.filter_by(patient_id=patient.id).all()
    # Treatment History
    treatments = Treatment.query.join(Appointment).filter(
        Appointment.patient_id == patient.id,
        Appointment.appointment_status == 'Completed'
    ).all()

    return render_template('patient_dashboard.html', 
            patient=patient, doctors=doctors,
            appointments=appointments,
            treatments=treatments, search_query=doctor_search_query,
            now=datetime.utcnow())
    

@app.route('/patient/profile', methods=['GET', 'POST'])
def patient_profile():
    
    if 'user_id' not in session or session['role'] != 'patient':
        flash("Access denied!", "error")
        return redirect(url_for('login'))
    try:
        patient = Patient.query.filter_by(user_id=session['user_id']).first()
        if not patient:
            flash("Patient profile not found.", "error")
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            name = request.form['name']
            phone = request.form['phone']
            patient.name = name
            patient.phone_number = phone
            db.session.commit()
            flash("Profile updated successfully.", "success")
            return redirect(url_for('patient_profile'))
        
        return render_template('patient_profile.html', patient=patient)
    
    except Exception as e:
        flash("Unexpected error.", "error")
        return redirect(url_for('login'))

# book appointment logic   
@app.route('/patient/book_appointment', methods=['POST'])
def book_appointment():

    if 'user_id' not in session or session['role'] != 'patient':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    try:
        patient = Patient.query.filter_by(user_id=session['user_id']).first()
        if not patient:
            flash("Patient profile not found.", "error")
            return redirect(url_for('logout'))
        
        doctor_id = request.form['doctor_id']
        date_time_str = request.form['date_time']

        appointment_date = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')

        # new appointment 
        new_appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_status='Booked')
        db.session.add(new_appointment)
        db.session.commit()
        flash("Appointment booked successfully.", "success")

    except Exception as e:
        flash("unexpected error.", "error")
    
    return redirect(url_for('patient_dashboard'))

# cancel appointment logic
@app.route('/patient/cancel_appointment/<int:appointment_id>')
def cancel_appointment(appointment_id):
    if 'user_id' not in session or session['role'] != 'patient':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    
    try:
        patient = Patient.query.filter_by(user_id=session['user_id']).first()
        appointment = Appointment.query.get(appointment_id)

        if appointment.patient_id != patient.id:
            flash("You cannot cancel this appointment.", "error")
            return redirect(url_for('patient_dashboard'))
        
        appointment.appointment_status = 'Cancelled'
        db.session.commit()
        flash("Appointment cancelled successfully.", "success")

    except Exception as e:
        flash("Unexpected error.", "error")
    return redirect(url_for('patient_dashboard'))

@app.route('/treatment_details/<int:appointment_id>')
def treatment_details(appointment_id):
    if 'user_id' not in session:
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    try:
        
        treatment = Treatment.query.filter_by(appointment_id=appointment_id).first()
        patient = Patient.query.filter_by(user_id=session['user_id']).first()
        
        if not treatment:
            flash("Treatment details not found for this appointment.", "info")
            return redirect(url_for('patient_dashboard'))

        if treatment.appointment.patient_id != patient.id:
            flash("You cannot view this treatment details.", "error")
            return redirect(url_for('patient_dashboard'))
        
        return render_template('treatment.html', treatment=treatment)
    except Exception as e:
        flash("Unexpected error.", "error")
        return redirect(url_for('patient_dashboard'))

@app.route('/doctor/profile/<int:doctor_id>')
def doctor_profile(doctor_id):
    if 'user_id' not in session:
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    try:
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            flash("Doctor not found.", "error")
            return redirect(url_for('dashboard'))
        
        return render_template('doctor_profile.html', doctor=doctor)
    except Exception as e:
        flash("Unexpected error.", "error")
        return redirect(url_for('login'))

@app.route('/doctor/dashboard')
def doctor_dashboard():
    # access for doctor only
    if 'user_id' not in session or session.get('role') != 'doctor':
        flash("Access denied!", "error")
        return redirect(url_for('logout'))
    
    # loggedin doctor
    doctor = Doctor.query.filter_by(user_id=session['user_id']).first()
    if not doctor:
        flash("not found", "error")
        return redirect(url_for('login'))
        
    doctor_id = doctor.id
    # upcoming appointments 
    upcoming_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_status == 'Booked', 
            Appointment.appointment_date >= datetime.utcnow()).all()
        
    # add treatments in completed appointments
    completed_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_status == 'Completed',
            Appointment.treatments == None ).all()
   
    return render_template('doctor_dashboard.html',
                doctor=doctor,
                appointments=upcoming_appointments,
                completed_appointments=completed_appointments,)
    
    
    
    
@app.route('/doctor/update_status/<int:appointment_id>/<string:status>')
def update_appointment_status(appointment_id, status):

    if 'user_id' not in session or session['role'] != 'doctor':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    try:
        doctor = Doctor.query.filter_by(user_id=session['user_id']).first()
        appointment = Appointment.query.get(appointment_id)

        if appointment.doctor_id != doctor.id:
            flash("You cannot update this appointment.", "error")
            return redirect(url_for('doctor_dashboard'))
        
        # update status
        if status == 'Completed':
            appointment.appointment_status = 'Completed'
            flash("Appointment completed.", "success")
        elif status == 'Rejected':
            appointment.appointment_status = 'Cancelled'
            flash("Appointment Rejected.", "success")

        db.session.commit()
    except Exception as e:
        flash("Unexpected error.", "error")
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/treatment', methods=['POST'])
def treatment():
    if 'user_id' not in session or session['role'] != 'doctor':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    try:
        doctor = Doctor.query.filter_by(user_id=session['user_id']).first()
        appointment_id = request.form['appointment_id']
        diagnosis = request.form['diagnosis']
        prescription = request.form['prescription']
        notes = request.form['notes']

        appointment = Appointment.query.get(appointment_id)

        if appointment.doctor_id != doctor.id:
            flash("You cannot add treatment for this appointment.", "error")
            return redirect(url_for('doctor_dashboard'))
        
        # new treatment 
        new_treatment = Treatment(
            appointment_id=appointment.id,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes)
        
        db.session.add(new_treatment)
        db.session.commit()
        flash("Treatment details added successfully.", "success")
    except Exception as e:
        flash("Unexpected error.", "error")
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/availability', methods=['POST'])
def availability():
    if 'user_id' not in session or session['role'] != 'doctor':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    try:
        doctor = Doctor.query.filter_by(user_id=session['user_id']).first()

        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)

        # available dates time 9 AM to 5 PM
        current_date = start_date
        while current_date <= end_date:
            new_availability = Availability(
                doctor_id=doctor.id,
                available_date=current_date,
                start_time=datetime.strptime('09:00', '%H:%M').time(),
                end_time=datetime.strptime('17:00', '%H:%M').time()
            )
            db.session.add(new_availability)
            current_date += timedelta(days=1)

        db.session.commit()
        flash("Availability added successfully.", "success")
    except Exception as e:
        flash("Unexpected error.", "error")
    return redirect(url_for('doctor_dashboard'))



# Run this to create the database 
if __name__ == '__main__':
    with app.app_context(): # Needed for DB operations 

        db.create_all()  # Create the database and tables
        create_admin()  # Create admin user if not exists
        
    app.run(debug=True)
