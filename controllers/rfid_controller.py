"""
RFID Controller for MP3 Player

This module manages RFID tag registrations and interactions with the database.
"""
import logging
from datetime import datetime
from flask import current_app
from models import RFIDTag, Song, db

logger = logging.getLogger(__name__)

class RFIDController:
    """
    Controller for RFID tag operations
    """
    @staticmethod
    def register_tag(tag_id, song_id, name=None):
        """
        Register a new RFID tag with a song
        
        Args:
            tag_id (str): The ID of the RFID tag
            song_id (int): The ID of the song to link
            name (str, optional): A friendly name for the tag
            
        Returns:
            RFIDTag: The newly created tag object, or None if failed
        """
        try:
            # Check if the tag already exists
            existing_tag = RFIDTag.query.filter_by(tag_id=tag_id).first()
            if existing_tag:
                logger.warning(f"Tag {tag_id} already registered, updating instead")
                existing_tag.song_id = song_id
                if name:
                    existing_tag.name = name
                db.session.commit()
                return existing_tag
            
            # Check if the song exists
            song = Song.query.get(song_id)
            if not song:
                logger.error(f"Song with ID {song_id} not found")
                return None
            
            # Create new tag
            tag = RFIDTag(
                tag_id=tag_id,
                song_id=song_id,
                name=name
            )
            
            db.session.add(tag)
            db.session.commit()
            logger.info(f"Registered RFID tag {tag_id} for song {song.title}")
            return tag
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering RFID tag: {e}")
            return None
    
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
            logger.error(f"Error getting all RFID tags: {e}")
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