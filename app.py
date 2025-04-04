"""
Main application module for the Kids Audio Player
"""
import os
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from routes.rfid_routes import rfid_bp
from models import db
import logging
import threading
import time
from utils.rfid_shared import get_rfid_handler
from utils.player import MP3Player, start_playback, stop_playback
from config import MUSIC_DIR

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

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

# Global variables for RFID scanning
scanning = False
current_tag = None

# Initialize MP3 player
player = MP3Player()

# Initialize RFID handler
rfid_handler = get_rfid_handler()

def tag_callback(tag_id, status):
    """Callback function for RFID tag events"""
    if status == 'present':
        # Get tag from database
        from models import db, RFIDTag
        with app.app_context():
            tag = RFIDTag.query.filter_by(tag_id=tag_id).first()
            if tag:
                # Play the associated MP3
                player.play(tag.mp3_filename)
                socketio.emit('song_playing', {'title': tag.name})
    elif status == 'absent':
        # Stop playback when tag is removed
        player.stop()
        socketio.emit('tag_removed')

# Register callback with RFID handler
rfid_handler.register_callback(tag_callback)

def start_rfid_scan():
    """Start continuous RFID scanning"""
    global scanning, current_tag
    
    if scanning:
        return
        
    scanning = True
    logger.info("Starte RFID-Scanning...")
    
    try:
        while scanning:
            # Get the shared RFID handler
            rfid_handler = get_rfid_handler()
            
            if not rfid_handler:
                logger.error("RFID handler not initialized")
                time.sleep(1)
                continue
                
            # Try to read a tag
            tag_id, text = rfid_handler.read_once()
            
            if tag_id:
                if tag_id != current_tag:
                    # New tag detected
                    logger.debug(f"Neuer Tag erkannt: {tag_id}")
                    current_tag = tag_id
                    
                    # Emit tag detected event
                    socketio.emit('tag_detected', {
                        'tag_id': tag_id,
                        'text': text
                    })
                    
                    # Check if tag is registered and play song
                    with app.app_context():
                        from models import RFIDTag
                        tag = RFIDTag.query.filter_by(tag_id=tag_id).first()
                        if tag and tag.mp3_filename:
                            # Start playback
                            if start_playback(tag.mp3_filename):
                                socketio.emit('song_playing', {
                                    'title': tag.name,
                                    'filename': tag.mp3_filename
                                })
                            else:
                                logger.error(f"Konnte MP3 nicht abspielen: {tag.mp3_filename}")
                        else:
                            logger.info(f"Tag {tag_id} nicht registriert oder keine MP3-Datei verknüpft")
            else:
                if current_tag:
                    # Tag removed
                    logger.debug(f"Tag entfernt: {current_tag}")
                    socketio.emit('tag_removed', {'tag_id': current_tag})
                    current_tag = None
                    stop_playback()
                    
            # Small delay to prevent CPU overload
            time.sleep(0.1)
            
    except Exception as e:
        logger.error(f"Fehler beim RFID-Scanning: {e}")
    finally:
        scanning = False
        current_tag = None

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

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info("Client connected")
    if not scanning:
        # Start RFID scanning in a separate thread
        threading.Thread(target=start_rfid_scan, daemon=True).start()

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info("Client disconnected")

if __name__ == '__main__':
    # Start RFID handler
    rfid_handler.start()
    
    # Run Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
