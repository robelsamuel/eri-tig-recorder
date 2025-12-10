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

// Initialize app
async function init() {
    await loadStats();
    await loadNextSentence();
    setupEventListeners();
}

// Setup event listeners
function setupEventListeners() {
    recordBtn.addEventListener('click', startRecording);
    stopBtn.addEventListener('click', stopRecording);
    submitBtn.addEventListener('click', submitRecording);
    skipBtn.addEventListener('click', loadNextSentence);
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
    } catch (error) {
        console.error('Error loading stats:', error);
        showStatus('Error loading statistics', 'error');
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
    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
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
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = () => {
            console.log('=== MediaRecorder stopped ===');
            
            // Create blob from chunks with the correct MIME type
            recordedBlob = new Blob(audioChunks, { type: recordingMimeType });
            console.log('Blob created:', recordedBlob.size, 'bytes');
            
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
        
        // Update UI
        recordBtn.disabled = true;
        stopBtn.disabled = false;
        submitBtn.disabled = true;
        skipBtn.disabled = true;
        audioPlayer.style.display = 'none';
        
        document.querySelector('.sentence-display').classList.add('recording');
        showStatus('🔴 Recording... Speak clearly!', 'recording');
        
    } catch (error) {
        console.error('Error starting recording:', error);
        showStatus('Error: Could not access microphone. Please allow microphone access.', 'error');
    }
}

// Stop recording
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        
        // Update UI
        recordBtn.disabled = false;
        stopBtn.disabled = true;
        skipBtn.disabled = false;
        
        // Show audio playback section
        audioPlaybackSection.style.display = 'block';
        
        document.querySelector('.sentence-display').classList.remove('recording');
        showStatus('✅ Recording stopped! Listen and submit if good, or record again.', 'success');
    }
}

// Submit recording
async function submitRecording() {
    if (!recordedBlob || !currentSentence) {
        showStatus('No recording to submit', 'error');
        return;
    }
    
    try {
        showStatus('Uploading recording...', 'recording');
        submitBtn.disabled = true;
        
        // Create form data
        const formData = new FormData();
        formData.append('audio', recordedBlob, 'recording.wav');
        formData.append('sentence', currentSentence);
        
        // Submit to backend
        const response = await fetch(`${API_BASE_URL}/submit_recording`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('✅ Recording saved successfully!', 'success');
            
            // Wait a moment, then load next sentence
            setTimeout(() => {
                loadNextSentence();
            }, 1500);
        } else {
            showStatus('Error saving recording', 'error');
            submitBtn.disabled = false;
        }
        
    } catch (error) {
        console.error('Error submitting recording:', error);
        showStatus('Error submitting recording. Please try again.', 'error');
        submitBtn.disabled = false;
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

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', init);
