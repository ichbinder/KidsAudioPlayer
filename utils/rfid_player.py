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
from models import RFIDTag, Song
from db import db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class RFIDPlayer:
    """
    Manages integration between RFID detection and song playback
    """
    def __init__(self):
        self.rfid_handler = None
        self.current_song = None
        self.is_playing = False
        self.process = None
        self.callbacks = []
        self.music_dir = os.environ.get("MUSIC_DIR", os.path.join(os.getcwd(), "mp3s"))
    
    def init_handler(self, handler):
        """Initialize the RFID handler"""
        self.rfid_handler = handler
        if self.rfid_handler:
            self.rfid_handler.register_callback(self._handle_tag_event)
            logger.info("RFID handler initialized and callback registered")
    
    def start(self):
        """Start the RFID player"""
        if not self.rfid_handler:
            logger.error("RFID handler not initialized")
            return
            
        self.rfid_handler.start()
        logger.info("RFID player started")
    
    def stop(self):
        """Stop the RFID player"""
        if self.rfid_handler:
            self.rfid_handler.stop()
        if self.process:
            self.process.terminate()
            self.process = None
        self.is_playing = False
        logger.info("RFID player stopped")
    
    def _handle_tag_event(self, tag_id, status):
        """Handle RFID tag events"""
        try:
            logger.debug(f"RFID event received - Tag: {tag_id}, Status: {status}")
            
            if status == 'present':
                # Get song from database
                tag = RFIDTag.query.filter_by(tag_id=tag_id).first()
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
            
            # Get the full path to the song
            song_path = os.path.join(self.music_dir, song.filename)
            
            if not os.path.exists(song_path):
                logger.error(f"Song file not found: {song_path}")
                return
                
            # Start playback using mpg123 with audio output to 3.5mm jack
            self.process = subprocess.Popen([
                'mpg123',
                '-a', 'hw:0,0',  # Use hardware audio device (3.5mm jack)
                song_path
            ])
            self.current_song = song
            self.is_playing = True
            logger.info(f"Started playing: {song.title}")
            
        except Exception as e:
            logger.error(f"Error starting playback: {e}")
    
    def _stop_playback(self):
        """Stop the current playback"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except Exception as e:
                logger.error(f"Error stopping playback: {e}")
            finally:
                self.process = None
                self.current_song = None
                self.is_playing = False
                logger.info("Playback stopped")
    
    def register_client_callback(self, callback):
        """Register a callback for client notifications"""
        self.callbacks.append(callback)

# Create a global instance
rfid_player = RFIDPlayer()