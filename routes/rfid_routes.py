"""
Routes for RFID tag management
"""
import logging
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from controllers.rfid_controller import RFIDController
from models import RFIDTag, db
from utils.rfid_shared import get_rfid_handler
import os

logger = logging.getLogger(__name__)

# Create blueprint
rfid_bp = Blueprint('rfid', __name__, url_prefix='/rfid')

@rfid_bp.route('/')
def rfid_management():
    """RFID tag management page"""
    # Get all available MP3 files from the music directory
    from utils.file_handler import get_mp3_files
    from config import MUSIC_DIR
    
    # Get all tags and MP3 files for the template
    tags = RFIDController.get_all_tags()
    mp3_files = get_mp3_files(MUSIC_DIR)
    
    return render_template('rfid_management.html', tags=tags, mp3_files=mp3_files)

@rfid_bp.route('/rfid/register', methods=['POST'])
def register_rfid():
    """Register a new RFID tag"""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ['tag_id', 'name', 'mp3_filename']):
            return jsonify({'error': 'Missing required fields'}), 400
            
        tag_id = data['tag_id']
        name = data['name']
        mp3_filename = data['mp3_filename']
        
        # Check if tag already exists
        existing_tag = RFIDTag.query.filter_by(tag_id=tag_id).first()
        if existing_tag:
            return jsonify({'error': 'Tag already registered'}), 400
            
        # Create new tag
        new_tag = RFIDTag(
            tag_id=tag_id,
            name=name,
            mp3_filename=mp3_filename
        )
        
        db.session.add(new_tag)
        db.session.commit()
        
        return jsonify({
            'message': 'Tag registered successfully',
            'tag': {
                'id': new_tag.id,
                'tag_id': new_tag.tag_id,
                'name': new_tag.name,
                'mp3_filename': new_tag.mp3_filename
            }
        })
        
    except Exception as e:
        logger.error(f"Error registering RFID tag: {e}")
        return jsonify({'error': str(e)}), 500

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
def scan_rfid():
    """Scan for an RFID tag"""
    try:
        # Get the shared RFID handler
        rfid_handler = get_rfid_handler()
        
        if not rfid_handler:
            logger.error("RFID handler not initialized")
            return jsonify({"error": "RFID handler not initialized"}), 500
            
        # Try to read a tag once
        tag_id, text = rfid_handler.read_once()
        
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
                    "mp3_filename": existing_tag.mp3_filename
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

@rfid_bp.route('/rfid/tags', methods=['GET'])
def get_tags():
    """Get all registered RFID tags"""
    try:
        tags = RFIDTag.query.all()
        return jsonify([{
            "id": tag.id,
            "tag_id": tag.tag_id,
            "name": tag.name,
            "mp3_filename": tag.mp3_filename
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