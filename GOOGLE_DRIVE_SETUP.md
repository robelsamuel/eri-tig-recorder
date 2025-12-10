# 🔑 Google Drive Credentials Setup Guide

## Step-by-Step Instructions to Get Your `credentials.json`

---

## �� **Step 1: Go to Google Cloud Console**

1. Open your browser and go to: **https://console.cloud.google.com/**
2. Sign in with your Google account (use the account where you want to store recordings)

---


## 🆕 **Step 2: Create a New Project**

1. Click the **project dropdown** at the top (next to "Google Cloud")
2. Click **"NEW PROJECT"** button (top right)
3. Fill in:
   - **Project Name**: `Tigrigna Speech Dataset` (or any name you like)
   - **Location**: Leave as default (No organization)
4. Click **"CREATE"**
5. Wait 10-15 seconds for the project to be created
6. **Select your new project** from the dropdown at the top

---

## 🔌 **Step 3: Enable Google Drive API**

1. In the left sidebar, click **"APIs & Services"** → **"Library"**
   - OR go directly to: https://console.cloud.google.com/apis/library
2. In the search box, type: **"Google Drive API"**
3. Click on **"Google Drive API"** from the results
4. Click the blue **"ENABLE"** button
5. Wait a few seconds for it to enable

---

## 🎫 **Step 4: Create OAuth Consent Screen**

1. In the left sidebar, click **"APIs & Services"** → **"OAuth consent screen"**
   - OR go to: https://console.cloud.google.com/apis/credentials/consent
2. Select **"External"** (unless you have a Google Workspace)
3. Click **"CREATE"**
4. Fill in the required fields:
   - **App name**: `Tigrigna Recorder`
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
5. Click **"SAVE AND CONTINUE"**
6. On **"Scopes"** page: Click **"SAVE AND CONTINUE"** (skip for now)
7. On **"Test users"** page:
   - Click **"+ ADD USERS"**
   - Enter your email address
   - Click **"ADD"**
   - Click **"SAVE AND CONTINUE"**
8. Review and click **"BACK TO DASHBOARD"**

---

## 🔐 **Step 5: Create OAuth Credentials**

1. In the left sidebar, click **"APIs & Services"** → **"Credentials"**
   - OR go to: https://console.cloud.google.com/apis/credentials
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"OAuth client ID"**
4. Configure:
   - **Application type**: Select **"Desktop app"**
   - **Name**: `Tigrigna Recorder Desktop`
5. Click **"CREATE"**
6. A popup will appear with your credentials

---

## 📥 **Step 6: Download credentials.json**

1. In the popup, click **"DOWNLOAD JSON"**
   - OR click the download icon (⬇️) next to your credential in the list
2. The file will be downloaded as something like:
   ```
   client_secret_XXXXX.apps.googleusercontent.com.json
   ```
3. **Rename this file** to `credentials.json`
4. **Move it** to your backend folder:
   ```bash
   mv ~/Downloads/client_secret_*.json /Users/robelgirmatsion/Documents/eri-tig-recorder/backend/credentials.json
   ```

---

## ✅ **Step 7: Verify the File**

Check that the file looks like this:

```bash
cat /Users/robelgirmatsion/Documents/eri-tig-recorder/backend/credentials.json
```

You should see something like:
```json
{
  "installed": {
    "client_id": "123456789-xxxxxxxxxxxxx.apps.googleusercontent.com",
    "project_id": "tigrigna-speech-dataset",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "GOCSPX-xxxxxxxxxxxxxxxxxxxxx",
    "redirect_uris": ["http://localhost"]
  }
}
```

---

## 🔓 **Step 8: Authenticate (First Time Only)**

1. **Restart your backend server**:
   ```bash
   cd /Users/robelgirmatsion/Documents/eri-tig-recorder/backend
   python3 main.py
   ```

