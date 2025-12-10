# 🚀 Deployment Checklist

## ✅ Pre-Deployment Tasks

### 1. Clean Start (DONE ✅)
- [x] Remove old audio files
- [x] Reset metadata.csv
- [x] Reset sentence_state.json
- [x] Create .gitignore file

### 2. Google Drive Setup (Optional)
- [ ] Create Google Cloud project
- [ ] Enable Google Drive API
- [ ] Download credentials.json
- [ ] Place credentials.json in backend/ folder (DO NOT commit to git!)
- [ ] Test authentication: `cd backend && python3 main.py`
- [ ] Verify auto-upload is working

### 3. Code Preparation
- [x] Update requirements.txt with all dependencies
- [x] Add Google Drive integration
- [x] Add WAV conversion (pydub)
- [x] Add environment detection (dev vs production)
- [x] Improve UI with animations

## 📦 GitHub Repository Setup

### 1. Initialize Git Repository
```bash
cd /path/to/eri-tig-recorder
git init
git add .
git commit -m "Initial commit: Tigrigna Speech Collection MVP"
```

### 2. Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `tigrigna-speech-recorder`
3. Description: "Open-source Tigrigna speech dataset collection tool"
4. Public repository (for open source)
5. Don't initialize with README (we have one)
6. Click "Create repository"

### 3. Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/tigrigna-speech-recorder.git
git branch -M main
git push -u origin main
```

## 🌐 Backend Deployment (Render.com)

### 1. Prepare for Render
```bash
# Make sure requirements.txt is up to date
cd backend
pip3 freeze > requirements.txt
```

### 2. Deploy to Render
1. Go to https://render.com/
2. Sign up/Login with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: tigrigna-speech-api
   - **Root Directory**: backend
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
6. Click "Create Web Service"
7. Wait 5-10 minutes for deployment
8. Copy your backend URL: `https://tigrigna-speech-api.onrender.com`

### 3. Add Google Drive Credentials (Optional)
- Go to Environment → Add Secret File
- Name: `credentials.json`
- Paste your credentials JSON content
- Save

## 🎨 Frontend Deployment (GitHub Pages)

### 1. Update Production API URL
Edit `frontend/app.js`:
```javascript
const PRODUCTION_API_URL = 'https://YOUR-APP.onrender.com';
```

### 2. Commit Changes
```bash
git add frontend/app.js
git commit -m "Update production API URL"
git push
```

### 3. Enable GitHub Pages
1. Go to repository → Settings → Pages
2. Source: "Deploy from a branch"
3. Branch: `main`
4. Folder: `/frontend`
5. Click "Save"
6. Wait 1-2 minutes

### 4. Access Your App
Visit: `https://YOUR_USERNAME.github.io/tigrigna-speech-recorder/`

## 🧪 Testing Checklist

### Local Testing
- [ ] Backend starts without errors
- [ ] Frontend opens successfully
- [ ] Can record audio
- [ ] Audio player appears after recording
- [ ] Can submit recording
- [ ] Recording saves as proper WAV file
- [ ] Can open WAV file in VS Code/VLC
- [ ] Stats update correctly
- [ ] Progress bar moves
- [ ] Google Drive upload works (if enabled)

### Production Testing
- [ ] Frontend loads from GitHub Pages
- [ ] Can connect to backend API
- [ ] No CORS errors in browser console
- [ ] All features work as in local
- [ ] Google Drive backup works (if configured)

## 📋 Post-Deployment

### 1. Share with Family
- Send GitHub Pages URL
- Provide recording instructions
- Set up Google Drive sharing (if used)

### 2. Monitor Usage
- Check Render logs for errors
- Monitor Google Drive folder
- Track recording progress

### 3. Backup Strategy
- **Option 1**: Google Drive auto-backup (recommended)
- **Option 2**: Manual download from Render
- **Option 3**: Regular git commits of metadata

## 🔐 Security Notes

### Files to NEVER Commit to GitHub:
- ❌ `backend/credentials.json` (Google Drive credentials)
- ❌ `backend/token.json` (Google Drive auth token)
- ❌ Any `.wav` audio files with personal data

### Already Protected by .gitignore:
- ✅ credentials.json
- ✅ token.json
- ✅ clips/*.wav
- ✅ sentence_state.json (contains progress, safe to exclude)

## 📞 Support & Next Steps

### If Issues Occur:
1. Check backend logs on Render dashboard
2. Check browser console for JavaScript errors
3. Verify CORS is enabled on backend
4. Ensure API URL is correct in frontend

### Future Enhancements:
- Add user authentication
- Implement speaker metadata collection
- Add audio quality validation
- Create dataset export tool
- Build family leaderboard

---

**Ready to deploy? Start with step 1 of GitHub Repository Setup!** 🚀
