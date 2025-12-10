# 🎤 Tigrigna Speech Collection MVP

A complete web application for collecting Tigrigna speech recordings to build an open speech dataset with automatic Google Drive backup.

## 📋 Features

- ✅ **Simple Recording Interface** - Clean UI for recording sentences
- ✅ **Progress Tracking** - See how many sentences you've recorded
- ✅ **Audio Playback** - Listen before submitting
- ✅ **Proper WAV Format** - Auto-converts browser recordings to WAV
- ✅ **Google Drive Backup** - Optional automatic cloud backup
- ✅ **Metadata Collection** - Automatically saves sentence-audio pairs
- ✅ **Privacy-First** - All data stays on your machine (unless you enable backup)
- ✅ **Free & Open Source** - No paid services required

## 🏗️ Architecture

```
eri-tig-recorder/
├── frontend/              # Web UI (HTML/CSS/JS)
│   ├── index.html        # Main interface
│   ├── styles.css        # Modern styling with animations
│   └── app.js            # Recording logic
├── backend/              # FastAPI server
│   ├── main.py           # API endpoints
│   ├── sentences.txt     # 50 Tigrigna sentences
│   ├── clips/            # Audio files (.wav)
│   ├── metadata.csv      # Dataset metadata
│   ├── sentence_state.json  # Progress tracking
│   ├── google_drive_helper.py  # Google Drive integration
│   └── credentials.json.template  # Google Drive config template
└── README.md
```

## 🚀 Quick Start (Local Development)

### Prerequisites

- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Microphone access
- ffmpeg (for audio conversion) - `brew install ffmpeg` on macOS

### Step 1: Install Backend Dependencies

```bash
cd backend
pip3 install -r requirements.txt
```

### Step 2: Start the Backend Server

```bash
cd backend
python3 main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Google Drive backup enabled (if configured)
```

### Step 3: Open the Frontend

```bash
# macOS
open frontend/index.html

# Or just double-click the file
```

### Step 4: Start Recording!

1. **Grant microphone access** when prompted
2. **Read the sentence** displayed
3. **Click "Start Recording"** 🎙️ and speak clearly
4. **Click "Stop"** ⏹️ when finished
5. **Listen** to your recording in the blue playback box
6. **Submit** ✅ if good, or record again
7. **Repeat** for the next sentence!

---

## ☁️ Google Drive Backup Setup (Optional)

Enable automatic backup of all recordings to Google Drive:

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "Tigrigna Speech Dataset")
3. Enable **Google Drive API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Drive API"
   - Click "Enable"

### Step 2: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Choose "Desktop app" as application type
4. Name it "Tigrigna Recorder"
5. Click "Create"
6. Download the credentials JSON file

### Step 3: Configure Backend

```bash
cd backend

# Rename the downloaded file to credentials.json
mv ~/Downloads/client_secret_*.json credentials.json

# Or copy the template and fill in your details
cp credentials.json.template credentials.json
# Edit credentials.json with your client_id and client_secret
```

### Step 4: Authenticate

```bash
# Restart the backend - it will open a browser for authorization
python3 main.py
```

Follow the browser prompts to authorize access. A `token.json` file will be created for future use.

### Step 5: Verify

After recording a sentence, check the console output:
```
✅ Uploaded 1_1765335833_qjyf.wav to Google Drive
```

Your recordings are now automatically backed up to Google Drive in a folder called "Tigrigna Speech Dataset"!

---

## 🌐 Deployment to Production

### Option 1: Deploy Backend to Render.com (Free)

