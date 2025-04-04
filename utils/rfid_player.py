"""
RFID Player Integration

This module combines the RFID handler with the MP3 player functionality.
It manages the playback of songs based on RFID tag detection.
"""
import logging
import threading
import time
import os
import subprocess
from datetime import datetime
try:
    from flask import current_app
except ImportError:
    # For development without Flask
    current_app = None

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
        self.current_process = None
        self.music_dir = os.environ.get("MUSIC_DIR", os.path.join(os.getcwd(), "mp3s"))
        self.is_playing = False
        self.callbacks = []
        
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
    
    def init_handler(self, handler):
        """Initialize the RFID handler"""
        self.rfid_handler = handler
        if self.rfid_handler:
            self.rfid_handler.register_callback(self._handle_tag_event)
            logger.info("RFID handler initialized and callback registered")
    
    def start(self):
        """Start the RFID player service"""
        if self.running:
            logger.warning("RFID player already running")
            return
        
        self.running = True
        
        # Initialize and start the RFID handler
        self.rfid_handler.start()
        
        logger.info("RFID player service started")
    
    def stop(self):
        """Stop the RFID player service"""
        if not self.running:
            return
            
        self.running = False
        
        # Stop any playing song
        self._stop_playback()
        
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
        try:
            logger.debug(f"RFID event received - Tag: {tag_id}, Status: {status}")
            
            if status == 'present':
                # Get song from database
                from models import RFIDTag
                from db import db
                
                with db.session() as session:
                    tag = session.query(RFIDTag).filter_by(tag_id=tag_id).first()
                    if tag and tag.song:
                        self._start_playback(tag.song)
                        # Notify clients
                        for callback in self.callbacks:
                            callback('play', {
                                'tag_id': tag_id,
                                'name': tag.name,
                                'song_id': tag.song.id,
                                'filename': tag.song.filename,
                                'title': tag.song.title
                            })
            elif status == 'absent':
                self._stop_playback()
                # Notify clients
                for callback in self.callbacks:
                    callback('pause', {'tag_id': tag_id})
                    
        except Exception as e:
            logger.error(f"Error handling tag event: {e}")
    
    def _start_playback(self, song):
        """Start playing a song"""
        try:
            # Stop any currently playing song
            self._stop_playback()
            
            # Get full path to song
            song_path = os.path.join(self.music_dir, song.filename)
            if not os.path.exists(song_path):
                logger.error(f"Song file not found: {song_path}")
                return
            
            # Start playback using mpg123
            self.current_process = subprocess.Popen(
                ['mpg123', song_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.current_song = song
            self.is_playing = True
            logger.info(f"Started playing: {song.title}")
            
        except Exception as e:
            logger.error(f"Error starting playback: {e}")
    
    def _stop_playback(self):
        """Stop the current playback"""
        if self.current_process:
            try:
                logger.info("Stopping playback")
                self.current_process.terminate()
                self.current_process.wait(timeout=1)
            except Exception as e:
                logger.error(f"Error stopping playback: {e}")
            finally:
                self.current_process = None
                self.current_song = None
                self.is_playing = False
    
    def register_client_callback(self, callback):
        """
        Register a callback function to be called when playback state changes
        
        Args:
            callback (callable): Function that accepts action and data
        """
        self.callbacks.append(callback)

# Singleton instance
rfid_player = RFIDPlayer()