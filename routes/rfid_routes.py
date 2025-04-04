"""
Routes for RFID tag management
"""
import logging
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from controllers.rfid_controller import RFIDController
from models import Song, db, RFIDTag
from utils.rfid_shared import get_rfid_handler

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

@rfid_bp.route('/simulate', methods=['POST'])
def simulate_tag():
    """Simulate an RFID tag for testing (only works in simulation mode)"""
    import os
    
    tag_id = request.form.get('tag_id')
    action = request.form.get('action', 'present')  # Default action is to simulate tag present
    
    if not tag_id and action == 'present':
        logger.error("Tag ID is required for simulation")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"error": "Tag ID is required"}), 400
        flash('Tag-ID ist erforderlich für die Simulation', 'error')
        return redirect(url_for('rfid.rfid_management'))
    
    # For simulation, write to a temporary file to trigger the tag detection
    simulation_file = '/tmp/rfid_simulation.txt'
    
    try:
        if action == 'present':
            # Simulate tag present
            with open(simulation_file, 'w') as f:
                f.write(tag_id)
            logger.info(f"Simulating RFID tag present: {tag_id}")
            message = f"Tag {tag_id} simuliert"
        else:
            # Simulate tag absent
            with open(simulation_file, 'w') as f:
                f.write('No tag')
            logger.info("Simulating RFID tag absent")
            message = "Tag-Entfernung simuliert"
        
        # For AJAX requests, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": True, "message": message})
            
        # For form submissions, redirect back to management page
        flash(message, 'success')
        return redirect(url_for('rfid.rfid_management'))
        
    except Exception as e:
        logger.error(f"Error simulating RFID tag: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"error": f"Fehler bei der Simulation: {e}"}), 500
        flash(f'Fehler bei der Simulation: {e}', 'error')
        return redirect(url_for('rfid.rfid_management'))

@rfid_bp.route('/test', methods=['GET'])
def test_rfid_reader():
    """Test page for direct RFID reader testing"""
    from utils.rfid_handler import RASPBERRY_PI
    
    # Check if we're running on a Raspberry Pi with RFID hardware
    has_rfid_hardware = RASPBERRY_PI
    
    return render_template('rfid_test.html', has_rfid_hardware=has_rfid_hardware)

@rfid_bp.route('/test/read', methods=['POST'])
def test_rfid_read():
    """Endpoint to directly read from RFID reader for testing"""
    from utils.rfid_handler import RASPBERRY_PI
    import time
    import json
    
    # Only allow this on Raspberry Pi
    if not RASPBERRY_PI:
        return jsonify({
            "success": False, 
            "error": "Diese Funktion ist nur auf dem Raspberry Pi mit RFID-Hardware verfügbar."
        }), 400
    
    try:
        # Import hardware libraries
        from mfrc522 import SimpleMFRC522
        import RPi.GPIO as GPIO
        
        # Initialize reader
        reader = SimpleMFRC522()
        
        # Read with timeout
        print("[TEST] Direct RFID read test started")
        timeout = 5  # 5 seconds timeout
        start_time = time.time()
        tag_id = None
        text = ""
        
        # Try non-blocking reads with timeout
        while time.time() - start_time < timeout and not tag_id:
            try:
                tag_id, text = reader.read_no_block()
                if tag_id:
                    break
                time.sleep(0.1)
            except Exception as e:
                print(f"[TEST] Error during read_no_block: {e}")
        
        # If we didn't find a tag with non-blocking, try one blocking read
        if not tag_id and time.time() - start_time < timeout:
            print("[TEST] Trying blocking read...")
            try:
                tag_id, text = reader.read()
            except Exception as e:
                print(f"[TEST] Error during blocking read: {e}")
        
        # Clean up
        try:
            GPIO.cleanup()
        except:
            pass
        
        # Process results
        if tag_id:
            tag_id = str(tag_id)
            text = text.strip() if text else ""
            print(f"[TEST] Tag detected! ID: {tag_id}, Text: {text}")
            return jsonify({
                "success": True,
                "tag_id": tag_id,
                "text": text
            })
        else:
            print("[TEST] No tag detected within timeout period")
            return jsonify({
                "success": False,
                "error": "Kein RFID-Tag innerhalb der Zeitbeschränkung erkannt. Bitte halten Sie einen Tag an den Leser und versuchen Sie es erneut."
            })
            
    except ImportError as e:
        print(f"[TEST] Import error: {e}")
        return jsonify({
            "success": False,
            "error": f"Fehler beim Importieren der RFID-Bibliotheken: {e}"
        }), 500
    except Exception as e:
        print(f"[TEST] General error: {e}")
        return jsonify({
            "success": False,
            "error": f"Fehler beim Lesen des RFID-Tags: {e}"
        }), 500

@rfid_bp.route('/rfid/scan', methods=['GET'])
def scan_rfid():
    """Scan for an RFID tag"""
    try:
        # Get the shared RFID handler
        rfid_handler = get_rfid_handler()
        
        if not rfid_handler:
            logger.error("RFID handler not initialized")
            return jsonify({"error": "RFID handler not initialized"}), 500
            
        # Try to read a tag
        tag_id, text = rfid_handler.read()
        
        if tag_id:
            # Convert tag_id to string for consistency
            tag_id = str(tag_id)
            
            # Check if tag is already registered
            existing_tag = RFIDTag.query.filter_by(tag_id=tag_id).first()
            
            if existing_tag:
                return jsonify({
                    "tag_id": tag_id,
                    "text": text,
                    "registered": True,
                    "name": existing_tag.name,
                    "song_id": existing_tag.song_id
                })
            else:
                return jsonify({
                    "tag_id": tag_id,
                    "text": text,
                    "registered": False
                })
        else:
            return jsonify({"error": "No tag detected"}), 404
            
    except Exception as e:
        logger.error(f"Error scanning RFID tag: {e}")
        return jsonify({"error": str(e)}), 500

@rfid_bp.route('/rfid/register', methods=['POST'])
def register_rfid():
    """Register a new RFID tag"""
    try:
        data = request.get_json()
        tag_id = data.get('tag_id')
        name = data.get('name')
        song_id = data.get('song_id')
        
        if not all([tag_id, name, song_id]):
            return jsonify({"error": "Missing required fields"}), 400
            
        # Check if tag is already registered
        existing_tag = RFIDTag.query.filter_by(tag_id=tag_id).first()
        if existing_tag:
            return jsonify({"error": "Tag already registered"}), 400
            
        # Check if song exists
        song = Song.query.get(song_id)
        if not song:
            return jsonify({"error": "Song not found"}), 404
            
        # Create new tag
        new_tag = RFIDTag(tag_id=tag_id, name=name, song_id=song_id)
        db.session.add(new_tag)
        db.session.commit()
        
        return jsonify({
            "message": "Tag registered successfully",
            "tag": {
                "id": new_tag.id,
                "tag_id": new_tag.tag_id,
                "name": new_tag.name,
                "song_id": new_tag.song_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error registering RFID tag: {e}")
        return jsonify({"error": str(e)}), 500

@rfid_bp.route('/rfid/tags', methods=['GET'])
def get_tags():
    """Get all registered RFID tags"""
    try:
        tags = RFIDTag.query.all()
        return jsonify([{
            "id": tag.id,
            "tag_id": tag.tag_id,
            "name": tag.name,
            "song_id": tag.song_id,
            "song": {
                "id": tag.song.id,
                "title": tag.song.title,
                "filename": tag.song.filename
            } if tag.song else None
        } for tag in tags])
        
    except Exception as e:
        logger.error(f"Error getting RFID tags: {e}")
        return jsonify({"error": str(e)}), 500

@rfid_bp.route('/rfid/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    """Delete a registered RFID tag"""
    try:
        tag = RFIDTag.query.get(tag_id)
        if not tag:
            return jsonify({"error": "Tag not found"}), 404
            
        db.session.delete(tag)
        db.session.commit()
        
        return jsonify({"message": "Tag deleted successfully"})
        
    except Exception as e:
        logger.error(f"Error deleting RFID tag: {e}")
        return jsonify({"error": str(e)}), 500