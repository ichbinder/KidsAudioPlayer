"""
RFID Service

This module runs the RFID reader and player service independently from the web server.
"""
import os
import logging
import time
from utils.rfid_shared import get_rfid_handler
from utils.rfid_player import rfid_player

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the RFID service"""
    try:
        logger.info("Starting RFID service...")
        
        # Get the shared RFID handler
        rfid_handler = get_rfid_handler()
        
        # Initialize the RFID player with the shared handler
        rfid_player.init_handler(rfid_handler)
        
        # Start the RFID player
        rfid_player.start()
        logger.info("RFID player started")
        
        # Keep the service running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Stopping RFID service...")
        rfid_player.stop()
        logger.info("RFID service stopped")
    except Exception as e:
        logger.error(f"Error in RFID service: {e}")
        rfid_player.stop()

if __name__ == "__main__":
    main() 