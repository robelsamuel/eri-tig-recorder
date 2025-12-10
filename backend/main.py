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

# Import Dropbox helper (optional)
try:
    from dropbox_helper import DropboxUploader
    dropbox_uploader = DropboxUploader()
    DROPBOX_ENABLED = dropbox_uploader.dbx is not None
    if DROPBOX_ENABLED:
        print("✅ Dropbox backup enabled")
except ImportError:
    DROPBOX_ENABLED = False
    dropbox_uploader = None
    print("⚠️ Dropbox integration not available")

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

def sync_with_dropbox():
    """Sync local state and metadata with Dropbox audio files.
    Remove any entries from state/metadata if their audio file is missing from Dropbox."""
    if not DROPBOX_ENABLED:
        return
    
    try:
        print("🔄 Syncing state with Dropbox audio files...")
        
        # Get list of audio files in Dropbox
        dropbox_audio_files = set(dropbox_uploader.get_audio_files())
        print(f"📁 Found {len(dropbox_audio_files)} audio files in Dropbox")
        
        if len(dropbox_audio_files) == 0:
            # No audio files in Dropbox - reset everything
            print("🗑️ No audio files in Dropbox - resetting state and metadata")
            
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({"recorded": []}, f, ensure_ascii=False)
            
            with open(METADATA_FILE, "w", encoding="utf-8") as f:
                f.write("filename|sentence\n")
            
            # Upload the reset files to Dropbox
            dropbox_uploader.upload_file(STATE_FILE)
            dropbox_uploader.upload_file(METADATA_FILE)
            
            print("✅ State and metadata reset and synced to Dropbox")
            return
        
        # Read current metadata
        metadata_lines = []
        metadata_changed = False
        sentences_in_metadata = set()
        
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Keep header
                metadata_lines.append(lines[0] if lines else "filename|sentence\n")
                
                # Check each metadata entry
                for line in lines[1:]:
                    if '|' in line:
                        filepath, sentence = line.strip().split('|', 1)
                        filename = os.path.basename(filepath)
                        
                        # Only keep if audio file exists in Dropbox
                        if filename in dropbox_audio_files:
                            metadata_lines.append(line)
                            sentences_in_metadata.add(sentence)
                        else:
                            metadata_changed = True
                            print(f"🗑️ Removed from metadata: {filename} (missing in Dropbox)")
        
        # Update metadata file if changed
        if metadata_changed or not os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, "w", encoding="utf-8") as f:
                f.writelines(metadata_lines)
            print("✅ Updated metadata.csv")
            
            # Upload updated metadata to Dropbox
            dropbox_uploader.upload_file(METADATA_FILE)
            print("✅ Uploaded updated metadata.csv to Dropbox")
        
        # Update state file - only keep sentences that have audio files
        state = load_state()
        original_recorded = set(state.get("recorded", []))
        synced_recorded = list(sentences_in_metadata)
        
        if set(synced_recorded) != original_recorded:
            state["recorded"] = synced_recorded
            save_state(state)
            
            removed_count = len(original_recorded) - len(synced_recorded)
            print(f"✅ Updated state: removed {removed_count} entries without audio files")
            
            # Upload updated state to Dropbox
            dropbox_uploader.upload_file(STATE_FILE)
            print("✅ Uploaded updated sentence_state.json to Dropbox")
        
        print(f"✅ Sync complete: {len(synced_recorded)} recordings tracked")
        
    except Exception as e:
        print(f"⚠️ Error during sync: {e}")

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
    # First, try to restore state from Dropbox if available
    if DROPBOX_ENABLED:
        print("🔄 Syncing state from Dropbox...")
        
        # Check if state files exist in Dropbox
        state_exists = dropbox_uploader.file_exists("sentence_state.json")
        metadata_exists = dropbox_uploader.file_exists("metadata.csv")
        
        if not state_exists and not metadata_exists:
            # Both files missing from Dropbox - user deleted everything, so reset
            print("🔄 No state files found in Dropbox - resetting to fresh state")
            
            # Delete local files if they exist
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
            if os.path.exists(METADATA_FILE):
                os.remove(METADATA_FILE)
            
            # Initialize fresh state
            init_state()
            print("✅ Reset to fresh state")
        else:
            # Try to download sentence_state.json
            state_downloaded = dropbox_uploader.download_file("sentence_state.json", STATE_FILE)
            if state_downloaded:
                print("✅ Restored sentence_state.json from Dropbox")
            elif state_downloaded is False:
                # File doesn't exist in Dropbox, reset it
                print("⚠️ sentence_state.json not in Dropbox - creating fresh")
                if os.path.exists(STATE_FILE):
                    os.remove(STATE_FILE)
            
            # Try to download metadata.csv
            metadata_downloaded = dropbox_uploader.download_file("metadata.csv", METADATA_FILE)
            if metadata_downloaded:
                print("✅ Restored metadata.csv from Dropbox")
            elif metadata_downloaded is False:
                # File doesn't exist in Dropbox, reset it
                print("⚠️ metadata.csv not in Dropbox - creating fresh")
                if os.path.exists(METADATA_FILE):
                    os.remove(METADATA_FILE)
            
            # Initialize state if files don't exist
            init_state()
            
            # Now sync with actual audio files in Dropbox
            sync_with_dropbox()
    else:
        # Initialize state if files don't exist
        init_state()
    
    # Log current stats
    try:
        state = load_state()
        recorded_count = len(state.get("recorded", []))
        print(f"📊 Current progress: {recorded_count} sentences recorded")
    except Exception as e:
        print(f"⚠️ Error loading state: {e}")

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
    
    print(f"📊 Total sentences: {len(sentences)}, Already recorded: {len(recorded)}")
    
    # Find unrecorded sentences
    unrecorded = [s for s in sentences if s not in recorded]
    
    print(f"📋 Unrecorded sentences remaining: {len(unrecorded)}")
    
    if not unrecorded:
        return {
            "sentence": None,
            "message": "All sentences have been recorded! 🎉",
            "completed": True
        }
    
    # Return a random unrecorded sentence
    sentence = random.choice(unrecorded)
    
    print(f"✅ Selected sentence: {sentence[:50]}...")
    
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
        
        # Optional: Upload to Dropbox
        if DROPBOX_ENABLED:
            try:
                dropbox_uploader.upload_file(filepath)
                print(f"✅ Uploaded {filename} to Dropbox")
                
                # Also upload the updated metadata.csv
                dropbox_uploader.upload_file(METADATA_FILE)
                print(f"✅ Uploaded metadata.csv to Dropbox")
                
                # Also upload the updated sentence_state.json
                dropbox_uploader.upload_file(STATE_FILE)
                print(f"✅ Uploaded sentence_state.json to Dropbox")
            except Exception as e:
                print(f"⚠️ Failed to upload to Dropbox: {e}")
        
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
