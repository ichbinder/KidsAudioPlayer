"""
MP3 Player for the Kids Audio Player
"""
import os
import subprocess
import logging
from config import MUSIC_DIR

logger = logging.getLogger(__name__)

# Global variable to store the current playback process
current_process = None

def start_playback(mp3_filename):
    """Start playing an MP3 file"""
    global current_process
    
    # Stop any existing playback
    stop_playback()
    
    if not mp3_filename:
        logger.warning("Keine MP3-Datei angegeben")
        return False
        
    # Construct the full path to the MP3 file
    mp3_path = os.path.join(MUSIC_DIR, mp3_filename)
    
    if not os.path.exists(mp3_path):
        logger.error(f"MP3-Datei nicht gefunden: {mp3_path}")
        return False
    
    try:
        # Start playback with mpg123
        # Use the 3.5mm jack for audio output
        current_process = subprocess.Popen(
            ['mpg123', '-a', 'hw:0,0', mp3_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info(f"Starte Wiedergabe: {mp3_filename}")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Abspielen der MP3: {e}")
        return False

def stop_playback():
    """Stop the current playback"""
    global current_process
    
    if current_process:
        try:
            current_process.terminate()
            current_process.wait(timeout=1)
            logger.info("Wiedergabe gestoppt")
        except Exception as e:
            logger.error(f"Fehler beim Stoppen der Wiedergabe: {e}")
        finally:
            current_process = None

class MP3Player:
    def __init__(self):
        self.process = None
        logger.info("MP3 Player initialized")

    def play(self, filename):
        """Play an MP3 file"""
        try:
            # Stop any currently playing song
            self.stop()
            
            # Get the full path to the MP3 file
            filepath = os.path.join(MUSIC_DIR, filename)
            
            if not os.path.exists(filepath):
                logger.error(f"MP3 file not found: {filepath}")
                return False
            
            # Play the MP3 file using mpg123
            self.process = subprocess.Popen(
                ['mpg123', '-q', filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Playing MP3: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error playing MP3: {e}")
            return False

    def stop(self):
        """Stop the currently playing song"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
                logger.info("MP3 playback stopped")
            except Exception as e:
                logger.error(f"Error stopping MP3 playback: {e}")
            finally:
                self.process = None 