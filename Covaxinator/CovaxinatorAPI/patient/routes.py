from flask import render_template, request, Blueprint, flash, url_for, redirect, jsonify, flash, session
import json
from CovaxinatorAPI.models import *
from CovaxinatorAPI import db
from werkzeug.utils import secure_filename
import os
from CovaxinatorAPI.config import Config

patient = Blueprint('patient', __name__)

@patient.route('/login', methods=['GET', 'POST'])
def patient_login():
	if(request.method == 'POST'):
		data = request.form
		phone = data['phone']
		password = data['password']
		patient = Patient.query.filter_by(phone=phone).first()
		if(not patient or patient.password != password):
			print("INVALID")
			flash('Invalid Credentials!', 'danger')
			return jsonify({"redirect": url_for('patient.patient_login')})

		flash('Login Completed Successfully!', 'success')
		session['logged_in_patient'] = patient.id
		return jsonify({"redirect": url_for('patient.patient_home')})
	return render_template('patient/login.html', title='Patient Login')

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@patient.route('/register', methods=['GET', 'POST'])
def patient_register():
	if(request.method == 'POST'):
		data = request.form
		location = Location.query.filter_by(name=data['location'].lower()).first()
		if(not location):
			location = Location(name=data['location'].lower())
			db.session.add(location)
			db.session.commit()
		print(data)

		print(request.files['file'])
		file = request.files['file']
		if(file):
			if(file.filename == ''):
				flash('No selected file', 'danger')
				return redirect(request.url)
			if file and allowed_file(file.filename):
				filename = secure_filename(data['phone'] + '.' + file.filename.rsplit('.', 1)[1].lower())
				file.save(os.path.join(Config.UPLOAD_FOLDER, 'Patients', filename))

		# Handle Image Uploads
		# Essentially they will come to the UPLOADS/Patients folder as their number
		# and can be queried via their number
		
		pat = Patient(
			name=data['full_name'],
			phone=data['phone'],
			password=data['password'],
			aadhar=data['aadhar'],
			address=data['address'],
			location=location
		)
		db.session.add(pat)
		db.session.commit()
		flash('Successfully Created Account!', 'success')
		return redirect(url_for('patient.patient_login'))
	
	return render_template('patient/register.html', title='Patient Register')

@patient.route('/home')
def patient_home():
	pat_id = session.get('logged_in_patient')
	if(not pat_id): return redirect(url_for('patient.patient_login'))
	patient = Patient.query.filter_by(id=pat_id).first()

	shield_data = {}
	for L in Location.query.all():
		vac = len([P for P in L.patients.all() if P.is_vaccinated])
		unvac = len([P for P in L.patients.all() if not P.is_vaccinated])
		total = vac+unvac if vac+unvac > 0 else 1
		print([P for P in L.patients])
		shield_data[L.name] = {
			'vaccinated': vac,
			'notvaccinated':unvac,
			'shieldpoint': round((vac/total)*100,3),
		}
	shield_data = json.dumps(shield_data)

	vac_centers = {}
	for L in Location.query.all():
		vac_centers[L.name] = [
			{
				'name': D.name,
				'address': D.address,
				'phone': D.phone,
			} for D in L.doctors
		]
	vac_centers = json.dumps(vac_centers)
	return render_template('patient/home.html',
		title="patient Home", 
		phone=patient.phone, 
		shield_data=shield_data, 
		vac_centers=vac_centers, 
		json=json,
		patient=patient
	)

@patient.route('/logout')
def patient_logout():
	session['logged_in_patient'] = None
	return jsonify({})


@patient.route('/report_fatality')
def report_fatality():
	pat_id = session.get('logged_in_patient')
	if(not pat_id): return redirect(url_for('patient.patient_login'))
	print("Reporting Death")
	patient = Patient.query.filter_by(id=pat_id).first()
	if(not patient.is_vaccinated):
		flash('You have not been vaccinated', 'danger')
		return redirect(url_for('patient.patient_home'))
	patient.is_alive = False
	db.session.commit()
	return redirect(url_for('patient.patient_home'))


@patient.route('/vaccination_certificate/<phone>')
def get_vaccination_certificate(phone):
	patient = Patient.query.filter_by(phone=phone).first()
	if(not patient): return "NO SUCH PATIENT"
	if(not patient.is_vaccinated): return "PATIENT NOT VACCINATED"

	vaccine_batch = patient.vaccine_batch
	

	return render_template('patient/certificate.html', title="Vaccination Certificate", patient=patient, vaccine_batch=vaccine_batch)


@patient.route('/report_symptoms', methods=['POST'])
def report_symptoms():
	pat_id = session.get('logged_in_patient')
	if(not pat_id): return redirect(url_for('patient.patient_login'))
	data = request.form
	patient_phone = data['patient_phone']
	symptoms = data['symptoms'].split(',')
	description = data['symdesc']
	patient = Patient.query.filter_by(phone=patient_phone).first()
	if(not patient): return "NO SUCH PATIENT"
	if(not patient.is_vaccinated):
		flash('You have not been vaccinated', 'danger')
		return jsonify({'redirect': url_for('patient.patient_home')})
	patient.report_side_effects(symptoms, description)
	return jsonify({'redirect': url_for('patient.patient_home')})

@patient.route('/follow_ups')
def follow_ups():
	pat_id = session.get('logged_in_patient')
	if(not pat_id): return redirect(url_for('patient.patient_login'))
	patient = Patient.query.filter_by(id=pat_id).first()
	doctor = patient.doctor
	return render_template('patient/follow_ups.html', title="Follow Ups", doctor=doctor, patient=patient)


@patient.route('/getchats/<doctorphone>')
def getchats(doctorphone):
	pat_id = session.get('logged_in_patient')
	patient = Patient.query.filter_by(id=pat_id).first()

	doctor = Doctor.query.filter_by(phone=doctorphone).first()
	if(not doctor): return "NO DOCTOR"
	
	print("====GETCHATS : PATIENT ====")
	print(f"Doctor {doctorphone} -> {doctor}")
	chats = doctor.get_chats(patient)
	print("Chat Object", chats)
	
	# print("CH: ", chats.chats)
	if(not chats):
		chats = FollowUpChatData(patient=patient, doctor=doctor)
		db.session.add(chats)
		db.session.commit()
	
	return jsonify({'chats': chats.chats})

@patient.route('/updatechat/<doctorphone>', methods=['POST'])
def updatechat(doctorphone):
	pat_id = session.get('logged_in_patient')

	print("------PATIENT : UPDATE CHAT-----------")
	print('~~~ Recieved DoctorPhone:', doctorphone)
	

	patient = Patient.query.filter_by(id=pat_id).first()
	print("~~~ PATIENT FROM LOGIN:", patient)

	doctor = Doctor.query.filter_by(phone=doctorphone).first()
	print("~~~ DOCTOR OBJECT:", doctor)
	if(not doctor):
		print("No Doctor")
		return jsonify({'status': 0})

	data = request.form
	#Sender [doctor|patient], Message[Any]
	payload = {
		'sender': data['sender'],
		'message': data['message']
	}

	chats = doctor.get_chats(patient)

	print('CHATS:', len(chats.chats))
	if(not chats): 
		print("No Chat")
		return jsonify({'status': 0})

	chats.add_chat(payload)
	db.session.commit()
	return jsonify({'status': 200})


