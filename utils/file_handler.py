import os
import logging

logger = logging.getLogger(__name__)

def get_mp3_files(directory):
    """
    Get all MP3 files from a directory.
    
    Args:
        directory (str): Path to the directory containing MP3 files
        
    Returns:
        list: List of dictionaries with song information
    """
    songs = []
    
    try:
        # Check if directory exists
        if not os.path.exists(directory):
            logger.warning(f"Directory does not exist: {directory}")
            return songs
            
        # Walk through directory and get all MP3 files
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.mp3'):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, directory)
                    
                    # Basic song info
                    song_info = {
                        'filename': relative_path,
                        'title': os.path.splitext(file)[0],  # Use filename as title
                    }
                    
                    songs.append(song_info)
                    
        logger.debug(f"Found {len(songs)} MP3 files in {directory}")
        return songs
        
    except Exception as e:
        logger.error(f"Error getting MP3 files: {e}")
        raise

def get_file_path(base_dir, filename):
    """
    Get the full path of a file given its relative path.
    
    Args:
        base_dir (str): Base directory
        filename (str): Relative path of the file
        
    Returns:
        str: Full path of the file
    """
    # Ensure the path doesn't escape the base directory
    full_path = os.path.normpath(os.path.join(base_dir, filename))
    
    if not full_path.startswith(os.path.normpath(base_dir)):
        logger.error(f"Attempted path traversal: {filename}")
        raise ValueError("Invalid file path")
        
    if not os.path.exists(full_path):
        logger.error(f"File not found: {full_path}")
        raise FileNotFoundError(f"File not found: {filename}")
        
    return full_path
