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
        check_interval = 0.1  # Check more frequently for better responsiveness
        
        while self.running:
            try:
                # Try to read the tag
                tag_id, _ = self.reader.read_no_block()
                
                if tag_id:
                    # Convert tag_id to string for consistency
                    tag_id = str(tag_id)
                    
                    # New tag detected or same tag still present
                    if last_tag_id != tag_id:
                        # It's a new tag
                        logger.debug(f"New RFID tag detected: {tag_id}")
                        
                        # If we had a previous tag, send 'absent' for it first
                        if last_tag_id and self.callback:
                            self.callback(last_tag_id, 'absent')
                            logger.info(f"Previous RFID tag removed: {last_tag_id}")
                        
                        # Now handle the new tag
                        last_tag_id = tag_id
                        tag_missing_count = 0
                        self.current_tag = tag_id
                        if self.callback:
                            self.callback(tag_id, 'present')
                        logger.info(f"RFID tag detected: {tag_id}")
                    else:
                        # Same tag still present, reset missing count
                        tag_missing_count = 0
                        logger.debug(f"RFID tag still present: {tag_id}")
                else:
                    # No tag detected
                    tag_missing_count += 1
                    logger.debug(f"No tag detected, missing count: {tag_missing_count}")
                    
                    # Only consider the tag missing after several consecutive failed reads
                    # This helps with brief read errors - but don't wait too long
                    if tag_missing_count >= 2 and last_tag_id:  # Reduced from 3 to 2 for faster response
                        if self.callback:
                            self.callback(last_tag_id, 'absent')
                        logger.info(f"RFID tag removed: {last_tag_id}")
                        last_tag_id = None
                        self.current_tag = None
                        tag_missing_count = 0
                
                # Sleep to prevent 100% CPU usage - but check more frequently
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in RFID detection loop: {e}")
                time.sleep(0.5)  # Wait a bit on errors, but not too long
    
    def _simulation_loop(self):
        """
        Simulation loop for testing without actual hardware
        In real deployment, this would be replaced by actual RFID reading
        """
        logger.info("Starting RFID simulation mode")
        
        # In simulation mode, use multiple simulated tags with faster cycling
        simulated_tags = ["12345678", "87654321", "11223344", "55667788", "99001122"]
        current_index = 0
        tag_present = False
        tag_detected_time = 0
        check_interval = 0.1  # Check much more frequently
        
        while self.running:
            current_time = time.time()
            
            # Toggle tag presence every 2-4 seconds
            if not tag_present and current_time - tag_detected_time > 2:
                # Simulate new tag detection
                current_index = (current_index + 1) % len(simulated_tags)
                tag_id = simulated_tags[current_index]
                self.current_tag = tag_id
                
                if self.callback:
                    self.callback(tag_id, 'present')
                logger.info(f"[SIMULATION] RFID tag detected: {tag_id}")
                tag_present = True
                tag_detected_time = current_time
                
            elif tag_present and current_time - tag_detected_time > 4:
                # Simulate tag removal
                tag_id = simulated_tags[current_index]
                if self.callback:
                    self.callback(tag_id, 'absent')
                logger.info(f"[SIMULATION] RFID tag removed: {tag_id}")
                self.current_tag = None
                tag_present = False
                tag_detected_time = current_time
            
            # Sleep for a short interval to prevent 100% CPU usage
            # but still be very responsive to changes
            time.sleep(check_interval)
    
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