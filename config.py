"""
Configuration settings for the Kids Audio Player
"""
import os

# Base directory for the application
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directory for storing MP3 files
MUSIC_DIR = os.path.join(BASE_DIR, 'static', 'music')

# Ensure the music directory exists
os.makedirs(MUSIC_DIR, exist_ok=True) 