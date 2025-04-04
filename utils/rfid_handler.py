"""
RFID Handler for MP3 Player

This module handles RFID tag detection using RC522 RFID reader.
It's designed to work with Raspberry Pi.
"""
import logging
import threading
import time
import os
from datetime import datetime
from contextlib import contextmanager

# Setup logging
logger = logging.getLogger(__name__)

# Flag to determine if we're running on a Raspberry Pi
GPIO = None
SimpleMFRC522 = None
RASPBERRY_PI = False

try:
    import RPi.GPIO as GPIO
    from mfrc522 import SimpleMFRC522
    RASPBERRY_PI = True
    logger.info("Running on Raspberry Pi, RFID module enabled")
    print("[INIT] Running on Raspberry Pi, RFID module enabled")
except (ImportError, RuntimeError) as e:
    RASPBERRY_PI = False
    logger.warning(f"Not running on Raspberry Pi or missing required libraries. RFID functionality will be simulated. Error: {e}")
    print(f"[INIT] Not running on Raspberry Pi or missing required libraries. RFID functionality will be simulated. Error: {e}")
    
# Allow force enabling simulation mode for testing (even on Raspberry Pi)
# Set the environment variable RFID_SIMULATION=1 to enable
if os.environ.get('RFID_SIMULATION') == '1':
    RASPBERRY_PI = False
    logger.info("RFID simulation mode forced by environment variable")
    print("[INIT] RFID simulation mode forced by environment variable")

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
        self.tag_removal_thread = None
        self.removal_event = threading.Event()
        
        # Initialize the RFID reader if we're on a Raspberry Pi
        if RASPBERRY_PI:
            try:
                self.reader = SimpleMFRC522()
                print("[INIT] RFID reader initialized successfully")
                logger.info("RFID reader initialized")
            except Exception as e:
                print(f"[ERROR] Failed to initialize RFID reader: {e}")
                logger.error(f"Failed to initialize RFID reader: {e}")
                self.reader = None
    
    def start(self):
        """Start the RFID detection thread"""
        if self.running:
            logger.warning("RFID handler already running")
            return
            
        # Print detailed startup information
        print("\n[RFID] Starting RFID detection system")
        if not RASPBERRY_PI:
            print("[RFID] ⚠️ Not running on Raspberry Pi or missing required libraries")
            print("[RFID] Using simulation mode instead")
        else:
            print(f"[RFID] 🔍 Running on Raspberry Pi with reader: {self.reader}")
        
        # Start the main detection loop
        self.running = True
        self.thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.thread.start()
        
        # Start a separate thread to detect tag removal
        if RASPBERRY_PI:
            self.tag_removal_thread = threading.Thread(target=self._check_tag_removal, daemon=True)
            self.tag_removal_thread.start()
            print("[RFID] Started additional tag removal detection thread")
            
        logger.info("RFID detection started")
        
    def _check_tag_removal(self):
        """Separate thread to check for tag removal"""
        print("[RFID] Tag removal detection thread started")
        last_tag_id = None
        consecutive_misses = 0
        
        while self.running:
            time.sleep(0.1)  # Short interval for quick detection
            
            # If we have a current tag, we need to check if it's still there
            current_tag = self.current_tag
            if current_tag:
                # Try to read the tag
                try:
                    tag_id, _ = self.reader.read_no_block()
                    if not tag_id:
                        consecutive_misses += 1
                        if consecutive_misses >= 5:  # After 0.5 seconds of no tag
                            print(f"[RFID REMOVAL] Tag {current_tag} has been removed (after {consecutive_misses} consecutive misses)")
                            # Notify callback that tag is gone
                            if self.callback:
                                self.callback(current_tag, 'absent')
                            self.current_tag = None
                            consecutive_misses = 0
                    else:
                        # Tag is still there
                        consecutive_misses = 0
                except Exception as e:
                    print(f"[ERROR] Error checking for tag removal: {e}")
                    time.sleep(0.5)  # Wait a bit longer on errors
            else:
                # No current tag, just reset
                consecutive_misses = 0
    
    def stop(self):
        """Stop the RFID detection thread"""
        if not self.running:
            return
        
        print("[RFID] Stopping RFID detection system...")    
        self.running = False
        
        # Stop main detection thread
        if self.thread:
            try:
                self.thread.join(timeout=2.0)
                print("[RFID] Main detection thread stopped successfully")
            except Exception as e:
                print(f"[RFID] Error stopping main thread: {e}")
        
        # Stop tag removal thread if it exists
        if hasattr(self, 'tag_removal_thread') and self.tag_removal_thread:
            try:
                self.tag_removal_thread.join(timeout=2.0)
                print("[RFID] Tag removal thread stopped successfully")
            except Exception as e:
                print(f"[RFID] Error stopping tag removal thread: {e}")
                
        # Clean up GPIO on shutdown if we're on a Raspberry Pi
        if RASPBERRY_PI:
            try:
                print("[RFID] Cleaning up GPIO...")
                GPIO.cleanup()
                print("[RFID] GPIO cleanup completed")
            except Exception as e:
                print(f"[RFID] Error during GPIO cleanup: {e}")
        
        print("[RFID] RFID detection system stopped")
        logger.info("RFID detection stopped")
    
    def _detection_loop(self):
        """Main detection loop, runs in a separate thread"""
        if not self.reader and not RASPBERRY_PI:
            # In simulation mode
            self._simulation_loop()
            return
            
        if not self.reader:
            logger.error("RFID reader not initialized, detection loop aborted")
            return
            
        print("============================================")
        print("RFID detection loop started on Raspberry Pi")
        print("This will continuously scan for RFID tags")
        print("============================================")
            
        last_tag_id = None
        tag_missing_count = 0
        check_interval = 0.05  # Very responsive checking
        read_counter = 0  # Count read attempts for debug output
        
        while self.running:
            try:
                # Debug-Ausgabe alle 100 Leseversuche (ca. alle 5 Sekunden)
                read_counter += 1
                if read_counter % 100 == 0:
                    print(f"[DEBUG] RFID: Noch aktiv, warte auf Tags... ({read_counter} Leseversuche)")
                
                # Versuche, den Tag zuerst nicht-blockierend zu lesen
                try:
                    # Non-blocking read first 
                    tag_id, text = self.reader.read_no_block()
                    
                    # If we got a tag, great!
                    if tag_id:
                        print(f"[DEBUG] RFID: Tag erkannt! ID: {tag_id}, Text: {text}")
                        # Convert tag_id to string for consistency
                        tag_id = str(tag_id)
                        
                        # New tag detected or same tag still present
                        if last_tag_id != tag_id:
                            # It's a new tag
                            print(f"[DEBUG] RFID: Neuer Tag erkannt: {tag_id}")
                            if self.callback:
                                self.callback(tag_id, 'present')
                            last_tag_id = tag_id
                            self.current_tag = tag_id
                    else:
                        # No tag found with non-blocking read
                        if last_tag_id:
                            print(f"[DEBUG] RFID: Tag entfernt: {last_tag_id}")
                            if self.callback:
                                self.callback(last_tag_id, 'absent')
                            last_tag_id = None
                            self.current_tag = None
                            
                except Exception as read_error:
                    print(f"[ERROR] RFID Lesefehler: {read_error}")
                    time.sleep(0.1)
                    continue
                
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"[ERROR] RFID Hauptschleife Fehler: {e}")
                time.sleep(0.5)
                
    def _blocking_read(self):
        """Perform a blocking read in a separate thread to avoid hanging the main loop"""
        try:
            print("[RFID] Starting blocking RFID read (timeout: 3s)")
            logger.debug("Starting blocking RFID read")
            
            # Add timeout mechanism for blocking read
            read_thread = threading.Thread(target=self._perform_blocking_read)
            read_thread.daemon = True
            read_thread.start()
            
            # Wait with timeout
            read_thread.join(timeout=3.0)
            
            if read_thread.is_alive():
                # Thread is still running after timeout
                print("[RFID] Blocking read timed out")
                logger.warning("Blocking RFID read timed out")
                return None
                
            # If we got here, the read completed
            if self.current_tag:
                print(f"[RFID] Blocking read detected tag: {self.current_tag}")
                logger.debug(f"Blocking read detected tag: {self.current_tag}")
                return self.current_tag
            else:
                print("[RFID] Blocking read returned no tag")
                logger.debug("Blocking read returned no tag")
                return None
                
        except Exception as e:
            print(f"[RFID ERROR] Error in blocking RFID read: {e}")
            logger.error(f"Error in blocking RFID read: {e}")
            self.current_tag = None
            return None
            
    def _perform_blocking_read(self):
        """Helper for _blocking_read - performs the actual blocking read"""
        if not self.reader:
            print("[RFID ERROR] No reader available for blocking read")
            return
            
        try:
            # This is the actual blocking call
            tag_id, text = self.reader.read()
            if tag_id:
                self.current_tag = str(tag_id)
                print(f"[RFID] Raw blocking read result: {tag_id}, {text}")
        except Exception as e:
            print(f"[RFID ERROR] Error in _perform_blocking_read: {e}")
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