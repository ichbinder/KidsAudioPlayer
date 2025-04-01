"""
RFID Handler for MP3 Player

This module handles RFID tag detection using RC522 RFID reader.
It's designed to work with Raspberry Pi.
"""
import logging
import threading
import time
from datetime import datetime
from contextlib import contextmanager

# Setup logging
logger = logging.getLogger(__name__)

# Flag to determine if we're running on a Raspberry Pi
try:
    import RPi.GPIO as GPIO
    from mfrc522 import SimpleMFRC522
    RASPBERRY_PI = True
    logger.info("Running on Raspberry Pi, RFID module enabled")
except (ImportError, RuntimeError):
    RASPBERRY_PI = False
    logger.warning("Not running on Raspberry Pi or missing required libraries. RFID functionality will be simulated.")

class RFIDHandler:
    """
    Handler for RFID reader operations
    """
    def __init__(self, callback=None):
        """
        Initialize the RFID handler

        Args:
            callback (callable): Function to call when a tag is detected or removed
                                 Should accept tag_id and status ('present' or 'absent')
        """
        self.callback = callback
        self.reader = None
        self.current_tag = None
        self.running = False
        self.thread = None
        
        # Initialize the RFID reader if we're on a Raspberry Pi
        if RASPBERRY_PI:
            try:
                self.reader = SimpleMFRC522()
                logger.info("RFID reader initialized")
            except Exception as e:
                logger.error(f"Failed to initialize RFID reader: {e}")
                self.reader = None
    
    def start(self):
        """Start the RFID detection thread"""
        if self.running:
            logger.warning("RFID handler already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.thread.start()
        logger.info("RFID detection started")
    
    def stop(self):
        """Stop the RFID detection thread"""
        if not self.running:
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("RFID detection stopped")
        
        # Clean up GPIO on shutdown if we're on a Raspberry Pi
        if RASPBERRY_PI:
            GPIO.cleanup()
    
    def _detection_loop(self):
        """Main detection loop, runs in a separate thread"""
        if not self.reader and not RASPBERRY_PI:
            # In simulation mode
            self._simulation_loop()
            return
            
        if not self.reader:
            logger.error("RFID reader not initialized, detection loop aborted")
            return
            
        last_tag_id = None
        tag_missing_count = 0
        
        while self.running:
            try:
                # Try to read the tag
                tag_id, _ = self.reader.read_no_block()
                
                if tag_id:
                    # Convert tag_id to string for consistency
                    tag_id = str(tag_id)
                    
                    # New tag detected
                    if last_tag_id != tag_id:
                        last_tag_id = tag_id
                        tag_missing_count = 0
                        self.current_tag = tag_id
                        if self.callback:
                            self.callback(tag_id, 'present')
                        logger.info(f"RFID tag detected: {tag_id}")
                else:
                    # No tag detected
                    tag_missing_count += 1
                    
                    # Only consider the tag missing after several consecutive failed reads
                    # This helps with brief read errors
                    if tag_missing_count > 3 and last_tag_id:
                        if self.callback:
                            self.callback(last_tag_id, 'absent')
                        logger.info(f"RFID tag removed: {last_tag_id}")
                        last_tag_id = None
                        self.current_tag = None
                        tag_missing_count = 0
                
                # Sleep to prevent 100% CPU usage
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error in RFID detection loop: {e}")
                time.sleep(1)  # Wait a bit longer on errors
    
    def _simulation_loop(self):
        """
        Simulation loop for testing without actual hardware
        In real deployment, this would be replaced by actual RFID reading
        """
        logger.info("Starting RFID simulation mode")
        
        # In simulation mode, we'll just toggle between simulated tags every 10 seconds
        simulated_tags = ["12345678", "87654321"]
        current_index = 0
        
        while self.running:
            # Simulate tag detection
            tag_id = simulated_tags[current_index]
            self.current_tag = tag_id
            
            if self.callback:
                self.callback(tag_id, 'present')
            logger.info(f"[SIMULATION] RFID tag detected: {tag_id}")
            
            # Wait for 10 seconds
            for _ in range(50):  # 10 seconds in 0.2s increments
                if not self.running:
                    break
                time.sleep(0.2)
            
            if not self.running:
                break
                
            # Simulate tag removal
            if self.callback:
                self.callback(tag_id, 'absent')
            logger.info(f"[SIMULATION] RFID tag removed: {tag_id}")
            self.current_tag = None
            
            # Switch to the next tag
            current_index = (current_index + 1) % len(simulated_tags)
            
            # Wait for 5 seconds before the next tag
            for _ in range(25):  # 5 seconds in 0.2s increments
                if not self.running:
                    break
                time.sleep(0.2)
    
    def get_current_tag(self):
        """Get the currently detected tag ID"""
        return self.current_tag

@contextmanager
def rfid_manager(callback=None):
    """
    Context manager for RFID handler to ensure proper cleanup
    
    Usage:
        with rfid_manager(callback_function) as handler:
            # Do something with handler
    """
    handler = RFIDHandler(callback)
    handler.start()
    try:
        yield handler
    finally:
        handler.stop()