"""
Models for MP3 player application
"""
from datetime import datetime
from db import db

class Playlist(db.Model):
    """
    Model representing a playlist of songs
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to songs
    songs = db.relationship('Song', backref='playlist', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Playlist {self.name}>'

class Song(db.Model):
    """
    Model representing a song file
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    order = db.Column(db.Integer, default=0)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), nullable=False)
    
    # Relationship to RFID tags
    rfid_tags = db.relationship('RFIDTag', backref='song', lazy=True)
    
    def __repr__(self):
        return f'<Song {self.title}>'

class RFIDTag(db.Model):
    """
    Model representing an RFID tag linked to a song
    """
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RFIDTag {self.tag_id}>'