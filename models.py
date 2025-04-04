"""
Models for MP3 player application
"""
from datetime import datetime
from db import db

class RFIDTag(db.Model):
    """Model for RFID tags"""
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    mp3_filename = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<RFIDTag {self.name} ({self.tag_id})>'