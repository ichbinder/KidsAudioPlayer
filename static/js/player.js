document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    
    // Create RFID status element
    const rfidStatusContainer = document.createElement('div');
    rfidStatusContainer.className = 'rfid-status-container';
    rfidStatusContainer.innerHTML = `
        <div class="rfid-status" id="rfid-status">
            <span class="rfid-status-icon">🔄</span>
            <span class="rfid-status-text">RFID bereit</span>
        </div>
    `;
    
    // Add it to the DOM after the header
    const header = document.querySelector('header');
    header.parentNode.insertBefore(rfidStatusContainer, header.nextSibling);
    
    // Reference to RFID status elements
    const rfidStatus = document.getElementById('rfid-status');
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
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const sleepTimerButton = document.querySelector('.top-buttons #sleep-timer-button');
    const sleepTimerOptions = document.querySelector('.top-buttons #sleep-timer-options');
    const sleepTimerText = document.querySelector('.top-buttons #sleep-timer-text');
    const timerOptions = document.querySelectorAll('.top-buttons .timer-option');
    
    // Player state
    let songs = [];
    let currentSongIndex = 0;
    let isPlaying = false;
    let sleepTimerId = null;
    let sleepTimerEndTime = null;
    let currentVolume = 0.7; // Default volume (0.0 to 1.0)

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
            songItem.setAttribute('data-index', index);
            
            // Create cover image container
            const coverContainer = document.createElement('div');
            coverContainer.classList.add('song-item-cover');
            
            // Add cover image if available, otherwise show music note
            if (song.cover_image) {
                const coverImg = document.createElement('img');
                coverImg.src = `/api/cover/${encodeURIComponent(song.cover_image)}`;
                coverImg.alt = song.title;
                coverContainer.appendChild(coverImg);
            } else {
                const defaultCover = document.createElement('div');
                defaultCover.classList.add('default-cover');
                defaultCover.textContent = '♪';
                coverContainer.appendChild(defaultCover);
            }
            
            // Create title element
            const titleElement = document.createElement('div');
            titleElement.classList.add('song-item-title');
            titleElement.textContent = song.title;
            
            // Add elements to song item
            songItem.appendChild(coverContainer);
            songItem.appendChild(titleElement);
            
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
        
        // Play the song - using timeout to avoid potential race conditions
        setTimeout(() => {
            if (audioPlayer.paused) {
                audioPlayer.play()
                    .then(() => {
                        isPlaying = true;
                        updatePlayButtonIcon();
                    })
                    .catch(error => {
                        // Only log error if it's not an AbortError
                        if (error.name !== 'AbortError') {
                            console.error('Error playing song:', error);
                            songTitle.textContent = 'Error playing song';
                        }
                    });
            }
        }, 50);
        
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
                .then(() => {
                    isPlaying = true;
                })
                .catch(error => {
                    // Only log error if it's not an AbortError
                    if (error.name !== 'AbortError') {
                        console.error('Error playing song:', error);
                    }
                });
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

    // Sleep Timer Functions
    function startSleepTimer(minutes) {
        // Clear any existing timer
        clearSleepTimer();
        
        if (minutes <= 0) {
            updateSleepTimerDisplay(0);
            return;
        }
        
        // Set end time
        const now = new Date();
        sleepTimerEndTime = new Date(now.getTime() + minutes * 60000);
        
        // Update display immediately
        updateSleepTimerDisplay(minutes);
        
        // Add active class to the sleep timer button
        sleepTimerButton.classList.add('timer-active');
        
        // Start a timer to update display and eventually pause playback
        sleepTimerId = setInterval(() => {
            // Calculate remaining time
            const now = new Date();
            const remainingMs = sleepTimerEndTime - now;
            
            if (remainingMs <= 0) {
                // Time's up - pause playback
                audioPlayer.pause();
                isPlaying = false;
                updatePlayButtonIcon();
                clearSleepTimer();
                return;
            }
            
            // Update display with remaining minutes
            const remainingMinutes = Math.ceil(remainingMs / 60000);
            updateSleepTimerDisplay(remainingMinutes);
        }, 1000);
    }
    
    function clearSleepTimer() {
        if (sleepTimerId) {
            clearInterval(sleepTimerId);
            sleepTimerId = null;
            sleepTimerEndTime = null;
            sleepTimerButton.classList.remove('timer-active');
            sleepTimerButton.setAttribute('title', 'Schlaf-Timer');
            sleepTimerButton.removeAttribute('data-time');
            
            // Remove active class from all timer options
            timerOptions.forEach(option => {
                option.classList.remove('active');
            });
        }
    }
    
    function updateSleepTimerDisplay(minutes) {
        if (minutes <= 0) {
            sleepTimerButton.setAttribute('title', 'Schlaf-Timer');
            sleepTimerButton.removeAttribute('data-time');
            return;
        }
        
        sleepTimerButton.setAttribute('title', `${minutes} Min`);
        sleepTimerButton.setAttribute('data-time', minutes);
    }
    
    // Sleep Timer button click handler
    sleepTimerButton.addEventListener('click', (event) => {
        // Toggle timer options visibility
        sleepTimerOptions.classList.toggle('hidden');
        event.stopPropagation();
    });
    
    // Click anywhere else to hide timer options
    document.addEventListener('click', (event) => {
        if (!sleepTimerOptions.contains(event.target) && event.target !== sleepTimerButton) {
            sleepTimerOptions.classList.add('hidden');
        }
    });
    
    // Timer option click handlers
    timerOptions.forEach(option => {
        option.addEventListener('click', () => {
            // Get minutes from data attribute
            const minutes = parseInt(option.getAttribute('data-minutes'), 10);
            
            // Remove active class from all options
            timerOptions.forEach(opt => opt.classList.remove('active'));
            
            // Add active class to selected option
            if (minutes > 0) {
                option.classList.add('active');
            }
            
            // Start/clear timer
            startSleepTimer(minutes);
            
            // Hide options
            sleepTimerOptions.classList.add('hidden');
        });
    });

    // Theme Management Functions
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update the theme toggle button icon
        if (theme === 'dark') {
            themeIcon.src = '/static/svg/sun.svg';
            themeToggle.title = 'Zum hellen Modus wechseln';
        } else {
            themeIcon.src = '/static/svg/moon.svg';
            themeToggle.title = 'Zum dunklen Modus wechseln';
        }
    }
    
    function initTheme() {
        // Check for saved theme preference or use device preference
        const savedTheme = localStorage.getItem('theme');
        
        if (savedTheme) {
            setTheme(savedTheme);
        } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            // Use dark theme if user prefers dark mode
            setTheme('dark');
        } else {
            // Default to light theme
            setTheme('light');
        }
    }
    
    // Theme toggle button click handler
    themeToggle.addEventListener('click', () => {
        // Toggle between light and dark themes
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    });
    
    // Initialize theme
    initTheme();
    
    // Volume Control Functions
    function initVolumeControl() {
        // Get volume control elements
        const volumeSlider = document.getElementById('volume-slider');
        const volumeSliderFill = document.getElementById('volume-slider-fill');
        const volumeIcon = document.getElementById('volume-icon');
        
        if (volumeSlider && volumeSliderFill) {
            // Set initial volume
            audioPlayer.volume = currentVolume;
            volumeSlider.value = currentVolume * 100;
            volumeSliderFill.style.width = `${currentVolume * 100}%`;
            
            // Add event listeners for volume control
            volumeSlider.addEventListener('input', function() {
                const value = this.value;
                
                // Update volume
                currentVolume = value / 100;
                audioPlayer.volume = currentVolume;
                
                // Update fill
                volumeSliderFill.style.width = `${value}%`;
                
                // Update volume icon based on level
                updateVolumeIcon(currentVolume);
                
                // Save volume preference
                localStorage.setItem('volume', currentVolume);
            });
            
            // Volume icon click to mute/unmute
            volumeIcon.addEventListener('click', function() {
                if (audioPlayer.volume > 0) {
                    // Store the current volume before muting
                    localStorage.setItem('previousVolume', audioPlayer.volume);
                    
                    // Mute
                    audioPlayer.volume = 0;
                    volumeSlider.value = 0;
                    volumeSliderFill.style.width = '0%';
                    updateVolumeIcon(0);
                } else {
                    // Unmute to previous volume or default
                    const previousVolume = parseFloat(localStorage.getItem('previousVolume')) || 0.7;
                    audioPlayer.volume = previousVolume;
                    volumeSlider.value = previousVolume * 100;
                    volumeSliderFill.style.width = `${previousVolume * 100}%`;
                    updateVolumeIcon(previousVolume);
                }
                
                // Save current volume
                currentVolume = audioPlayer.volume;
                localStorage.setItem('volume', currentVolume);
            });
            
            // Load saved volume preference
            const savedVolume = localStorage.getItem('volume');
            if (savedVolume !== null) {
                currentVolume = parseFloat(savedVolume);
                audioPlayer.volume = currentVolume;
                volumeSlider.value = currentVolume * 100;
                volumeSliderFill.style.width = `${currentVolume * 100}%`;
                updateVolumeIcon(currentVolume);
            }
        }
    }
    
    function updateVolumeIcon(volume) {
        const volumeIcon = document.getElementById('volume-icon');
        if (volumeIcon) {
            if (volume <= 0) {
                volumeIcon.textContent = '🔇';
            } else if (volume < 0.3) {
                volumeIcon.textContent = '🔈';
            } else if (volume < 0.7) {
                volumeIcon.textContent = '🔉';
            } else {
                volumeIcon.textContent = '🔊';
            }
        }
    }
    
    // Initialize volume control
    initVolumeControl();
    
    // Load songs on page load
    loadSongs();
    
    // RFID functionality
    // Function to check for RFID events via polling
    function setupRFIDListener() {
        let lastEventTimestamp = null;
        let isTagPresent = false;
        
        // Update RFID status display
        function updateRFIDStatus(status, message, isActive = false, isError = false) {
            rfidStatus.innerHTML = `<span class="rfid-status-icon">${status}</span><span class="rfid-status-text">${message}</span>`;
            
            rfidStatus.classList.toggle('active', isActive);
            rfidStatus.classList.toggle('error', isError);
        }
        
        // Handle tag_present event
        function handleTagPresent(data) {
            console.log('RFID tag present:', data);
            
            // Update UI
            updateRFIDStatus('🎵', `RFID-Tag: ${data.name || data.tag_id}`, true, false);
            
            // Only play if the tag was just detected (not on every poll)
            if (!isTagPresent) {
                isTagPresent = true;
                
                // Play the associated song if it's available
                if (data.song_id) {
                    // Find the song in our songs array
                    const songIndex = songs.findIndex(song => song.id === data.song_id);
                    if (songIndex !== -1) {
                        playSong(songIndex);
                    } else if (data.filename) {
                        // If the song is not in our current list, we need to play it directly
                        audioPlayer.src = `/api/play/${encodeURIComponent(data.filename)}`;
                        audioPlayer.play()
                            .then(() => {
                                isPlaying = true;
                                updatePlayButtonIcon();
                                songTitle.textContent = data.title || 'Unknown Song';
                            })
                            .catch(error => {
                                console.error('Error playing song from RFID:', error);
                                songTitle.textContent = 'Error playing song';
                            });
                    }
                }
            }
        }
        
        // Handle tag_absent event
        function handleTagAbsent(data) {
            console.log('RFID tag removed:', data);
            
            // Update UI
            updateRFIDStatus('🔄', 'RFID bereit', false, false);
            
            // Only pause if the tag was just removed (not on every poll)
            if (isTagPresent) {
                isTagPresent = false;
                
                // Pause the playback
                if (isPlaying) {
                    audioPlayer.pause();
                    isPlaying = false;
                    updatePlayButtonIcon();
                }
            }
        }
        
        // Poll for RFID status
        function pollRFIDStatus() {
            fetch('/api/rfid/status')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'active' && data.timestamp !== lastEventTimestamp) {
                        lastEventTimestamp = data.timestamp;
                        
                        if (data.event === 'tag_present') {
                            handleTagPresent(data.data);
                        } else if (data.event === 'tag_absent') {
                            handleTagAbsent(data.data);
                        }
                    }
                })
                .catch(error => {
                    console.error('Error polling RFID status:', error);
                    updateRFIDStatus('⚠️', 'RFID Verbindungsfehler', false, true);
                });
        }
        
        // Initial UI state
        updateRFIDStatus('🔄', 'RFID bereit', false, false);
        
        // Start polling
        pollRFIDStatus();
        setInterval(pollRFIDStatus, 2000); // Poll every 2 seconds
    }
    
    // Setup RFID listener
    setupRFIDListener();
});