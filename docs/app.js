// Configuration - Auto-detect environment
const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

// For GitHub Pages deployment, update this to your deployed backend URL
// Example: 'https://your-backend.onrender.com' or 'https://your-api.herokuapp.com'
const PRODUCTION_API_URL = 'https://eri-tig-recorder.onrender.com'; // TODO: Replace with your deployed backend URL

const API_BASE_URL = isDevelopment ? 'http://localhost:8000' : PRODUCTION_API_URL;

console.log(`Running in ${isDevelopment ? 'DEVELOPMENT' : 'PRODUCTION'} mode`);
console.log(`API endpoint: ${API_BASE_URL}`);

// State management
let mediaRecorder;
let audioChunks = [];
let currentSentence = null;
let recordedBlob = null;
let recordingMimeType = 'audio/webm'; // Store the actual mime type used
let speakerName = null; // Store speaker name
let recordingTimer = null; // Timer for max recording duration
let recordingStartTime = null; // Track recording start time
const MAX_RECORDING_DURATION = 20000; // 20 seconds in milliseconds

// DOM Elements
const sentenceText = document.getElementById('sentenceText');
const recordBtn = document.getElementById('recordBtn');
const stopBtn = document.getElementById('stopBtn');
const submitBtn = document.getElementById('submitBtn');
const skipBtn = document.getElementById('skipBtn');
const statusMessage = document.getElementById('statusMessage');
const audioPlayer = document.getElementById('audioPlayer');
const audioPlaybackSection = document.getElementById('audioPlaybackSection');
const recordingCard = document.getElementById('recordingCard');
const completionCard = document.getElementById('completionCard');

// Stats elements
const totalSentences = document.getElementById('totalSentences');
const recordedCount = document.getElementById('recordedCount');
const remainingCount = document.getElementById('remainingCount');
const progressPercent = document.getElementById('progressPercent');
const progressBar = document.getElementById('progressBar');

// Personal stats elements
const personalStatsContainer = document.getElementById('personalStatsContainer');
const personalCount = document.getElementById('personalCount');
const personalPercentage = document.getElementById('personalPercentage');
const speakerRank = document.getElementById('speakerRank');

// Speaker name elements
const speakerNameInput = document.getElementById('speakerNameInput');
const saveNameBtn = document.getElementById('saveNameBtn');
const currentSpeakerName = document.getElementById('currentSpeakerName');
const speakerNameDisplay = document.getElementById('speakerNameDisplay');
const changeNameBtn = document.getElementById('changeNameBtn');

// Initialize app
async function init() {
    loadSpeakerName();
    await checkSystemHealth(); // Check Dropbox connection first
    await loadStats();
    await loadNextSentence();
    setupEventListeners();
    updateRecordingControlsState();
}

// Check system health (Dropbox connection)
async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const health = await response.json();
        
        if (health.status === 'unavailable' || !health.dropbox_connected) {
            showStatus('⚠️ System unavailable: Dropbox connection failed. Recording is disabled. Please try again later.', 'error');
            disableAllRecordingFeatures();
            return false;
        }
        
        return true;
    } catch (error) {
        console.error('Error checking system health:', error);
        showStatus('⚠️ Cannot connect to server. Please check your connection and try again later.', 'error');
        disableAllRecordingFeatures();
        return false;
    }
}

// Disable all recording features when system is unavailable
function disableAllRecordingFeatures() {
    recordBtn.disabled = true;
    stopBtn.disabled = true;
    submitBtn.disabled = true;
    skipBtn.disabled = true;
    
    recordBtn.style.opacity = '0.5';
    recordBtn.style.cursor = 'not-allowed';
    recordBtn.title = 'System unavailable - Dropbox connection failed';
    
    skipBtn.style.opacity = '0.5';
    skipBtn.style.cursor = 'not-allowed';
}

