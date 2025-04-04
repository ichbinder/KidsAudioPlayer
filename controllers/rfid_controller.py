"""
RFID Controller for MP3 Player

This module manages RFID tag registrations and interactions with the database.
"""
import logging
from datetime import datetime
from flask import current_app
from models import RFIDTag, db
from utils.rfid_shared import get_rfid_handler

logger = logging.getLogger(__name__)

class RFIDController:
    """
    Controller for RFID tag operations
    """
    @staticmethod
    def register_tag(tag_id, name, mp3_filename):
        """
        Register a new RFID tag
        
        Args:
            tag_id (str): The ID of the RFID tag
            name (str): A friendly name for the tag
            mp3_filename (str): The filename of the associated MP3 file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if the tag already exists
            existing_tag = RFIDTag.query.filter_by(tag_id=tag_id).first()
            if existing_tag:
                logger.warning(f"Tag {tag_id} already registered, updating instead")
                existing_tag.name = name
                existing_tag.mp3_filename = mp3_filename
                db.session.commit()
                return True
            
            # Create new tag
            new_tag = RFIDTag(
                tag_id=tag_id,
                name=name,
                mp3_filename=mp3_filename
            )
            
            db.session.add(new_tag)
            db.session.commit()
            logger.info(f"Registered RFID tag {tag_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering RFID tag: {e}")
            return False
    
    @staticmethod
    def unregister_tag(tag_id):
        """
        Unregister an RFID tag
        
        Args:
            tag_id (str): The ID of the tag to unregister
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            tag = RFIDTag.query.filter_by(tag_id=tag_id).first()
            if not tag:
                logger.warning(f"Tag {tag_id} not found, nothing to unregister")
                return False
            
            db.session.delete(tag)
            db.session.commit()
            logger.info(f"Unregistered RFID tag {tag_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error unregistering RFID tag: {e}")
            return False
    
    @staticmethod
    def get_song_by_tag(tag_id):
        """
        Get the song associated with an RFID tag
        
        Args:
            tag_id (str): The ID of the RFID tag
            
        Returns:
            Song: The associated song object, or None if not found
        """
        try:
            tag = RFIDTag.query.filter_by(tag_id=tag_id).first()
            if not tag:
                logger.warning(f"Tag {tag_id} not found")
                return None
            
            # Update last_used timestamp
            tag.last_used = datetime.utcnow()
            db.session.commit()
            
            return tag.song
            
        except Exception as e:
            logger.error(f"Error getting song for RFID tag: {e}")
            return None
    
    @staticmethod
    def get_all_tags():
        """
        Get all registered RFID tags
        
        Returns:
            list: List of all RFID tag objects
        """
        try:
            return RFIDTag.query.all()
        except Exception as e:
            logger.error(f"Error getting RFID tags: {e}")
            return []
            
    @staticmethod
    def get_tag(tag_id):
        """
        Get a specific RFID tag
        
        Args:
            tag_id (str): The ID of the RFID tag
            
        Returns:
            RFIDTag: The tag object, or None if not found
        """
        try:
            return RFIDTag.query.filter_by(tag_id=tag_id).first()
        except Exception as e:
            logger.error(f"Error getting RFID tag: {e}")
            return None

    @staticmethod
    def get_tag_info(tag_id):
        """Get information about a specific tag"""
        try:
            tag = RFIDTag.query.filter_by(tag_id=tag_id).first()
            if not tag:
                return None

            return {
                'id': tag.id,
                'tag_id': tag.tag_id,
                'name': tag.name,
                'mp3_filename': tag.mp3_filename
            }

        except Exception as e:
            logger.error(f"Error getting tag info: {e}")
            return None