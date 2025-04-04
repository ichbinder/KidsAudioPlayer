"""
Main application module
"""
import os
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from routes.rfid_routes import rfid_bp
from models import db
import logging
import threading
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
socketio = SocketIO(app)

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

def start_rfid_scan():
    """Start continuous RFID scanning"""
    global scanning, current_tag
    from utils.rfid_shared import get_rfid_handler
    from utils.player import start_playback, stop_playback
    from models import RFIDTag, Song
    
    rfid_handler = get_rfid_handler()
    if not rfid_handler:
        logger.error("RFID handler not initialized")
        return
        
    scanning = True
    logger.info("Starting continuous RFID scan")
    
    while scanning:
        try:
            # Try to read a tag
            tag_id, text = rfid_handler.read_once()
            
            if tag_id:
                # Convert tag_id to string for consistency
                tag_id = str(tag_id)
                
                # Check if this is a new tag
                if tag_id != current_tag:
                    logger.debug(f"[DEBUG] RFID: Neuer Tag erkannt: {tag_id}")
                    current_tag = tag_id
                    
                    # Send tag ID to all connected clients
                    socketio.emit('tag_detected', {'tag_id': tag_id})
                    
                    # Check if tag is registered and play song
                    with app.app_context():
                        tag = RFIDTag.query.filter_by(tag_id=tag_id).first()
                        if tag:
                            song = Song.query.get(tag.song_id)
                            if song:
                                start_playback(song.filename)
                                socketio.emit('song_playing', {
                                    'title': song.title,
                                    'filename': song.filename
                                })
                                
            else:
                # No tag detected
                if current_tag:
                    logger.debug(f"[RFID REMOVAL] Tag {current_tag} has been removed")
                    current_tag = None
                    socketio.emit('tag_removed')
                    stop_playback()
                    
            # Small delay to prevent CPU overload
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error in RFID scan: {e}")
            time.sleep(1)
            
    logger.info("RFID scan stopped")

def stop_rfid_scan():
    """Stop continuous RFID scanning"""
    global scanning
    scanning = False
    logger.info("Stopping RFID scan")

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
    if current_tag:
        socketio.emit('tag_detected', {'tag_id': current_tag})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info("Client disconnected")

if __name__ == '__main__':
    # Start RFID scanning in a separate thread
    rfid_thread = threading.Thread(target=start_rfid_scan)
    rfid_thread.daemon = True
    rfid_thread.start()
    
    # Run the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