// Setup event listeners
function setupEventListeners() {
    recordBtn.addEventListener('click', startRecording);
    stopBtn.addEventListener('click', stopRecording);
    submitBtn.addEventListener('click', submitRecording);
    skipBtn.addEventListener('click', loadNextSentence);
    saveNameBtn.addEventListener('click', saveSpeakerName);
    changeNameBtn.addEventListener('click', enableNameEditing);
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const stats = await response.json();
        
        totalSentences.textContent = stats.total_sentences;
        recordedCount.textContent = stats.recorded_count;
        remainingCount.textContent = stats.remaining_count;
        progressPercent.textContent = `${stats.progress_percent}%`;
        progressBar.style.width = `${stats.progress_percent}%`;
        
        // Load personal stats if speaker name is set
        if (speakerName) {
            await loadPersonalStats();
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        showStatus('Error loading statistics', 'error');
    }
}

// Load personal statistics for the current speaker
async function loadPersonalStats() {
    if (!speakerName) {
        personalStatsContainer.style.display = 'none';
        return;
    }
    
    try {
        // Get speaker's personal stats
        const response = await fetch(`${API_BASE_URL}/speaker_stats/${encodeURIComponent(speakerName)}`);
        const speakerStats = await response.json();
        
        // Get all speakers for ranking
        const allSpeakersResponse = await fetch(`${API_BASE_URL}/all_speakers`);
        const allSpeakersData = await allSpeakersResponse.json();
        
        // Get global stats for percentage calculation
        const globalResponse = await fetch(`${API_BASE_URL}/stats`);
        const globalStats = await globalResponse.json();
        
        // Update personal count
        personalCount.textContent = speakerStats.recording_count;
        
        // Calculate and display percentage contribution
        const percentage = globalStats.recorded_count > 0 
            ? ((speakerStats.recording_count / globalStats.recorded_count) * 100).toFixed(1)
            : 0;
        personalPercentage.textContent = `${percentage}%`;
        
        // Find speaker's rank
        const speakers = allSpeakersData.speakers || [];
        const rank = speakers.findIndex(s => s.name === speakerName.replace(/\s/g, '_')) + 1;
        
        if (rank > 0) {
            speakerRank.textContent = `#${rank} of ${speakers.length}`;
        } else {
            speakerRank.textContent = speakerStats.recording_count > 0 ? '#1' : '-';
        }
        
        // Show the personal stats container
        personalStatsContainer.style.display = 'block';
        
        console.log('✅ Personal stats loaded:', speakerStats);
    } catch (error) {
        console.error('Error loading personal stats:', error);
        // Don't show error to user, just hide the stats
        personalStatsContainer.style.display = 'none';
    }
}

// Load next sentence
async function loadNextSentence() {
    try {
        showStatus('Loading next sentence...', 'recording');
        
        const response = await fetch(`${API_BASE_URL}/next_sentence`);
        const data = await response.json();
        
        if (data.completed) {
            showCompletionScreen();
            return;
        }
        
        currentSentence = data.sentence;
        sentenceText.textContent = currentSentence;
        
        // Reset UI
        resetRecordingUI();
        hideStatus();
        
        // Update stats
        await loadStats();
        
    } catch (error) {
        console.error('Error loading sentence:', error);
        showStatus('Error loading sentence. Please check backend connection.', 'error');
    }
}

