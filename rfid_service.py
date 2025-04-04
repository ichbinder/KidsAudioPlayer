"""
RFID Service

This module runs the RFID reader service independently from the web application.
"""
import os
import logging
import time
from app import app
from utils.rfid_shared import get_rfid_handler
from utils.player import start_playback, stop_playback
from models import RFIDTag, Song, db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the RFID service"""
    try:
        logger.info("[INIT] Starting RFID service")
        
        # Get the shared RFID handler
        rfid_handler = get_rfid_handler()
        if not rfid_handler:
            logger.error("Failed to initialize RFID handler")
            return
            
        logger.info("[INIT] RFID reader initialized successfully")
        
        # Start continuous scanning
        current_tag = None
        
        while True:
            try:
                # Try to read a tag
                tag_id, text = rfid_handler.read_once()
                
                if tag_id:
                    # Convert tag_id to string for consistency
                    tag_id = str(tag_id)
                    
                    # Check if this is a new tag
                    if tag_id != current_tag:
                        logger.debug(f"[DEBUG] RFID: Neuer Tag erkannt: {tag_id}")
                        current_tag = tag_id
                        
                        # Get tag info from database
                        with app.app_context():
                            tag = RFIDTag.query.filter_by(tag_id=tag_id).first()
                            if tag:
                                # Get the associated song
                                song = Song.query.get(tag.song_id)
                                if song:
                                    # Start playback
                                    start_playback(song.filename)
                                    logger.info(f"Playing song: {song.title}")
                                else:
                                    logger.error(f"No song found for tag {tag_id}")
                            else:
                                logger.debug(f"Tag {tag_id} not registered")
                                
                else:
                    # No tag detected
                    if current_tag:
                        logger.debug(f"[RFID REMOVAL] Tag {current_tag} has been removed")
                        current_tag = None
                        
                        # Stop playback
                        stop_playback()
                        
                # Small delay to prevent CPU overload
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in RFID service: {e}")
                time.sleep(1)  # Wait a bit longer on error
                
    except KeyboardInterrupt:
        logger.info("[SHUTDOWN] RFID service stopped by user")
    except Exception as e:
        logger.error(f"[ERROR] RFID service stopped due to error: {e}")
    finally:
        # Clean up
        try:
            rfid_handler.cleanup()
        except:
            pass
        logger.info("[SHUTDOWN] RFID service cleanup completed")

if __name__ == '__main__':
    main() 