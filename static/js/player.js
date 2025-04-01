document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const audioPlayer = document.getElementById('audio-player');
    const playButton = document.getElementById('play-button');
    const playIcon = document.getElementById('play-icon');
    const prevButton = document.getElementById('prev-button');
    const nextButton = document.getElementById('next-button');
    const songTitle = document.getElementById('song-title');
    const songList = document.getElementById('song-list');
    const noSongsMessage = document.getElementById('no-songs-message');
    const progress = document.getElementById('progress');
    const progressBar = document.getElementById('progress-bar');
    const albumCover = document.getElementById('album-cover');
    const albumPlaceholder = document.getElementById('album-placeholder');
    
    // Player state
    let songs = [];
    let currentSongIndex = 0;
    let isPlaying = false;

    // Fetch songs from the server
    async function loadSongs() {
        try {
            const response = await fetch('/api/songs');
            if (!response.ok) {
                throw new Error('Failed to load songs');
            }
            
            songs = await response.json();
            
            // Update the UI with the songs
            displaySongs();
            
        } catch (error) {
            console.error('Error loading songs:', error);
            songList.innerHTML = `<div class="loading-message">Error loading songs: ${error.message}</div>`;
        }
    }

    // Display songs in the song list
    function displaySongs() {
        // Clear the loading message
        songList.innerHTML = '';
        
        if (songs.length === 0) {
            // Show message if no songs found
            noSongsMessage.style.display = 'block';
            return;
        }
        
        // Hide the no songs message
        noSongsMessage.style.display = 'none';
        
        // Create a song list item for each song
        songs.forEach((song, index) => {
            const songItem = document.createElement('div');
            songItem.classList.add('song-item');
            songItem.textContent = song.title;
            songItem.setAttribute('data-index', index);
            
            songItem.addEventListener('click', () => {
                playSong(index);
            });
            
            songList.appendChild(songItem);
        });
    }

    // Play a song by index
    function playSong(index) {
        if (songs.length === 0) return;
        
        // Update current song index
        currentSongIndex = index;
        
        // Get the song filename
        const song = songs[currentSongIndex];
        
        // Update the audio source
        audioPlayer.src = `/api/play/${encodeURIComponent(song.filename)}`;
        
        // Update the UI
        updateSongDisplay();
        
        // Play the song
        audioPlayer.play()
            .then(() => {
                isPlaying = true;
                updatePlayButtonIcon();
            })
            .catch(error => {
                console.error('Error playing song:', error);
                songTitle.textContent = 'Error playing song';
            });
        
        // Update the active song in the list
        updateActiveSong();
    }

    // Update the song display
    function updateSongDisplay() {
        if (songs.length === 0) {
            songTitle.textContent = 'No songs available';
            return;
        }
        
        const song = songs[currentSongIndex];
        songTitle.textContent = song.title;
        
        // Update album cover if available
        if (song.cover_image) {
            albumCover.src = `/api/cover/${encodeURIComponent(song.cover_image)}`;
            albumCover.style.display = 'block';
            albumPlaceholder.style.display = 'none';
        } else {
            albumCover.style.display = 'none';
            albumPlaceholder.style.display = 'flex';
        }
    }

    // Update the play button icon
    function updatePlayButtonIcon() {
        if (isPlaying) {
            playIcon.src = '/static/svg/pause.svg';
        } else {
            playIcon.src = '/static/svg/play.svg';
        }
    }

    // Update the active song in the list
    function updateActiveSong() {
        // Remove active class from all songs
        document.querySelectorAll('.song-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to current song
        const activeSong = document.querySelector(`.song-item[data-index="${currentSongIndex}"]`);
        if (activeSong) {
            activeSong.classList.add('active');
            // Scroll to the active song
            activeSong.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    // Play/Pause button click handler
    playButton.addEventListener('click', () => {
        if (songs.length === 0) return;
        
        if (isPlaying) {
            audioPlayer.pause();
            isPlaying = false;
        } else {
            // If no song is loaded, play the first one
            if (!audioPlayer.src) {
                playSong(0);
                return;
            }
            audioPlayer.play()
                .catch(error => {
                    console.error('Error playing song:', error);
                });
            isPlaying = true;
        }
        
        updatePlayButtonIcon();
    });

    // Previous button click handler
    prevButton.addEventListener('click', () => {
        if (songs.length === 0) return;
        
        // Go to previous song or wrap around to the last
        let prevIndex = currentSongIndex - 1;
        if (prevIndex < 0) {
            prevIndex = songs.length - 1;
        }
        
        playSong(prevIndex);
    });

    // Next button click handler
    nextButton.addEventListener('click', () => {
        if (songs.length === 0) return;
        
        // Go to next song or wrap around to the first
        let nextIndex = currentSongIndex + 1;
        if (nextIndex >= songs.length) {
            nextIndex = 0;
        }
        
        playSong(nextIndex);
    });

    // Progress bar click handler
    progressBar.addEventListener('click', (event) => {
        if (songs.length === 0 || !audioPlayer.duration) return;
        
        const rect = progressBar.getBoundingClientRect();
        const position = (event.clientX - rect.left) / rect.width;
        
        // Set current time based on click position
        audioPlayer.currentTime = position * audioPlayer.duration;
    });

    // Audio player event handlers
    audioPlayer.addEventListener('timeupdate', () => {
        if (audioPlayer.duration) {
            const percentage = (audioPlayer.currentTime / audioPlayer.duration) * 100;
            progress.style.width = `${percentage}%`;
        }
    });

    audioPlayer.addEventListener('ended', () => {
        // Auto-play next song
        let nextIndex = currentSongIndex + 1;
        if (nextIndex >= songs.length) {
            nextIndex = 0;
        }
        
        playSong(nextIndex);
    });

    audioPlayer.addEventListener('error', (e) => {
        console.error('Audio error:', e);
        songTitle.textContent = 'Error playing song';
        isPlaying = false;
        updatePlayButtonIcon();
    });

    // Load songs on page load
    loadSongs();
});