// Start recording
async function startRecording() {
    // Force username input before recording
    if (!speakerName) {
        showStatus('❌ Please enter your name before recording!', 'error');
        speakerNameInput.focus();
        // Scroll to the speaker name section
        document.getElementById('speakerNameSection').scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
    }
    
    try {
        console.log('🎙️ Starting recording...');
        
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('✅ Microphone access granted');
        
        // Determine best audio format supported by browser
        const mimeTypes = [
            'audio/webm',
            'audio/webm;codecs=opus',
            'audio/ogg;codecs=opus',
            'audio/mp4'
        ];
        
        recordingMimeType = mimeTypes.find(type => MediaRecorder.isTypeSupported(type)) || 'audio/webm';
        console.log('Using MIME type:', recordingMimeType);
        
        // Create media recorder with supported format
        mediaRecorder = new MediaRecorder(stream, { mimeType: recordingMimeType });
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            console.log('📦 Audio data received:', event.data.size, 'bytes');
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = () => {
            console.log('=== MediaRecorder stopped ===');
            console.log('Total audio chunks:', audioChunks.length);
            
            // Create blob from chunks with the correct MIME type
            recordedBlob = new Blob(audioChunks, { type: recordingMimeType });
            console.log('Blob created:', recordedBlob.size, 'bytes');
            
            if (recordedBlob.size === 0) {
                console.error('❌ Recording is empty!');
                showStatus('Recording failed - no audio captured. Please try again.', 'error');
                recordBtn.disabled = false;
                stopBtn.disabled = true;
                return;
            }
            
            // Create URL for playback
            const audioUrl = URL.createObjectURL(recordedBlob);
            console.log('Audio URL created:', audioUrl);
            
            // Set audio source
            audioPlayer.src = audioUrl;
            audioPlayer.load();
            
            // FORCE SHOW - Use setTimeout to ensure DOM is ready
            setTimeout(() => {
                audioPlaybackSection.style.display = 'block';
                audioPlaybackSection.style.visibility = 'visible';
                audioPlaybackSection.style.opacity = '1';
                audioPlayer.style.display = 'block';
                
                console.log('✅ Audio player displayed');
                console.log('Audio section display:', audioPlaybackSection.style.display);
                console.log('Audio player display:', audioPlayer.style.display);
                console.log('Audio player src:', audioPlayer.src);
                
                // Scroll to the audio player so user can see it
                audioPlaybackSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 100);
            
            // Enable submit button
            submitBtn.disabled = false;
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
            
            console.log('=== Audio player should now be visible ===');
        };
        
        // Start recording
        mediaRecorder.start();
        console.log('🔴 Recording started, state:', mediaRecorder.state);
        
        // Track recording start time
        recordingStartTime = Date.now();
        
        // Set automatic stop timer (20 seconds max)
        recordingTimer = setTimeout(() => {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                console.log('⏱️ Maximum recording duration reached (20 seconds) - auto-stopping');
                stopRecording();
                showStatus('⏱️ Recording stopped automatically (20 second limit reached). Listen and submit if good, or record again.', 'success');
            }
        }, MAX_RECORDING_DURATION);
        
        // Update UI
        recordBtn.disabled = true;
        stopBtn.disabled = false;
        submitBtn.disabled = true;
        skipBtn.disabled = true;
        audioPlaybackSection.style.display = 'none';
        
        document.querySelector('.sentence-display').classList.add('recording');
        showStatus('🔴 Recording... Speak clearly! (Max 20 seconds)', 'recording');
        
    } catch (error) {
        console.error('❌ Error starting recording:', error);
        if (error.name === 'NotAllowedError') {
            showStatus('Error: Microphone access denied. Please allow microphone access and try again.', 'error');
        } else if (error.name === 'NotFoundError') {
            showStatus('Error: No microphone found. Please connect a microphone and try again.', 'error');
        } else {
            showStatus('Error: Could not access microphone. ' + error.message, 'error');
        }
    }
}

// Stop recording
function stopRecording() {
    // Clear the auto-stop timer
    if (recordingTimer) {
        clearTimeout(recordingTimer);
        recordingTimer = null;
    }
    
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        console.log('⏹️ Stopping recording...');
        
        // Calculate recording duration
        const duration = recordingStartTime ? Date.now() - recordingStartTime : 0;
        console.log(`Recording duration: ${(duration / 1000).toFixed(1)} seconds`);
        
        mediaRecorder.stop();
        
        // Update UI
        recordBtn.disabled = false;
        stopBtn.disabled = true;
        skipBtn.disabled = false;
        
        document.querySelector('.sentence-display').classList.remove('recording');
        
        // Show duration in status message
        if (duration > 0) {
            const durationText = `${(duration / 1000).toFixed(1)} seconds`;
            showStatus(`✅ Recording stopped! (Duration: ${durationText}) Listen and submit if good, or record again.`, 'success');
        } else {
            showStatus('✅ Recording stopped! Listen and submit if good, or record again.', 'success');
        }
    } else {
        console.warn('⚠️ MediaRecorder not active, state:', mediaRecorder ? mediaRecorder.state : 'null');
    }
}

