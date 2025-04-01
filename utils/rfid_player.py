"""
RFID Player Integration

This module combines the RFID handler with the MP3 player functionality.
It manages the playback of songs based on RFID tag detection.
"""
import logging
import threading
import time
from datetime import datetime
from flask import current_app

from utils.rfid_handler import RFIDHandler
from controllers.rfid_controller import RFIDController

logger = logging.getLogger(__name__)

class RFIDPlayer:
    """
    Manages integration between RFID detection and song playback
    """
    def __init__(self, app=None):
        """
        Initialize the RFID Player
        
        Args:
            app (Flask): Flask application instance
        """
        self.app = app
        self.rfid_handler = None
        self.running = False
        self.current_song = None
        self.client_callback = None
        
        # If app is provided, initialize with it
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize with Flask app
        
        Args:
            app (Flask): Flask application instance
        """
        self.app = app
        
        # Register cleanup function
        @app.teardown_appcontext
        def cleanup(exception=None):
            self.stop()
    
    def start(self):
        """Start the RFID player service"""
        if self.running:
            logger.warning("RFID player already running")
            return
        
        self.running = True
        
        # Initialize and start the RFID handler
        self.rfid_handler = RFIDHandler(callback=self._handle_tag_event)
        self.rfid_handler.start()
        
        logger.info("RFID player service started")
    
    def stop(self):
        """Stop the RFID player service"""
        if not self.running:
            return
            
        self.running = False
        
        # Stop the RFID handler
        if self.rfid_handler:
            self.rfid_handler.stop()
        
        logger.info("RFID player service stopped")
    
    def _handle_tag_event(self, tag_id, status):
        """
        Handle RFID tag events
        
        Args:
            tag_id (str): The ID of the detected/removed tag
            status (str): 'present' or 'absent'
        """
        logger.info(f"RFID event: Tag {tag_id} is {status}")
        
        # We need to wrap DB operations in application context
        with self.app.app_context():
            if status == 'present':
                # Tag placed on reader - start playing associated song
                song = RFIDController.get_song_by_tag(tag_id)
                
                if not song:
                    logger.warning(f"No song associated with tag {tag_id}")
                    return
                
                # Store current song
                self.current_song = song
                
                # Notify clients to play this song
                self._notify_clients('play', {
                    'song_id': song.id,
                    'filename': song.filename,
                    'title': song.title
                })
                
                logger.info(f"Playing song: {song.title}")
                
            elif status == 'absent':
                # Tag removed - pause playback
                self._notify_clients('pause', {})
                logger.info("Pausing playback")
    
    def register_client_callback(self, callback):
        """
        Register a callback function to be called when playback state changes
        
        Args:
            callback (callable): Function that accepts action and data
        """
        self.client_callback = callback
    
    def _notify_clients(self, action, data):
        """
        Notify clients of a playback state change
        
        Args:
            action (str): Action to perform ('play', 'pause', etc.)
            data (dict): Data associated with the action
        """
        if self.client_callback:
            self.client_callback(action, data)

# Singleton instance
rfid_player = RFIDPlayer()