"""
Main application module
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from routes.rfid_routes import rfid_bp
from routes.song_routes import song_bp
from routes.playlist_routes import playlist_bp
from routes.player_routes import player_bp
from models import db
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///kids_audio_player.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(rfid_bp)
app.register_blueprint(song_bp)
app.register_blueprint(playlist_bp)
app.register_blueprint(player_bp)

# Create database tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
