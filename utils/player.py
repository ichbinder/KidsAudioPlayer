"""
MP3 Player functionality
"""
import os
import subprocess
import logging
from app import MUSIC_DIR

logger = logging.getLogger(__name__)

# Global variable to store the current playback process
current_process = None

def start_playback(filename):
    """Start playing an MP3 file"""
    global current_process
    
    try:
        # Stop any existing playback
        stop_playback()
        
        # Get the full path to the MP3 file
        file_path = os.path.join(MUSIC_DIR, filename)
        
        if not os.path.exists(file_path):
            logger.error(f"MP3 file not found: {file_path}")
            return False
            
        # Start playback using mpg123 with audio output to 3.5mm jack
        current_process = subprocess.Popen(
            ['mpg123', '-a', 'hw:0,0', file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        logger.info(f"Started playback of {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error starting playback: {e}")
        return False

def stop_playback():
    """Stop the current playback"""
    global current_process
    
    if current_process:
        try:
            current_process.terminate()
            current_process.wait(timeout=1)
            logger.info("Playback stopped")
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
        finally:
            current_process = None 