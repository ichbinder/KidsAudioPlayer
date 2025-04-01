"""
Routes for RFID tag management
"""
import logging
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from controllers.rfid_controller import RFIDController
from models import Song, db

logger = logging.getLogger(__name__)

# Create blueprint
rfid_bp = Blueprint('rfid', __name__, url_prefix='/rfid')

@rfid_bp.route('/')
def rfid_management():
    """RFID tag management page"""
    # Get all available songs from mp3 directory
    from utils.file_handler import get_mp3_files
    from app import MUSIC_DIR
    import os
    from sqlalchemy.exc import IntegrityError
    
    # Ensure all MP3 files are in the database
    mp3_files = get_mp3_files(MUSIC_DIR)
    default_playlist_id = 1
    
    # Check if we have a default playlist
    from models import Playlist
    default_playlist = Playlist.query.filter_by(id=default_playlist_id).first()
    if not default_playlist:
        # Create a default playlist
        default_playlist = Playlist(name="Default")
        db.session.add(default_playlist)
        try:
            db.session.commit()
            default_playlist_id = default_playlist.id
            logger.info(f"Created default playlist with ID {default_playlist_id}")
        except Exception as e:
            logger.error(f"Error creating default playlist: {e}")
            db.session.rollback()
            
    # Add any missing songs to the database
    for mp3 in mp3_files:
        # Check if the song already exists in the database
        existing_song = Song.query.filter_by(filename=mp3['filename']).first()
        if not existing_song:
            # Create new song entry
            new_song = Song(
                title=mp3['title'],
                filename=mp3['filename'],
                playlist_id=default_playlist_id
            )
            db.session.add(new_song)
            try:
                db.session.commit()
                logger.info(f"Added song {mp3['title']} to database")
            except IntegrityError:
                logger.error(f"Database integrity error adding song {mp3['title']}")
                db.session.rollback()
            except Exception as e:
                logger.error(f"Error adding song {mp3['title']} to database: {e}")
                db.session.rollback()
    
    # Get all tags and songs for the template
    tags = RFIDController.get_all_tags()
    songs = Song.query.all()
    
    return render_template('rfid_management.html', tags=tags, songs=songs)

@rfid_bp.route('/register', methods=['POST'])
def register_tag():
    """Register a new RFID tag"""
    tag_id = request.form.get('tag_id')
    song_id = request.form.get('song_id')
    name = request.form.get('name')
    
    if not tag_id or not song_id:
        logger.error("Missing tag_id or song_id in register request")
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        song_id = int(song_id)
    except ValueError:
        logger.error(f"Invalid song_id: {song_id}")
        return jsonify({"error": "Invalid song ID"}), 400
    
    tag = RFIDController.register_tag(tag_id, song_id, name)
    
    if not tag:
        return jsonify({"error": "Failed to register tag"}), 500
    
    # For AJAX requests, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"success": True, "tag": {
            "id": tag.id,
            "tag_id": tag.tag_id,
            "name": tag.name,
            "song_id": tag.song_id,
            "song_title": tag.song.title
        }})
    
    # For form submissions, redirect back to management page
    flash('RFID-Tag erfolgreich registriert', 'success')
    return redirect(url_for('rfid.rfid_management'))

@rfid_bp.route('/unregister/<tag_id>', methods=['POST', 'DELETE'])
def unregister_tag(tag_id):
    """Unregister an RFID tag"""
    success = RFIDController.unregister_tag(tag_id)
    
    if not success:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"error": "Failed to unregister tag"}), 404
        flash('Fehler beim Entfernen des RFID-Tags', 'error')
        return redirect(url_for('rfid.rfid_management'))
    
    # For AJAX requests, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"success": True})
    
    # For form submissions, redirect back to management page
    flash('RFID-Tag erfolgreich entfernt', 'success')
    return redirect(url_for('rfid.rfid_management'))

@rfid_bp.route('/scan', methods=['GET'])
def scan_tag():
    """Endpoint to get the currently scanned tag"""
    from utils.rfid_player import rfid_player
    
    if not rfid_player.rfid_handler:
        return jsonify({"error": "RFID handler not initialized"}), 500
    
    tag_id = rfid_player.rfid_handler.get_current_tag()
    
    if not tag_id:
        return jsonify({"detected": False})
    
    # Get tag info from database
    tag = RFIDController.get_tag(tag_id)
    
    if not tag:
        return jsonify({
            "detected": True,
            "registered": False,
            "tag_id": tag_id
        })
    
    return jsonify({
        "detected": True,
        "registered": True,
        "tag_id": tag_id,
        "name": tag.name,
        "song": {
            "id": tag.song.id,
            "title": tag.song.title,
            "filename": tag.song.filename
        }
    })