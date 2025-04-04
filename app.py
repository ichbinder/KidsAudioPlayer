import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, send_file, request
from utils.file_handler import get_mp3_files, get_file_path
from utils.rfid_shared import get_rfid_handler
from db import db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configure database
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    logger.info("Database configuration set with URL from environment")
else:
    logger.warning("DATABASE_URL not found in environment")
    # Fallback for development - use SQLite
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kid_music_player.db"
    logger.info("Using SQLite database as fallback")

# Initialize database with app
db.init_app(app)

# Import models and create tables
with app.app_context():
    import models
    db.create_all()
    logger.info("Database tables created")

# Define the MP3s directory - use the 'mp3s' folder in the project directory
MUSIC_DIR = os.environ.get("MUSIC_DIR", os.path.join(os.getcwd(), "mp3s"))
if not os.path.exists(MUSIC_DIR):
    try:
        os.makedirs(MUSIC_DIR)
        logger.info(f"Created MP3s directory at {MUSIC_DIR}")
    except Exception as e:
        logger.error(f"Failed to create MP3s directory: {e}")

# Get the shared RFID handler
rfid_handler = get_rfid_handler()

# Register blueprints
from routes.rfid_routes import rfid_bp
from routes.api_routes import api_bp, emit_event

# Initialize RFID routes with the shared handler
rfid_bp.rfid_handler = rfid_handler
app.register_blueprint(rfid_bp)
app.register_blueprint(api_bp)

@app.route('/')
def index():
    """Render the main page of the MP3 player."""
    return render_template('index.html')

@app.route('/api/songs')
def get_songs():
    """Get list of MP3 files from the music directory."""
    try:
        songs = get_mp3_files(MUSIC_DIR)
        
        # Add database IDs to songs if they exist in the database
        from models import Song
        for song in songs:
            db_song = Song.query.filter_by(filename=song['filename']).first()
            if db_song:
                song['id'] = db_song.id
        
        return jsonify(songs)
    except Exception as e:
        logger.error(f"Error getting songs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/play/<path:filename>')
def play_song(filename):
    """Stream an MP3 file for playback."""
    try:
        file_path = get_file_path(MUSIC_DIR, filename)
        return send_file(file_path, mimetype="audio/mpeg")
    except Exception as e:
        logger.error(f"Error playing song {filename}: {e}")
        return jsonify({"error": str(e)}), 404

@app.route('/api/cover/<path:filename>')
def get_cover_image(filename):
    """Get cover image for a song."""
    try:
        file_path = get_file_path(MUSIC_DIR, filename)
        # Determine the appropriate mimetype
        mimetype = None
        if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            mimetype = 'image/jpeg'
        elif filename.lower().endswith('.png'):
            mimetype = 'image/png'
        elif filename.lower().endswith('.gif'):
            mimetype = 'image/gif'
        elif filename.lower().endswith('.bmp'):
            mimetype = 'image/bmp'
        elif filename.lower().endswith('.webp'):
            mimetype = 'image/webp'
        else:
            mimetype = 'image/jpeg'  # Default
            
        return send_file(file_path, mimetype=mimetype)
    except Exception as e:
        logger.error(f"Error getting cover image {filename}: {e}")
        return jsonify({"error": str(e)}), 404

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error"}), 500

if __name__ == '__main__':
    # Run the Flask app without debug mode
    app.run(host="0.0.0.0", port=5000, debug=False)
