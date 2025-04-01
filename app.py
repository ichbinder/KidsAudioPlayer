import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, send_file, request
from utils.file_handler import get_mp3_files, get_file_path
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

@app.route('/')
def index():
    """Render the main page of the MP3 player."""
    return render_template('index.html')

@app.route('/api/songs')
def get_songs():
    """Get list of MP3 files from the music directory."""
    try:
        songs = get_mp3_files(MUSIC_DIR)
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

# Playlist Routes
@app.route('/api/playlists', methods=['GET'])
def get_playlists():
    """Get all playlists."""
    try:
        playlists = models.Playlist.query.all()
        return jsonify([playlist.to_dict() for playlist in playlists])
    except Exception as e:
        logger.error(f"Error getting playlists: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/playlists', methods=['POST'])
def create_playlist():
    """Create a new playlist."""
    try:
        data = request.json
        if not data or 'name' not in data:
            return jsonify({"error": "Name is required"}), 400
        
        playlist = models.Playlist(name=data['name'])
        db.session.add(playlist)
        db.session.commit()
        return jsonify(playlist.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating playlist: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/playlists/<int:playlist_id>', methods=['GET'])
def get_playlist(playlist_id):
    """Get a specific playlist."""
    try:
        playlist = models.Playlist.query.get(playlist_id)
        if not playlist:
            return jsonify({"error": "Playlist not found"}), 404
        return jsonify(playlist.to_dict())
    except Exception as e:
        logger.error(f"Error getting playlist {playlist_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/playlists/<int:playlist_id>/songs', methods=['POST'])
def add_song_to_playlist(playlist_id):
    """Add a song to a playlist."""
    try:
        playlist = models.Playlist.query.get(playlist_id)
        if not playlist:
            return jsonify({"error": "Playlist not found"}), 404
        
        data = request.json
        if not data or 'title' not in data or 'filename' not in data:
            return jsonify({"error": "Title and filename are required"}), 400
        
        # Get highest order value for songs in this playlist
        max_order = db.session.query(db.func.max(models.Song.order)).filter_by(playlist_id=playlist_id).scalar() or 0
        
        song = models.Song(
            title=data['title'],
            filename=data['filename'],
            order=max_order + 1,
            playlist_id=playlist_id
        )
        db.session.add(song)
        db.session.commit()
        return jsonify(song.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding song to playlist {playlist_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/playlists/<int:playlist_id>/songs/<int:song_id>', methods=['DELETE'])
def remove_song_from_playlist(playlist_id, song_id):
    """Remove a song from a playlist."""
    try:
        song = models.Song.query.filter_by(id=song_id, playlist_id=playlist_id).first()
        if not song:
            return jsonify({"error": "Song not found in this playlist"}), 404
        
        # Remember the song's order
        removed_order = song.order
        
        # Delete the song
        db.session.delete(song)
        
        # Reorder remaining songs to maintain sequence
        for s in models.Song.query.filter(
            models.Song.playlist_id == playlist_id,
            models.Song.order > removed_order
        ).all():
            s.order -= 1
        
        db.session.commit()
        return jsonify({"message": "Song removed from playlist"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing song {song_id} from playlist {playlist_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/playlists/<int:playlist_id>/songs/reorder', methods=['PUT'])
def reorder_songs(playlist_id):
    """Reorder songs in a playlist."""
    try:
        playlist = models.Playlist.query.get(playlist_id)
        if not playlist:
            return jsonify({"error": "Playlist not found"}), 404
        
        data = request.json
        if not data or 'songs' not in data or not isinstance(data['songs'], list):
            return jsonify({"error": "Song order list is required"}), 400
        
        # Expected format: {"songs": [{"id": 1, "order": 3}, {"id": 2, "order": 1}, ...]}
        song_dict = {song.id: song for song in playlist.songs}
        
        # Update song orders
        for song_data in data['songs']:
            if 'id' in song_data and 'order' in song_data:
                song_id = song_data['id']
                if song_id in song_dict:
                    song_dict[song_id].order = song_data['order']
        
        db.session.commit()
        return jsonify(playlist.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error reordering songs in playlist {playlist_id}: {e}")
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