1. **Create a Render account**: [https://render.com](https://render.com)

2. **Push your code to GitHub**:
```bash
cd /path/to/eri-tig-recorder
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/tigrigna-speech-recorder.git
git push -u origin main
```

3. **Create a new Web Service on Render**:
   - Connect your GitHub repository
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && python main.py`
   - Environment: Python 3.9+
   - Plan: Free

4. **Add Environment Variables** (if using Google Drive):
   - Add your `credentials.json` content as an environment variable
   - Or upload via Render's file system

5. **Get your backend URL**: `https://your-app.onrender.com`

### Option 2: Deploy Frontend to GitHub Pages (Free)

1. **Update API URL** in `frontend/app.js`:
```javascript
const PRODUCTION_API_URL = 'https://your-app.onrender.com';
```

2. **Push to GitHub** and enable GitHub Pages:
```bash
git add .
git commit -m "Update production API URL"
git push
```

3. **Enable GitHub Pages**:
   - Go to repository Settings → Pages
   - Source: Deploy from branch
   - Branch: main, folder: /frontend
   - Save

4. **Access your app**: `https://YOUR_USERNAME.github.io/tigrigna-speech-recorder/`

### Option 3: All-in-One with Railway/Fly.io

Deploy both frontend and backend together on platforms like Railway.app or Fly.io for a simpler setup.

---

## 📊 Dataset Output

### Metadata Format (metadata.csv)

```csv
filename|sentence
clips/1_1733758920_a3f2.wav|መልእኽቲ ትግርኛ ኣብዚ ይኣልቦ
clips/2_1733758945_b7k9.wav|ንስኻ ኣብዚ ተቐሊልካ
```

### Folder Structure

```
backend/
├── clips/
│   ├── 1_1733758920_a3f2.wav  (proper WAV format)
│   ├── 2_1733758945_b7k9.wav
│   └── ...
├── metadata.csv
└── sentence_state.json
```

### Audio Quality

- **Format**: WAV (PCM 16-bit)
- **Sample Rate**: 48kHz (browser default)
- **Channels**: Mono or Stereo
- **Playable in**: VS Code, VLC, QuickTime, Audacity, any media player

---

## 🎯 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info and version |
| `/stats` | GET | Recording statistics (total, recorded, remaining) |
| `/next_sentence` | GET | Get next unrecorded sentence |
| `/submit_recording` | POST | Submit audio + sentence (auto-backup to Drive) |
| `/reset` | POST | Reset progress (testing only) |

---

## 📝 Adding More Sentences

1. Open `backend/sentences.txt`
2. Add one sentence per line (UTF-8 encoding)
3. Restart the backend server
4. New sentences will appear automatically

**Current dataset**: 50 Tigrigna sentences ready to record!

---

## 🔧 Troubleshooting

### Backend Won't Start

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Reinstall dependencies
cd backend
pip3 install --upgrade -r requirements.txt
```

### Microphone Not Working

1. Check browser permissions (Settings → Privacy → Microphone)
2. Try a different browser (Chrome recommended)
3. Restart your browser

### Audio Files Not Opening

The app now automatically converts recordings to proper WAV format. If old files don't open, they're likely WebM format with `.wav` extension. New recordings will work correctly.

### Google Drive Upload Failing

```bash
# Re-authenticate
cd backend
rm token.json
python3 main.py  # Will prompt for authorization again
```

### CORS Errors in Browser

Make sure:
1. Backend is running on `http://localhost:8000`
2. Frontend is opened via `file://` or served properly
3. CORS is enabled in `backend/main.py` (already configured)

---

## 🎨 Customization

### Change UI Colors

Edit `frontend/styles.css`:
```css
/* Header gradient */
body {
    background: linear-gradient(135deg, #YOUR_COLOR_1 0%, #YOUR_COLOR_2 100%);
}
```

### Change Backend Port

Edit `backend/main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # Change port here
```

Then update `frontend/app.js`:
```javascript
const API_BASE_URL = 'http://localhost:YOUR_PORT';
```

### Disable Google Drive Backup

Simply don't create `credentials.json` - the app works perfectly without it!

---

## 📦 Batch Upload to Google Drive

If you want to upload existing recordings manually:

```bash
cd backend
python3 google_drive_helper.py
```

This will:
- Authenticate with Google Drive
- Create "Tigrigna Speech Dataset" folder
- Upload all files from `clips/` directory
- Upload `metadata.csv`

---

## 🎯 Project Roadmap

### ✅ Phase 1 - Core Features (Complete)
- [x] Recording interface
- [x] Audio playback
- [x] Progress tracking
- [x] WAV format conversion
- [x] Google Drive backup

### 🚀 Phase 2 - User Management
- [ ] Speaker ID/name collection
- [ ] Age/gender metadata (optional)
- [ ] Multi-user support

### 📊 Phase 3 - Data Quality
- [ ] Audio validation (duration, volume, noise)
- [ ] Quality scoring
- [ ] Duplicate detection

### ☁️ Phase 4 - Advanced Features
- [ ] Sentence difficulty rating
- [ ] Daily recording goals
- [ ] Family leaderboard
- [ ] Export to Common Voice format

---

## 🤝 Contributing

This is a family language preservation project! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - Feel free to use and modify for your language preservation projects!

---

## 🙏 Acknowledgments

- Built with love for the Tigrigna language community 🇪🇷
- Inspired by Mozilla Common Voice
- Uses free, open-source tools: FastAPI, pydub, Google Drive API

---

## 📞 Support

Having issues?
- Check the [Troubleshooting](#-troubleshooting) section
- Open an issue on GitHub
- Contact the maintainer

---

## 🎉 Current Progress

**50 Sentences Available** | **Ready to Record** | **Let's Preserve Tigrigna!** 🎤

---

**Built for family language preservation** | **100% Free & Open Source** | **Privacy-First Design**
