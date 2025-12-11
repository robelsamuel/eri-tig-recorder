# 🔐 Dropbox Token Setup Guide

## Why Your Token Expires

Dropbox has two types of access tokens:


1. **Short-lived tokens** - Expire after 4 hours (what you're currently using)
2. **Refresh tokens** - Never expire and auto-renew access tokens

## Solution Options

### Option 1: Get a Long-Lived Access Token (Quick Fix)

This is the easiest solution for personal use:

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Select your app (or create a new one if needed)
3. Go to **Settings** tab
4. Scroll to **"OAuth 2"** section
5. Under **"Generated access token"**, click **"Generate"**
6. ⚠️ **IMPORTANT**: Make sure the token type is set to **"No expiration"** or **"Legacy long-lived token"**
7. Copy the token and add it to your `.env` file:

```bash
DROPBOX_ACCESS_TOKEN=your_long_lived_token_here
DROPBOX_FOLDER_PATH=/tigrigna_datasets
```

### Option 2: Use OAuth Refresh Token (Recommended for Production)

This is more secure and is the recommended approach:

#### Step 1: Get Your App Credentials

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Select your app
3. Go to **Settings** tab
4. Find your **App key** and **App secret**

#### Step 2: Generate a Refresh Token

Run this Python script to get your refresh token:

```python
# save as get_dropbox_refresh_token.py
import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect

# Replace with your app credentials
APP_KEY = 'your_app_key_here'
APP_SECRET = 'your_app_secret_here'

# Start OAuth flow
auth_flow = DropboxOAuth2FlowNoRedirect(
    APP_KEY, 
    APP_SECRET,
    token_access_type='offline'  # This gives us a refresh token
)

# Get authorization URL
authorize_url = auth_flow.start()
print("1. Go to:", authorize_url)
print("2. Click 'Allow' (you might need to log in first)")
print("3. Copy the authorization code")

# Get the authorization code from user
auth_code = input("Enter the authorization code here: ").strip()

# Exchange for refresh token
try:
    oauth_result = auth_flow.finish(auth_code)
    print("\n✅ SUCCESS! Add these to your .env file:")
    print(f"\nDROPBOX_APP_KEY={APP_KEY}")
    print(f"DROPBOX_APP_SECRET={APP_SECRET}")
    print(f"DROPBOX_REFRESH_TOKEN={oauth_result.refresh_token}")
    print(f"DROPBOX_FOLDER_PATH=/tigrigna_datasets")
except Exception as e:
    print(f"❌ Error: {e}")
```

#### Step 3: Run the Script

```bash
cd backend
python3 get_dropbox_refresh_token.py
```

#### Step 4: Update Your .env File

Add the credentials to your `.env` file:

```bash
# Dropbox OAuth Credentials (Recommended - tokens never expire)
DROPBOX_APP_KEY=your_app_key
DROPBOX_APP_SECRET=your_app_secret
DROPBOX_REFRESH_TOKEN=your_refresh_token
DROPBOX_FOLDER_PATH=/tigrigna_datasets

# Legacy method (will expire after 4 hours)
# DROPBOX_ACCESS_TOKEN=your_access_token
```

## How the Updated Code Works

The updated `dropbox_helper.py` now:

1. ✅ **First tries refresh token** (never expires)
2. ✅ **Falls back to access token** (with warning)
3. ✅ **Auto-retries on auth errors** (handles token refresh automatically)
4. ✅ **Shows helpful error messages** when tokens expire

## Testing Your Setup

```bash
cd backend
python3 -c "from dropbox_helper import DropboxUploader; u = DropboxUploader(); print('✅ Connected!' if u.dbx else '❌ Failed')"
```

You should see:
- `✅ Connected to Dropbox with refresh token!` (best)
- `✅ Connected to Dropbox with access token!` (temporary)

## Troubleshooting

### "Access token expired"
- You're using a short-lived token
- Follow Option 1 or 2 above to get a permanent solution

### "App key or secret not found"
- Make sure all credentials are in your `.env` file
- Check for typos in variable names

### "Invalid refresh token"
- Your refresh token might be revoked
- Re-run `get_dropbox_refresh_token.py` to get a new one

### Still having issues?
- Make sure your `.env` file is in the `backend/` directory
- Restart your backend after updating `.env`
- Check that `python-dotenv` is installed: `pip install python-dotenv`

## Security Notes

⚠️ **Never commit tokens to git!**

Add to your `.gitignore`:
```
.env
*.env
token.json
credentials.json
```

✅ **For production (Render.com):**
- Add tokens as environment variables in Render dashboard
- Don't use `.env` file in production
- Keep `APP_SECRET` and tokens private

## Quick Reference

| Method | Duration | Best For |
|--------|----------|----------|
| Short-lived token | 4 hours | Testing only |
| Long-lived token | Forever | Personal use |
| Refresh token | Forever | Production apps |

---

**Updated**: December 2025
**Status**: ✅ Your code now supports all three methods!
