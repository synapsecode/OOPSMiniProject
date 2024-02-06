#Database Layer
from datetime import datetime
from flask import current_app
from CovaxinatorAPI import db

#Association Tables
doctor_location_association = db.Table(
	'DoctorLocationAssociations',
	db.Column('location_id', db.Integer, db.ForeignKey('location.id')),
	db.Column('doctor_id', db.Integer, db.ForeignKey('doctor.id'))
)

patient_location_association = db.Table(
	'PatientLocationAssociations',
	db.Column('location_id', db.Integer, db.ForeignKey('location.id')),
	db.Column('patient_id', db.Integer, db.ForeignKey('patient.id'))
)


class Location(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return f"Location({self.name})"


class VaccineBatch(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	
	vaccine_name = db.Column(db.String)
	batch_id = db.Column(db.String)

	doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))
	patients = db.relationship('Patient', backref='vaccine_batch')

	#doctor (one-may) -> Doctor who registered batch
	#patients (many-one) -> Patients can be tracked back to this batch in inventory
	vaccine_count = db.Column(db.Integer)

	def __init__(self, vName, batchID, vaccineCount):
		self.vaccine_name = vName
		self.batch_id = batchID
		self.vaccine_count = vaccineCount

	def __repr__(self):
		return f"VaccineBatch({self.vaccine_name}, {self.batch_id})"

	@property
	def vaccinated_patients(self):
		patients = self.doctor.patients
		return [P for P in patients if P.is_vaccinated]



class Doctor(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	phone = db.Column(db.String) #also used as username
	password = db.Column(db.String) #also used as password

	location = db.relationship('Location', secondary=doctor_location_association, backref=db.backref('doctors', lazy='dynamic'))
	aadhar = db.Column(db.String)
	address = db.Column(db.String)

	patients = db.relationship('Patient', backref='doctor')
	vaccine_batches = db.relationship('VaccineBatch', backref='doctor')

	follow_ups = db.relationship('FollowUpChatData', backref='doctor')

	#vaccine_batches -> one-many (one doctor can have many batches but one batch has only one doctor)

	def __init__(self, name, phone,password, aadhar, address, location):
		self.name = name
		self.phone = phone
		self.password = password
		self.aadhar = aadhar
		self.address = address
		location.doctors.append(self)

	def vaccinate(self, batchID, patient):
		vacbat = VaccineBatch.query.filter_by(batch_id=batchID).first()
		print(batchID, patient, vacbat)
		if(not vacbat): 
			print("No Such Batch")
			return "No Such Batch"
		if(vacbat.vaccine_count == 0):
			print("NO MORE VACCINES IN BATCH")
			return "NO MORE VACCINES IN BATCH"
		self.patients.append(patient)
		patient.is_vaccinated = True

		vacbat.patients.append(patient)
		vacbat.vaccine_count = vacbat.vaccine_count - 1
		print(f"Vaccinated -> {patient} with Vaccine Batch {vacbat}")
		db.session.commit()

	def register_vaccine(self, vName, batch_id, count):
		vb = VaccineBatch(vName, batch_id, count)
		db.session.add(vb)
		self.vaccine_batches.append(vb)
		db.session.commit()
		print(f"{self} has Registered Vaccine {vb}")

	def get_chats(self, patient):
		chats = None
		for chat in self.follow_ups:
			if(len(chat.patient)>0):
				if(chat.patient[0] == patient):
					print("Chat History Found")
					chats = chat
			else: print("ERR: No Patients in Chat")
		return chats

	def __repr__(self):
		return f"Doctor({self.name}, {self.phone})"



class Patient(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	phone = db.Column(db.String) #also used as username
	password = db.Column(db.String) #also used as password

	location = db.relationship('Location', secondary=patient_location_association, backref=db.backref('patients', lazy='dynamic'))
	aadhar = db.Column(db.String)
	address = db.Column(db.String)

	is_alive = db.Column(db.String)

	is_vaccinated = db.Column(db.Boolean, default=False)

	#vaccine_batch (many-one) Many Patients can be given same batch but one patient can be given only one batch
	#doctor -> The Doctor who assigned vaccine to you
	#sideeffects -> SideEffects
	doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))
	vaccine_batch_id = db.Column(db.Integer, db.ForeignKey('vaccine_batch.id'))
	
	side_effects = db.relationship('SideEffects', backref='patient')
	followup_chat_id = db.Column(db.Integer, db.ForeignKey('follow_up_chat_data.id'))

	def __init__(self,name, phone,password, aadhar, address, location):
		self.name = name
		self.phone = phone
		self.password = password
		self.aadhar = aadhar
		self.address = address
		self.is_alive = True
		location.patients.append(self)

	def report_side_effects(self, symptoms, description):
		se = SideEffects(symptoms=symptoms, description=description)
		db.session.add(se)
		self.side_effects.append(se)
		db.session.commit()

	def report_fatality(self):
		self.is_alive = False
		db.session.commit()

	def __repr__(self):
		return f"Patient({self.name}, {self.phone})"



class SideEffects(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	#patient -> mono
	#doctor -> patient's docto
	
	
	patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
	symptoms = db.Column(db.PickleType) #[List of Symptoms]
	description = db.Column(db.String)

	@property
	def doctor(self):
		return self.patient.doctor

	@property
	def vaccine_batch(self):
		return self.patient.vaccine_batch

	def __init__(self, symptoms, description):
		self.symptoms = symptoms
		self.description = description


class FollowUpChatData(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	patient = db.relationship('Patient', backref='followup_chat')
	doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))
	#{'timestamp', 'message', 'sender'}
	data = db.Column(db.PickleType)

	def __init__(self, patient, doctor):
		self.patient.append(patient)
		doctor.follow_ups.append(self)
		self.data = []

	def add_chat(self, payload):
		"""
		message payload consists of:
			Sender [doctor|patient], Message[Any]
		"""
		new_data = [
			{
				'sender': payload['sender'],
				'timestamp': datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
				'message':payload['message'],
			},
			*self.data,
		]

		self.data = new_data
		db.session.commit()

	@property
	def chats(self):
		chats = [*self.data]
		chats.sort(key=lambda x: x['timestamp'])
		return chats

	