// Submit recording
async function submitRecording() {
    if (!speakerName) {
        showStatus('❌ Please enter your name before submitting!', 'error');
        speakerNameInput.focus();
        return;
    }
    
    if (!recordedBlob || !currentSentence) {
        console.error('❌ No recording or sentence to submit');
        showStatus('No recording to submit', 'error');
        return;
    }
    
    try {
        console.log('📤 Submitting recording...', recordedBlob.size, 'bytes');
        showStatus('Uploading recording...', 'recording');
        
        // Disable ALL buttons during upload to prevent any interaction
        submitBtn.disabled = true;
        recordBtn.disabled = true;
        stopBtn.disabled = true;
        skipBtn.disabled = true;
        
        // Create form data
        const formData = new FormData();
        formData.append('audio', recordedBlob, 'recording.wav');
        formData.append('sentence', currentSentence);
        formData.append('speaker', speakerName);
        
        console.log('Uploading to:', `${API_BASE_URL}/submit_recording`);
        
        // Submit to backend
        const response = await fetch(`${API_BASE_URL}/submit_recording`, {
            method: 'POST',
            body: formData
        });
        
        console.log('Response status:', response.status);
        const result = await response.json();
        console.log('Response data:', result);
        
        if (result.success) {
            console.log('✅ Recording saved successfully!');
            showStatus('✅ Recording saved successfully!', 'success');
            
            // Wait a moment, then load next sentence
            setTimeout(() => {
                loadNextSentence();
            }, 1500);
        } else {
            console.error('❌ Server returned error:', result);
            showStatus('Error saving recording. Please try again.', 'error');
            
            // Re-enable buttons on error so user can try again
            submitBtn.disabled = false;
            recordBtn.disabled = false;
            skipBtn.disabled = false;
        }
        
    } catch (error) {
        console.error('❌ Error submitting recording:', error);
        showStatus('Error submitting recording. Please try again.', 'error');
        
        // Re-enable buttons on error so user can try again or re-record
        submitBtn.disabled = false;
        recordBtn.disabled = false;
        skipBtn.disabled = false;
    }
}

// Reset recording UI
function resetRecordingUI() {
    recordBtn.disabled = false;
    stopBtn.disabled = true;
    submitBtn.disabled = true;
    skipBtn.disabled = false;
    audioPlaybackSection.style.display = 'none';
    audioPlayer.src = '';
    recordedBlob = null;
    document.querySelector('.sentence-display').classList.remove('recording');
}

// Show status message
function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
    statusMessage.style.display = 'block';
}

// Hide status message
function hideStatus() {
    statusMessage.style.display = 'none';
}

// Show completion screen
function showCompletionScreen() {
    recordingCard.style.display = 'none';
    completionCard.style.display = 'block';
}

// Load speaker name from localStorage
function loadSpeakerName() {
    const savedName = localStorage.getItem('speakerName');
    if (savedName) {
        speakerName = savedName;
        speakerNameDisplay.textContent = savedName;
        currentSpeakerName.style.display = 'block';
        speakerNameInput.style.display = 'none';
        saveNameBtn.style.display = 'none';
        
        // Load personal stats for the saved speaker
        loadPersonalStats();
        updateRecordingControlsState();
    } else {
        currentSpeakerName.style.display = 'none';
        speakerNameInput.style.display = 'block';
        saveNameBtn.style.display = 'block';
        personalStatsContainer.style.display = 'none';
        disableRecordingControls();
    }
}

