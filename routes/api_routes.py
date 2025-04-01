"""
API routes for the MP3 player
"""
import logging
import json
import time
import threading
from queue import Queue, Empty
from datetime import datetime
from flask import Blueprint, Response, stream_with_context, current_app, g

logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Queue for SSE events
event_queue = Queue()

# Function to emit events to all connected clients
def emit_event(event_type, data):
    """
    Emit an event to all connected SSE clients
    
    Args:
        event_type (str): Type of event ('tag_present', 'tag_absent', etc.)
        data (dict): Data to send with the event
    """
    event_data = {
        "event": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    event_queue.put(event_data)
    logger.debug(f"Emitted event: {event_type}, data: {data}")

@api_bp.route('/rfid/events')
def rfid_events():
    """Server-Sent Events (SSE) endpoint for RFID tag events"""
    def event_stream():
        # Create a client-specific queue
        client_queue = Queue()
        
        # Function to forward events from main queue to client queue
        def forward_events():
            while True:
                try:
                    # Get event from main queue
                    event = event_queue.get(block=True, timeout=None)
                    # Forward to client queue
                    client_queue.put(event)
                    # Mark as done
                    event_queue.task_done()
                except Exception as e:
                    logger.error(f"Error forwarding events: {e}")
                    break
        
        # Start forwarding thread
        forward_thread = threading.Thread(target=forward_events, daemon=True)
        forward_thread.start()
        
        # Send initial connection established event
        yield 'event: connection_established\ndata: {"message": "Connected to RFID events"}\n\n'
        
        # Send events as they come in
        try:
            while True:
                try:
                    # Try to get event with timeout
                    event = client_queue.get(block=True, timeout=30)
                    
                    # Format the event for SSE
                    event_type = event['event']
                    data = json.dumps(event['data'])
                    
                    yield f'event: {event_type}\ndata: {data}\n\n'
                    
                    # Mark as done
                    client_queue.task_done()
                    
                except Empty:
                    # No events for 30 seconds, send keepalive
                    yield ': keepalive\n\n'
                    
        except GeneratorExit:
            # Client disconnected
            logger.info("Client disconnected from RFID events")
        except Exception as e:
            logger.error(f"Error in event stream: {e}")
    
    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable proxy buffering
        }
    )