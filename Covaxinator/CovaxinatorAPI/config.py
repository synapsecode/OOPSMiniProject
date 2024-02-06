import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
	SECRET_KEY = "2Fd6CE5AE30B54AA5D7CED1BA5669824773HHHHH7382474HE1865D2C2D8815CD4"
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.sqlite') #Database path
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	PRODUCTION_MODE = False #This states whether the app runs in DEBUG MODE or not
	PORT_NUMBER = 8080
	HOST_NAME = 'localhost'
	UPLOAD_FOLDER = os.path.join(basedir, 'static', 'UPLOAD')
	ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
