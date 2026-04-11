import os
from flask import send_from_directory
from app import create_app
from app.extensions import socketio
from dotenv import load_dotenv
load_dotenv()  # This loads the .env file!

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

# -----------------------------------------------------------------------
# Serve the frontend/  directory from Flask so there's zero CORS overhead.
# Everything runs on the same origin: http://127.0.0.1:5000
# -----------------------------------------------------------------------
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))


@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve any file from the frontend directory (HTML, CSS, JS, assets)."""
    # Try to serve the exact file; fall back to index.html for SPA routing
    full_path = os.path.join(FRONTEND_DIR, filename)
    if os.path.isfile(full_path):
        return send_from_directory(FRONTEND_DIR, filename)
    return send_from_directory(FRONTEND_DIR, 'index.html')


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
