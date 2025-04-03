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
        check_interval = 0.05  # Very responsive checking
        use_blocking_read = True  # Flag to switch between blocking and non-blocking reads
        
        while self.running:
            try:
                # Try to read the tag - alternate between blocking and non-blocking
                if not last_tag_id and use_blocking_read:
                    # No tag detected yet, use blocking read to wait for one (with timeout)
                    logger.debug("Using blocking read to wait for tag")
                    tag_read_thread = threading.Thread(target=self._blocking_read)
                    tag_read_thread.daemon = True
                    tag_read_thread.start()
                    
                    # Wait for a short time to see if a tag was detected
                    for _ in range(20):  # 1 second max wait (20 * 0.05)
                        if not self.running:
                            break
                        if self.current_tag:
                            # Tag detected by the blocking read
                            tag_id = self.current_tag
                            break
                        time.sleep(0.05)
                    else:
                        # No tag detected in the timeout period
                        tag_id = None
                else:
                    # Already have a tag or using non-blocking
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
                        
                        # Switch to non-blocking for a while to check for removals
                        use_blocking_read = False
                    else:
                        # Same tag still present, reset missing count
                        tag_missing_count = 0
                        logger.debug(f"RFID tag still present: {tag_id}")
                else:
                    # No tag detected
                    tag_missing_count += 1
                    logger.debug(f"No tag detected, missing count: {tag_missing_count}")
                    
                    # Only consider the tag missing after a few consecutive failed reads
                    if tag_missing_count >= 2 and last_tag_id:  # Very fast response
                        if self.callback:
                            self.callback(last_tag_id, 'absent')
                        logger.info(f"RFID tag removed: {last_tag_id}")
                        last_tag_id = None
                        self.current_tag = None
                        tag_missing_count = 0
                        
                        # Switch back to blocking read to wait for next tag
                        use_blocking_read = True
                
                # Sleep to prevent 100% CPU usage
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in RFID detection loop: {e}")
                time.sleep(0.5)  # Wait a bit on errors
                
    def _blocking_read(self):
        """Perform a blocking read in a separate thread to avoid hanging the main loop"""
        try:
            logger.debug("Starting blocking RFID read")
            tag_id, _ = self.reader.read()
            if tag_id:
                self.current_tag = str(tag_id)
                logger.debug(f"Blocking read detected tag: {self.current_tag}")
            else:
                logger.debug("Blocking read returned no tag")
        except Exception as e:
            logger.error(f"Error in blocking RFID read: {e}")
            self.current_tag = None
    
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
        check_interval = 0.05  # Very responsive checking
        
        # For manual testing via browser interface
        manual_tag_request = None
        last_manual_action_time = 0
        
        try:
            # Create a simulation file to signal tag changes (for manual testing)
            with open('/tmp/rfid_simulation.txt', 'w') as f:
                f.write('No tag')
        except:
            pass  # Ignore errors if we can't write to the file
            
        while self.running:
            current_time = time.time()
            
            # Check for manual tag simulation input (for testing without hardware)
            try:
                with open('/tmp/rfid_simulation.txt', 'r') as f:
                    content = f.read().strip()
                    if content != 'No tag' and content != '':
                        # This is a simulated tag request
                        manual_tag_request = content
                        last_manual_action_time = current_time
                        # Clear the file
                        with open('/tmp/rfid_simulation.txt', 'w') as f:
                            f.write('No tag')
            except:
                pass  # Ignore errors if we can't read the file
            
            # Handle manual tag requests first
            if manual_tag_request and current_time - last_manual_action_time < 0.5:
                # Immediately simulate the requested tag
                if not tag_present:
                    # New tag detected
                    tag_id = manual_tag_request
                    self.current_tag = tag_id
                    
                    if self.callback:
                        self.callback(tag_id, 'present')
                    logger.info(f"[MANUAL SIMULATION] RFID tag detected: {tag_id}")
                    tag_present = True
                    tag_detected_time = current_time
                    manual_tag_request = None
            
            # Automatic tag simulation logic (when no manual requests)
            elif manual_tag_request is None:
                # Toggle tag presence automatically
                if not tag_present and current_time - tag_detected_time > 1:
                    # Simulate new tag detection
                    current_index = (current_index + 1) % len(simulated_tags)
                    tag_id = simulated_tags[current_index]
                    self.current_tag = tag_id
                    
                    if self.callback:
                        self.callback(tag_id, 'present')
                    logger.info(f"[SIMULATION] RFID tag detected: {tag_id}")
                    tag_present = True
                    tag_detected_time = current_time
                    
                elif tag_present and current_time - tag_detected_time > 3:
                    # Simulate tag removal
                    tag_id = simulated_tags[current_index]
                    if self.callback:
                        self.callback(tag_id, 'absent')
                    logger.info(f"[SIMULATION] RFID tag removed: {tag_id}")
                    self.current_tag = None
                    tag_present = False
                    tag_detected_time = current_time
            
            # Check for manual tag removal
            if tag_present and current_time - last_manual_action_time > 5:
                # After 5 seconds, automatically remove the manual tag
                if manual_tag_request is not None:
                    tag_id = self.current_tag
                    if self.callback:
                        self.callback(tag_id, 'absent')
                    logger.info(f"[MANUAL SIMULATION] RFID tag removed: {tag_id}")
                    self.current_tag = None
                    tag_present = False
                    manual_tag_request = None
            
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