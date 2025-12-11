#!/usr/bin/env python3
"""

Script to generate a Dropbox refresh token that never expires.
Run this once to get your permanent credentials.
"""

import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect

print("🔐 Dropbox Refresh Token Generator")
print("=" * 50)
print("\nThis will generate a refresh token that never expires!")
print("\nFirst, get your App Key and App Secret:")
print("1. Go to: https://www.dropbox.com/developers/apps")
print("2. Select your app (or create one)")
print("3. Go to Settings tab")
print("4. Find 'App key' and 'App secret'\n")

# Get credentials from user
APP_KEY = input("Enter your App Key: ").strip()
APP_SECRET = input("Enter your App Secret: ").strip()

if not APP_KEY or not APP_SECRET:
    print("❌ Error: App Key and App Secret are required!")
    exit(1)

try:
    # Start OAuth flow with offline access (gives refresh token)
    auth_flow = DropboxOAuth2FlowNoRedirect(
        APP_KEY, 
        APP_SECRET,
        token_access_type='offline'
    )

    # Get authorization URL
    authorize_url = auth_flow.start()
    
    print("\n" + "=" * 50)
    print("📋 STEP 1: Authorize the app")
    print("=" * 50)
    print(f"\n1. Open this URL in your browser:\n   {authorize_url}\n")
    print("2. Click 'Allow' to authorize the app")
    print("3. You'll see an authorization code")
    print("4. Copy the code and paste it below\n")

    # Get the authorization code from user
    auth_code = input("Enter the authorization code: ").strip()

    if not auth_code:
        print("❌ Error: Authorization code is required!")
        exit(1)

    # Exchange for refresh token
    print("\n🔄 Exchanging authorization code for refresh token...")
    oauth_result = auth_flow.finish(auth_code)
    
    print("\n" + "=" * 50)
    print("✅ SUCCESS! Your refresh token is ready!")
    print("=" * 50)
    print("\n📝 Add these lines to your .env file:\n")
    print("-" * 50)
    print(f"DROPBOX_APP_KEY={APP_KEY}")
    print(f"DROPBOX_APP_SECRET={APP_SECRET}")
    print(f"DROPBOX_REFRESH_TOKEN={oauth_result.refresh_token}")
    print(f"DROPBOX_FOLDER_PATH=/tigrigna_datasets")
    print("-" * 50)
    
    print("\n💡 This refresh token will NEVER expire!")
    print("🔒 Keep these credentials secret - don't commit to git!")
    
    # Test the connection
    print("\n🧪 Testing connection...")
    dbx = dropbox.Dropbox(
        oauth2_refresh_token=oauth_result.refresh_token,
        app_key=APP_KEY,
        app_secret=APP_SECRET
    )
    account = dbx.users_get_current_account()
    print(f"✅ Successfully connected as: {account.name.display_name}")
    print(f"📧 Email: {account.email}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n💡 Common issues:")
    print("   - Make sure you copied the authorization code correctly")
    print("   - Check that your App Key and App Secret are correct")
    print("   - Ensure your app has the required permissions")
    exit(1)

print("\n🎉 Setup complete! Restart your backend to use the new credentials.")
