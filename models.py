from datetime import datetime
from db import db

class Playlist(db.Model):
    """Model representing a playlist of songs"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with songs
    songs = db.relationship('Song', back_populates='playlist', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert playlist to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'songs': [song.to_dict() for song in self.songs]
        }

class Song(db.Model):
    """Model representing a song in a playlist"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    order = db.Column(db.Integer, default=0)  # Order in the playlist
    
    # Foreign key to playlist
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), nullable=False)
    
    # Relationship with playlist
    playlist = db.relationship('Playlist', back_populates='songs')
    
    def to_dict(self):
        """Convert song to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'filename': self.filename,
            'order': self.order
        }