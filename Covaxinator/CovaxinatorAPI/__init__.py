from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from CovaxinatorAPI.config import Config
from flask_cors import CORS
from flask_socketio import SocketIO

db = SQLAlchemy()
socketio = SocketIO()

def create_app(config_class=Config):
	app = Flask(__name__)
	app.config.from_object(Config)
	db.init_app(app)
	
	cors = CORS(app)
	socketio.init_app(app, cors_allowed_origins="*")
	# 

	#Import all your blueprints
	from CovaxinatorAPI.main.routes import main
	from CovaxinatorAPI.doctor.routes import doctor
	from CovaxinatorAPI.patient.routes import patient
	
	#use the url_prefix arguement if you need prefixes for the routes in the blueprint
	app.register_blueprint(main)
	app.register_blueprint(doctor, url_prefix='/doctor')
	app.register_blueprint(patient, url_prefix='/patient')

	return app

#Helper function to create database file directly from terminal
def create_database():
	import CovaxinatorAPI.models
	print("Creating App & Database")
	app = create_app()
	with app.app_context():
		db.create_all()
		db.session.commit()
	print("Successfully Created Database")


ac = create_app().app_context()