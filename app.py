"""
Main application module
"""
import os
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from routes.rfid_routes import rfid_bp
from models import db
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///kids_audio_player.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure MP3 directory
MUSIC_DIR = os.environ.get('MUSIC_DIR', os.path.join(os.getcwd(), 'mp3s'))
if not os.path.exists(MUSIC_DIR):
    os.makedirs(MUSIC_DIR)
    logger.info(f"Created MP3 directory at {MUSIC_DIR}")

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(rfid_bp)

# Create database tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created")

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/songs')
def get_songs():
    """Get list of MP3 files"""
    try:
        songs = []
        for filename in os.listdir(MUSIC_DIR):
            if filename.lower().endswith('.mp3'):
                # Use filename without extension as title
                title = os.path.splitext(filename)[0]
                songs.append({
                    'filename': filename,
                    'title': title
                })
        return jsonify(songs)
    except Exception as e:
        logger.error(f"Error getting songs: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
