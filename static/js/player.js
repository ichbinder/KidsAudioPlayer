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
    
    // Playlist elements
    const playlistsContainer = document.getElementById('playlists-container');
    const noPlaylistsMessage = document.getElementById('no-playlists-message');
    const newPlaylistButton = document.getElementById('new-playlist-button');
    const addToPlaylistButton = document.getElementById('add-to-playlist-button');
    const currentPlaylistName = document.getElementById('current-playlist-name');
    
    // Modal elements
    const playlistModal = document.getElementById('playlist-modal');
    const addSongsModal = document.getElementById('add-songs-modal');
    const playlistForm = document.getElementById('playlist-form');
    const playlistNameInput = document.getElementById('playlist-name');
    const playlistSelect = document.getElementById('playlist-select');
    const availableSongs = document.getElementById('available-songs');
    const addSongsButton = document.getElementById('add-songs-button');
    const modalCloseButtons = document.querySelectorAll('.close-modal, .cancel');
    
    // Player state
    let songs = [];
    let playlists = [];
    let allSongs = [];
    let currentSongIndex = 0;
    let isPlaying = false;
    let currentPlaylistId = null; // null means "All Songs" view

    // Fetch songs from the server
    async function loadSongs() {
        try {
            const response = await fetch('/api/songs');
            if (!response.ok) {
                throw new Error('Failed to load songs');
            }
            
            allSongs = await response.json();
            
            // If we're in "All Songs" view (no playlist selected)
            if (currentPlaylistId === null) {
                songs = allSongs;
            }
            
            // Update the UI with the songs
            displaySongs();
            
        } catch (error) {
            console.error('Error loading songs:', error);
            songList.innerHTML = `<div class="loading-message">Error loading songs: ${error.message}</div>`;
        }
    }
    
    // Fetch playlists from the server
    async function loadPlaylists() {
        try {
            playlistsContainer.innerHTML = '<div class="loading-message">Loading playlists...</div>';
            
            const response = await fetch('/api/playlists');
            if (!response.ok) {
                throw new Error('Failed to load playlists');
            }
            
            playlists = await response.json();
            
            // Update the UI with the playlists
            displayPlaylists();
            
        } catch (error) {
            console.error('Error loading playlists:', error);
            playlistsContainer.innerHTML = `<div class="loading-message">Error loading playlists: ${error.message}</div>`;
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
        
        // Show/hide Add to Playlist button only when we are in All Songs view
        addToPlaylistButton.style.display = (currentPlaylistId === null && playlists.length > 0) ? 'block' : 'none';
    }
    
    // Display playlists
    function displayPlaylists() {
        // Clear the container
        playlistsContainer.innerHTML = '';
        
        if (playlists.length === 0) {
            // Show message if no playlists found
            noPlaylistsMessage.style.display = 'block';
            // Hide Add to playlist button if there are no playlists
            addToPlaylistButton.style.display = 'none';
            return;
        }
        
        // Hide the no playlists message
        noPlaylistsMessage.style.display = 'none';
        
        // Add "All Songs" option
        const allSongsItem = document.createElement('div');
        allSongsItem.classList.add('playlist-item');
        if (currentPlaylistId === null) {
            allSongsItem.classList.add('active');
        }
        
        const allSongsTitle = document.createElement('div');
        allSongsTitle.classList.add('playlist-title');
        allSongsTitle.textContent = 'All Songs';
        
        const allSongsInfo = document.createElement('div');
        allSongsInfo.classList.add('playlist-info');
        allSongsInfo.textContent = `${allSongs.length} songs`;
        
        allSongsItem.appendChild(allSongsTitle);
        allSongsItem.appendChild(allSongsInfo);
        
        allSongsItem.addEventListener('click', () => {
            selectPlaylist(null);
        });
        
        playlistsContainer.appendChild(allSongsItem);
        
        // Create a playlist item for each playlist
        playlists.forEach((playlist) => {
            const playlistItem = document.createElement('div');
            playlistItem.classList.add('playlist-item');
            if (currentPlaylistId === playlist.id) {
                playlistItem.classList.add('active');
            }
            
            const playlistTitle = document.createElement('div');
            playlistTitle.classList.add('playlist-title');
            playlistTitle.textContent = playlist.name;
            
            const playlistInfo = document.createElement('div');
            playlistInfo.classList.add('playlist-info');
            playlistInfo.textContent = `${playlist.songs.length} songs`;
            
            playlistItem.appendChild(playlistTitle);
            playlistItem.appendChild(playlistInfo);
            
            playlistItem.addEventListener('click', () => {
                selectPlaylist(playlist.id);
            });
            
            playlistsContainer.appendChild(playlistItem);
        });
        
        // Show Add to playlist button if we're in All Songs view and have playlists
        addToPlaylistButton.style.display = (currentPlaylistId === null) ? 'block' : 'none';
        
        // Update playlist select dropdown in modal
        updatePlaylistSelect();
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

    // Select a playlist and load its songs
    function selectPlaylist(playlistId) {
        currentPlaylistId = playlistId;
        
        // Update header and active state
        if (playlistId === null) {
            currentPlaylistName.textContent = 'All Songs';
            songs = [...allSongs]; // Copy all songs
        } else {
            const playlist = playlists.find(p => p.id === playlistId);
            if (playlist) {
                currentPlaylistName.textContent = playlist.name;
                songs = playlist.songs;
            }
        }
        
        // Update UI
        displaySongs();
        displayPlaylists();
        
        // Reset player if needed
        if (currentSongIndex >= songs.length) {
            currentSongIndex = 0;
            if (isPlaying) {
                audioPlayer.pause();
                isPlaying = false;
                updatePlayButtonIcon();
            }
            updateSongDisplay();
        }
    }
    
    // Update playlist select in modal
    function updatePlaylistSelect() {
        playlistSelect.innerHTML = '';
        
        playlists.forEach(playlist => {
            const option = document.createElement('option');
            option.value = playlist.id;
            option.textContent = playlist.name;
            playlistSelect.appendChild(option);
        });
    }
    
    // Modal functions
    function openPlaylistModal() {
        playlistModal.style.display = 'flex';
        playlistNameInput.value = '';
        playlistNameInput.focus();
    }
    
    function closePlaylistModal() {
        playlistModal.style.display = 'none';
    }
    
    function openAddSongsModal() {
        if (playlists.length === 0) {
            alert('Create a playlist first before adding songs.');
            return;
        }
        
        addSongsModal.style.display = 'flex';
        updateAvailableSongs();
    }
    
    function closeAddSongsModal() {
        addSongsModal.style.display = 'none';
    }
    
    // Update available songs in add to playlist modal
    function updateAvailableSongs() {
        availableSongs.innerHTML = '';
        
        if (allSongs.length === 0) {
            availableSongs.innerHTML = '<div class="loading-message">No songs available</div>';
            return;
        }
        
        allSongs.forEach(song => {
            const songCheckbox = document.createElement('div');
            songCheckbox.classList.add('song-checkbox');
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `song-${song.id || song.filename.replace(/[^a-z0-9]/gi, '-')}`;
            checkbox.value = song.filename;
            checkbox.dataset.title = song.title;
            
            const label = document.createElement('label');
            label.htmlFor = checkbox.id;
            label.textContent = song.title;
            
            songCheckbox.appendChild(checkbox);
            songCheckbox.appendChild(label);
            
            availableSongs.appendChild(songCheckbox);
        });
    }
    
    // Create a new playlist
    async function createPlaylist(name) {
        try {
            const response = await fetch('/api/playlists', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name })
            });
            
            if (!response.ok) {
                throw new Error('Failed to create playlist');
            }
            
            const playlist = await response.json();
            playlists.push(playlist);
            displayPlaylists();
            
            return playlist;
        } catch (error) {
            console.error('Error creating playlist:', error);
            alert(`Error creating playlist: ${error.message}`);
            return null;
        }
    }
    
    // Add songs to a playlist
    async function addSongsToPlaylist(playlistId, songsToAdd) {
        try {
            for (const song of songsToAdd) {
                const response = await fetch(`/api/playlists/${playlistId}/songs`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        title: song.title,
                        filename: song.filename
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`Failed to add song "${song.title}" to playlist`);
                }
            }
            
            // Refresh playlists after adding songs
            await loadPlaylists();
            
            return true;
        } catch (error) {
            console.error('Error adding songs to playlist:', error);
            alert(`Error adding songs: ${error.message}`);
            return false;
        }
    }
    
    // Event listeners for playlist/modal functionality
    newPlaylistButton.addEventListener('click', openPlaylistModal);
    
    addToPlaylistButton.addEventListener('click', openAddSongsModal);
    
    modalCloseButtons.forEach(button => {
        button.addEventListener('click', () => {
            closePlaylistModal();
            closeAddSongsModal();
        });
    });
    
    playlistForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = playlistNameInput.value.trim();
        
        if (name) {
            const playlist = await createPlaylist(name);
            if (playlist) {
                closePlaylistModal();
            }
        } else {
            alert('Please enter a playlist name');
        }
    });
    
    addSongsButton.addEventListener('click', async () => {
        const playlistId = parseInt(playlistSelect.value);
        if (!playlistId) {
            alert('Please select a playlist');
            return;
        }
        
        const selectedCheckboxes = availableSongs.querySelectorAll('input[type="checkbox"]:checked');
        if (selectedCheckboxes.length === 0) {
            alert('Please select at least one song');
            return;
        }
        
        const songsToAdd = Array.from(selectedCheckboxes).map(checkbox => {
            return {
                title: checkbox.dataset.title,
                filename: checkbox.value
            };
        });
        
        const success = await addSongsToPlaylist(playlistId, songsToAdd);
        if (success) {
            closeAddSongsModal();
        }
    });
    
    // Load songs and playlists on page load
    loadSongs();
    loadPlaylists();
});
