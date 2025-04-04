"""
MP3 Player for the Kids Audio Player
"""
import os
import subprocess
import logging
from config import MUSIC_DIR

logger = logging.getLogger(__name__)

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