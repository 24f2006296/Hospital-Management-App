from flask_sqlalchemy import SQLAlchemy

from flask import Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ----------------------------Models---------------------------- #


from datetime import datetime
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # e.g., '
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow )

    # Relationships
    doctors = db.relationship('Doctor', back_populates='user', uselist=False)
    patients = db.relationship('Patient', back_populates='user', uselist=False)

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
    Appointments = db.relationship('Appointment', back_populates='patient')
    user = db.relationship('User', back_populates='patients')


class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    specialization_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)

    # Relationships
    appointments = db.relationship('Appointment', back_populates='doctor')
    department = db.relationship('Department', back_populates='doctors')
    user = db.relationship('User', back_populates='doctors')


class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    appointment_status = db.Column(db.String(50), default='Booked', nullable=False)  # e.g., 'Booked', 'Completed', 'Cancelled'

    # Relationships
    treatments = db.relationship('Treatment', back_populates='appointment', uselist=False)
    patient = db.relationship('Patient', back_populates='Appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')


class Availability(db.Model):
    __tablename__ = 'availabilities'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    available_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    

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
            role='Admin')
        
        admin_user.set_password('Admin@123') #Admin password
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created.")
        

# Run this to create the database 
if __name__ == '__main__':
    with app.app_context(): # Needed for DB operations 

        db.create_all()  # Create the database and tables
        create_admin()  # Create admin user if not exists
        
    app.run(debug=True)
