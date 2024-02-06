from CovaxinatorAPI import create_app, socketio
from CovaxinatorAPI.config import Config
from flask_socketio import send, emit

app = create_app()
config = Config()

connected_doctors = {}

connected_patients = {}

@socketio.on('message')
def handle_socketio_message(payload):
	# print(f"Recieved Payload: {payload}")
	if(payload['role'] == 'doctor'):
		connected_doctors[payload['phone']] = payload['socket_id']
		print(f"Doctor {payload['phone']} Connected Via Socket {payload['socket_id']}")
	elif(payload['role'] == 'patient'):
		connected_patients[payload['phone']] = payload['socket_id']
		print(f"Patient {payload['phone']} Connected Via Socket {payload['socket_id']}")
	send("")

@socketio.on('private_message')
def private_message(payload):
	# print(payload)
	emit('private_message',payload, broadcast=True)

if __name__ == '__main__':
	#Runs on localhost:8080
	socketio.run(app, debug=not config.PRODUCTION_MODE, host=config.HOST_NAME, port=config.PORT_NUMBER)
	# socketio.run(app)
	# app.run(debug=not config.PRODUCTION_MODE, host=config.HOST_NAME, port=config.PORT_NUMBER)
