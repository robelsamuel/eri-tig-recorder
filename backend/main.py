from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import time
import random
import string
import tempfile

# Try to import pydub for audio conversion (optional)
try:
    from pydub import AudioSegment
    AUDIO_CONVERSION_ENABLED = True
    print("✅ Audio conversion enabled (pydub available)")
except ImportError:
    AUDIO_CONVERSION_ENABLED = False
    print("⚠️ Audio conversion disabled (pydub not available - files will be saved as-is)")

# Import Google Drive helper (optional)
try:
    from google_drive_helper import GoogleDriveUploader
    GOOGLE_DRIVE_ENABLED = True
except ImportError:
    GOOGLE_DRIVE_ENABLED = False
    print("⚠️ Google Drive integration not available. Install dependencies to enable.")

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File paths
SENTENCES_FILE = "sentences.txt"
STATE_FILE = "sentence_state.json"
METADATA_FILE = "metadata.csv"
CLIPS_DIR = "clips"

# Ensure clips directory exists
os.makedirs(CLIPS_DIR, exist_ok=True)

# Initialize state file if it doesn't exist
def init_state():
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"recorded": []}, f, ensure_ascii=False)
    
    # Initialize metadata CSV if it doesn't exist
    if not os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            f.write("filename|sentence\n")

# Load sentences from file
def load_sentences():
    if not os.path.exists(SENTENCES_FILE):
        return []
    with open(SENTENCES_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

# Load recorded state
def load_state():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Save recorded state
def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# Global Google Drive uploader instance
drive_uploader = None
if GOOGLE_DRIVE_ENABLED and os.path.exists('credentials.json'):
    drive_uploader = GoogleDriveUploader()
    try:
        if drive_uploader.authenticate():
            drive_uploader.create_folder('Tigrigna Speech Dataset')
            print("✅ Google Drive backup enabled")
    except Exception as e:
        print(f"⚠️ Google Drive authentication failed: {e}")
        drive_uploader = None

@app.on_event("startup")
async def startup_event():
    init_state()

@app.get("/")
async def root():
    return {"message": "Tigrigna Speech Collection API", "version": "1.0"}

@app.get("/stats")
async def get_stats():
    """Get recording statistics"""
    sentences = load_sentences()
    state = load_state()
    recorded = state.get("recorded", [])
    
    return {
        "total_sentences": len(sentences),
        "recorded_count": len(recorded),
        "remaining_count": len(sentences) - len(recorded),
        "progress_percent": round((len(recorded) / len(sentences) * 100), 2) if sentences else 0
    }

@app.get("/next_sentence")
async def get_next_sentence():
    """Get the next unrecorded sentence"""
    sentences = load_sentences()
    if not sentences:
        raise HTTPException(status_code=404, detail="No sentences found. Please add sentences.txt file.")
    
    state = load_state()
    recorded = set(state.get("recorded", []))
    
    # Find unrecorded sentences
    unrecorded = [s for s in sentences if s not in recorded]
    
    if not unrecorded:
        return {
            "sentence": None,
            "message": "All sentences have been recorded! 🎉",
            "completed": True
        }
    
    # Return a random unrecorded sentence
    sentence = random.choice(unrecorded)
    
    return {
        "sentence": sentence,
        "remaining": len(unrecorded),
        "completed": False
    }

@app.post("/submit_recording")
async def submit_recording(
    audio: UploadFile = File(...),
    sentence: str = Form(...)
):
    """Save audio recording and update metadata"""
    temp_path = None
    try:
        # Generate unique filename
        timestamp = int(time.time())
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        state = load_state()
        sentence_num = len(state.get("recorded", [])) + 1
        
        # Always use .wav extension
        filename = f"{sentence_num}_{timestamp}_{random_id}.wav"
        filepath = os.path.join(CLIPS_DIR, filename)
        
        # Read audio content
        audio_content = await audio.read()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            temp_file.write(audio_content)
            temp_path = temp_file.name
        
        if AUDIO_CONVERSION_ENABLED:
            # Try to convert from WebM format (most common browser format)
            try:
                audio_segment = AudioSegment.from_file(temp_path, format="webm")
                print(f"Successfully loaded as WebM format")
            except:
                # Fallback: Try OGG format
                try:
                    audio_segment = AudioSegment.from_file(temp_path, format="ogg")
                    print(f"Successfully loaded as OGG format")
                except Exception as e:
                    # Last resort: let pydub auto-detect
                    audio_segment = AudioSegment.from_file(temp_path)
                    print(f"Auto-detected format")
            
            # Export as proper WAV file
            audio_segment.export(filepath, format="wav")
            print(f"Saved as proper WAV: {filepath}")
        else:
            # Save the file as-is
            with open(filepath, "wb") as f:
                f.write(audio_content)
            print(f"Saved as-is: {filepath}")
        
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        # Update metadata CSV
        with open(METADATA_FILE, "a", encoding="utf-8") as f:
            f.write(f"{filepath}|{sentence}\n")
        
        # Update state
        recorded = state.get("recorded", [])
        if sentence not in recorded:
            recorded.append(sentence)
            state["recorded"] = recorded
            save_state(state)
        
        # Optional: Upload to Google Drive
        if drive_uploader:
            try:
                drive_uploader.upload_file(filepath, folder_name='Tigrigna Speech Dataset')
                print(f"✅ Uploaded {filename} to Google Drive")
            except Exception as e:
                print(f"⚠️ Failed to upload {filename} to Google Drive: {e}")
        
        return {
            "success": True,
            "filename": filename,
            "message": "Recording saved successfully!"
        }
    
    except Exception as e:
        # Clean up temp file on error
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"Error saving recording: {str(e)}")

@app.post("/reset")
async def reset_progress():
    """Reset all progress (for testing)"""
    try:
        # Reset state
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"recorded": []}, f, ensure_ascii=False)
        
        return {"success": True, "message": "Progress reset successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
