"""
API routes for the MP3 player
"""
import logging
import json
from datetime import datetime
from flask import Blueprint, jsonify, current_app

logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Store for the latest RFID event
latest_rfid_event = {
    "event": None,
    "data": None,
    "timestamp": None
}

# Function to store latest RFID event
def emit_event(event_type, data):
    """
    Store the latest RFID event for polling
    
    Args:
        event_type (str): Type of event ('tag_present', 'tag_absent', etc.)
        data (dict): Data to send with the event
    """
    global latest_rfid_event
    
    latest_rfid_event = {
        "event": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    logger.debug(f"Stored RFID event: {event_type}, data: {data}")

@api_bp.route('/rfid/status')
def rfid_status():
    """Polling endpoint for RFID tag status"""
    # Return the latest RFID event
    if latest_rfid_event["event"] is None:
        return jsonify({
            "status": "waiting",
            "message": "No RFID activity yet"
        })
    
    return jsonify({
        "status": "active",
        "event": latest_rfid_event["event"],
        "data": latest_rfid_event["data"],
        "timestamp": latest_rfid_event["timestamp"]
    })