// Save speaker name to localStorage
async function saveSpeakerName() {
    const name = speakerNameInput.value.trim();
    
    if (!name) {
        showStatus('Please enter a valid name.', 'error');
        speakerNameInput.focus();
        return;
    }
    
    // Validate format: no spaces, hyphens, or special characters
    const hasSpaces = /\s/.test(name);
    const hasHyphens = /-/.test(name);
    const hasSpecialChars = /[^a-zA-Z0-9_]/.test(name);
    
    if (hasSpaces) {
        showStatus('❌ Name cannot contain spaces. Use underscores instead (e.g., "John_Doe")', 'error');
        speakerNameInput.focus();
        return;
    }
    
    if (hasHyphens) {
        showStatus('❌ Name cannot contain hyphens. Use underscores instead (e.g., "John_Doe")', 'error');
        speakerNameInput.focus();
        return;
    }
    
    if (hasSpecialChars) {
        showStatus('❌ Name can only contain letters, numbers, and underscores (e.g., "Robel_123")', 'error');
        speakerNameInput.focus();
        return;
    }
    
    // Check for minimum length
    if (name.length < 2) {
        showStatus('❌ Name must be at least 2 characters long', 'error');
        speakerNameInput.focus();
        return;
    }
    
    // Check if name is already taken by another speaker
    try {
        const response = await fetch(`${API_BASE_URL}/all_speakers`);
        const data = await response.json();
        const existingSpeakers = data.speakers || [];
        
        // Check if this exact name already exists (case-insensitive)
        const existingSpeaker = existingSpeakers.find(speaker => 
            speaker.name.toLowerCase() === name.toLowerCase()
        );
        
        if (existingSpeaker && existingSpeaker.count > 0) {
            // Name exists - this is a returning contributor!
            const confirmResume = confirm(
                `Welcome back! 🎉\n\n` +
                `The name "${name}" already has ${existingSpeaker.count} recording(s).\n\n` +
                `Click OK if this is you and you want to continue recording.\n` +
                `Click Cancel if this is NOT you (choose a different name).`
            );
            
            if (!confirmResume) {
                showStatus(`❌ Name "${name}" is taken. Please choose a different name.`, 'error');
                speakerNameInput.focus();
                return;
            }
            
            // User confirmed - they are resuming their work
            console.log(`✅ Returning contributor: ${name} (${existingSpeaker.count} recordings)`);
            showStatus(`🎉 Welcome back, ${name}! You have ${existingSpeaker.count} recording(s).`, 'success');
        } else {
            // New contributor
            console.log(`✅ New contributor: ${name}`);
            showStatus(`✅ Welcome, ${name}! Let's start recording.`, 'success');
        }
        
        // Save name and proceed
        speakerName = name;
        localStorage.setItem('speakerName', speakerName);
        speakerNameDisplay.textContent = speakerName;
        currentSpeakerName.style.display = 'block';
        speakerNameInput.style.display = 'none';
        saveNameBtn.style.display = 'none';
        
        // Enable recording controls
        updateRecordingControlsState();
        
        // Load personal stats after setting name
        await loadPersonalStats();
        
        setTimeout(hideStatus, 3000);
        
    } catch (error) {
        console.error('Error checking speaker names:', error);
        // If we can't check uniqueness, still allow the name (offline mode)
        speakerName = name;
        localStorage.setItem('speakerName', speakerName);
        speakerNameDisplay.textContent = speakerName;
        currentSpeakerName.style.display = 'block';
        speakerNameInput.style.display = 'none';
        saveNameBtn.style.display = 'none';
        showStatus(`✅ Recording as: ${speakerName}`, 'success');
        
        // Enable recording controls
        updateRecordingControlsState();
        
        await loadPersonalStats();
        setTimeout(hideStatus, 2000);
    }
}

// Enable editing of speaker name
function enableNameEditing() {
    speakerNameInput.value = speakerName;
    currentSpeakerName.style.display = 'none';
    speakerNameInput.style.display = 'block';
    saveNameBtn.style.display = 'block';
    speakerNameInput.focus();
    
    // Disable recording controls while editing name
    disableRecordingControls();
}

// Disable recording controls when no speaker name is set
function disableRecordingControls() {
    recordBtn.disabled = true;
    recordBtn.style.opacity = '0.5';
    recordBtn.style.cursor = 'not-allowed';
    recordBtn.title = 'Please enter your name first';
    
    stopBtn.disabled = true;
    submitBtn.disabled = true;
    skipBtn.disabled = true;
}

// Enable recording controls when speaker name is set
function updateRecordingControlsState() {
    if (speakerName) {
        recordBtn.disabled = false;
        recordBtn.style.opacity = '1';
        recordBtn.style.cursor = 'pointer';
        recordBtn.title = '';
        
        skipBtn.disabled = false;
    } else {
        disableRecordingControls();
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', init);