2. **A browser window will automatically open** asking you to:
   - Choose your Google account
   - Review permissions
   - Click **"Continue"** (even if it says "Google hasn't verified this app")
   - Click **"Continue"** again on the warning
   - Grant access to **"See, edit, create, and delete all of your Google Drive files"**

3. **Authorization successful!**
   - The browser will show: "The authentication flow has completed"
   - Close the browser tab
   - Check your terminal - you should see:
     ```
     ✅ Successfully authenticated with Google Drive
     ✅ Google Drive backup enabled
     ```

4. **A `token.json` file is created** - this stores your authorization for future use

---

## 🎉 **Step 9: Test It!**

1. **Record a sentence** in your app
2. **Submit the recording**
3. **Check the console output**:
   ```
   Successfully loaded as WebM format
   Saved as proper WAV: clips/1_1765336123_abc4.wav
   ✅ Uploaded 1_1765336123_abc4.wav to Google Drive
   ```

4. **Check your Google Drive**:
   - Go to: https://drive.google.com/
   - Look for a folder: **"Tigrigna Speech Dataset"**
   - Your recording should be there! 🎤

---

## 🔒 **Security Notes**

### ⚠️ **NEVER share or commit these files to GitHub:**
- ❌ `credentials.json` - Contains your app secrets
- ❌ `token.json` - Contains your authorization token

### ✅ **Already protected by `.gitignore`:**
Both files are automatically excluded from git commits.

---

## 🐛 **Troubleshooting**

### **Issue 1: "Credentials file not found"**
**Solution:**
```bash
# Make sure the file is in the right place
ls -la /Users/robelgirmatsion/Documents/eri-tig-recorder/backend/credentials.json

# If not, move it:
mv ~/Downloads/client_secret_*.json /Users/robelgirmatsion/Documents/eri-tig-recorder/backend/credentials.json
```

### **Issue 2: "Access blocked: This app's request is invalid"**
**Solution:**
- Make sure you completed Step 4 (OAuth consent screen)
- Make sure you added yourself as a test user
- Make sure "Application type" is set to "Desktop app" (not "Web application")

### **Issue 3: Browser doesn't open for authentication**
**Solution:**
```bash
# Manually open the URL shown in the terminal
# It will look like: https://accounts.google.com/o/oauth2/auth?client_id=...
```

### **Issue 4: "Invalid grant" or expired token**
**Solution:**
```bash
# Delete the old token and re-authenticate
rm /Users/robelgirmatsion/Documents/eri-tig-recorder/backend/token.json
python3 main.py  # Will prompt for authorization again
```

### **Issue 5: Upload fails silently**
**Solution:**
```bash
# Check your Google Drive quota
# Go to: https://drive.google.com/settings/storage
# Make sure you have free space
```

---

## 📦 **Manual Batch Upload (Optional)**

If you want to upload existing recordings to Google Drive:

```bash
cd /Users/robelgirmatsion/Documents/eri-tig-recorder/backend
python3 google_drive_helper.py
```

This will:
- Authenticate (if not already done)
- Create "Tigrigna Speech Dataset" folder
- Upload all files from `clips/` directory
- Upload `metadata.csv`

---

## 🎯 **Quick Reference**

### **File Locations:**
```
backend/credentials.json       ← Your OAuth credentials (download from Google Cloud)
backend/token.json             ← Auto-generated after first authentication
backend/clips/                 ← Audio files to backup
backend/metadata.csv           ← Dataset metadata
```

### **Important URLs:**
- **Google Cloud Console**: https://console.cloud.google.com/
- **API Library**: https://console.cloud.google.com/apis/library
- **Credentials**: https://console.cloud.google.com/apis/credentials
- **OAuth Consent**: https://console.cloud.google.com/apis/credentials/consent
- **Google Drive**: https://drive.google.com/

---

## ✅ **You're Done!**

Your recordings will now automatically backup to Google Drive every time you submit one! 🎉

---

**Need Help?** Check the troubleshooting section above or open an issue on GitHub.
