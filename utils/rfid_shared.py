"""
Shared RFID handler instance for the application
"""
from utils.rfid_handler import RFIDHandler

# Create a single instance of the RFID handler
_rfid_handler = None

def get_rfid_handler():
    """Get the shared RFID handler instance"""
    global _rfid_handler
    if _rfid_handler is None:
        _rfid_handler = RFIDHandler()
    return _rfid_handler 