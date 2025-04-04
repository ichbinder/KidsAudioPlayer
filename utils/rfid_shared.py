"""
Shared RFID Handler

This module provides a shared RFID handler instance that can be used by both
the web application and the RFID service.
"""
import logging
from utils.rfid_handler import RFIDHandler

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a shared RFID handler instance
shared_rfid_handler = RFIDHandler()

def get_rfid_handler():
    """Get the shared RFID handler instance"""
    return shared_rfid_handler 