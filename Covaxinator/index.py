from CovaxinatorAPI import create_app
from CovaxinatorAPI.config import Config

app = create_app()
config = Config()

connected_doctors = {}

connected_patients = {}


if __name__ == '__main__':
	#Runs on localhost:8080
	# socketio.run(app, debug=not config.PRODUCTION_MODE, host=config.HOST_NAME, port=config.PORT_NUMBER)
	# socketio.run(app)
	app.run(debug=not config.PRODUCTION_MODE, host=config.HOST_NAME, port=config.PORT_NUMBER)
