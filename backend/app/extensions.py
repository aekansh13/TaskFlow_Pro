from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_cors import CORS

# Initialized without app — configured later via init_app() in the factory
jwt = JWTManager()
socketio = SocketIO()
cors = CORS()
