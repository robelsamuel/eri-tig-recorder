"""
Dropbox Helper for automatic backup of audio recordings.
Uses your Dropbox account to store recordings permanently.
Supports both long-lived tokens and OAuth refresh tokens.
"""

import dropbox
from dropbox.exceptions import ApiError, AuthError
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

class DropboxUploader:
    def __init__(self):
        """Initialize Dropbox connection"""
        self.access_token = os.getenv('DROPBOX_ACCESS_TOKEN')
        self.refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')
        self.app_key = os.getenv('DROPBOX_APP_KEY')
        self.app_secret = os.getenv('DROPBOX_APP_SECRET')
        self.folder_path = os.getenv('DROPBOX_FOLDER_PATH', '/tigrigna_datasets')
        self.dbx = None
        
        # Try to initialize connection
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Dropbox connection with refresh token support"""
        # Option 1: Use refresh token (recommended)
        if self.refresh_token and self.app_key and self.app_secret:
            try:
                self.dbx = dropbox.Dropbox(
                    oauth2_refresh_token=self.refresh_token,
                    app_key=self.app_key,
                    app_secret=self.app_secret
                )
                # Test the connection
                self.dbx.users_get_current_account()
                print(f"✅ Connected to Dropbox with refresh token! Folder: {self.folder_path}")
                return
            except Exception as e:
                print(f"❌ Dropbox refresh token connection failed: {e}")
                self.dbx = None
        
        # Option 2: Use access token (will expire)
        if self.access_token:
            try:
                self.dbx = dropbox.Dropbox(self.access_token)
                # Test the connection
                self.dbx.users_get_current_account()
                print(f"✅ Connected to Dropbox with access token! Folder: {self.folder_path}")
                print("⚠️  WARNING: Using short-lived access token. Use refresh token for production.")
            except AuthError as e:
                print(f"❌ Dropbox access token expired or invalid: {e}")
                print("💡 Generate a new token or use refresh token instead")
                self.dbx = None
            except Exception as e:
                print(f"❌ Dropbox connection failed: {e}")
                self.dbx = None
        else:
            print("⚠️ Dropbox credentials not found in .env file")
    
    def _retry_on_auth_error(self, func, *args, **kwargs):
        """Retry operation if auth error occurs (token might have expired)"""
        try:
            return func(*args, **kwargs)
        except AuthError as e:
            print(f"⚠️ Auth error, attempting to reconnect: {e}")
            self._initialize_connection()
            if self.dbx:
                return func(*args, **kwargs)
            raise
    
    def upload_file(self, local_file_path):
        """Upload a file to Dropbox"""
        if not self.dbx:
            return False
        
        try:
            file_name = os.path.basename(local_file_path)
            dropbox_path = f"{self.folder_path}/{file_name}"
            
            with open(local_file_path, 'rb') as f:
                # Upload file with retry on auth error
                self._retry_on_auth_error(
                    self.dbx.files_upload,
                    f.read(),
                    dropbox_path,
                    mode=dropbox.files.WriteMode.overwrite
                )
            
            print(f"✅ Uploaded to Dropbox: {file_name}")
            return True
            
        except ApiError as e:
            print(f"❌ Dropbox upload failed for {local_file_path}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error uploading {local_file_path}: {e}")
            return False
    
    def download_file(self, dropbox_filename, local_file_path):
        """Download a file from Dropbox. Returns True if downloaded, False if file doesn't exist or error."""
        if not self.dbx:
            return None  # Dropbox not configured
        
        try:
            dropbox_path = f"{self.folder_path}/{dropbox_filename}"
            
            # Download file with retry on auth error
            metadata, res = self._retry_on_auth_error(
                self.dbx.files_download,
                dropbox_path
            )
            
            # Save to local file
            with open(local_file_path, 'wb') as f:
                f.write(res.content)
            
            print(f"✅ Downloaded from Dropbox: {dropbox_filename}")
            return True
            
        except ApiError as e:
            if e.error.is_path() and e.error.get_path().is_not_found():
                print(f"⚠️ File not found in Dropbox: {dropbox_filename}")
                return False  # File doesn't exist
            else:
                print(f"❌ Dropbox download failed for {dropbox_filename}: {e}")
                return None  # Error occurred
        except Exception as e:
            print(f"❌ Error downloading {dropbox_filename}: {e}")
            return None  # Error occurred
    
    def file_exists(self, dropbox_filename):
        """Check if a file exists in Dropbox"""
        if not self.dbx:
            return False
        
        try:
            dropbox_path = f"{self.folder_path}/{dropbox_filename}"
            self._retry_on_auth_error(
                self.dbx.files_get_metadata,
                dropbox_path
            )
            return True
        except ApiError as e:
            if e.error.is_path():
                return False
            # Log other API errors but don't crash
            print(f"⚠️ Dropbox API error checking {dropbox_filename}: {e}")
            return False
        except Exception as e:
            print(f"⚠️ Error checking file existence for {dropbox_filename}: {e}")
            return False
    
    def get_audio_files(self):
        """Get list of all audio files (.wav) in Dropbox folder"""
        if not self.dbx:
            return []
        
        try:
            result = self._retry_on_auth_error(
                self.dbx.files_list_folder,
                self.folder_path
            )
            audio_files = [
                entry.name for entry in result.entries 
                if isinstance(entry, dropbox.files.FileMetadata) and entry.name.endswith('.wav')
            ]
            return audio_files
        except Exception as e:
            print(f"❌ Error listing audio files: {e}")
            return []
    
    def upload_directory(self, directory_path):
        """Upload all files from a directory"""
        if not os.path.exists(directory_path):
            print(f"❌ Directory not found: {directory_path}")
            return 0
        
        uploaded_count = 0
        
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            
            if os.path.isfile(file_path):
                if self.upload_file(file_path):
                    uploaded_count += 1
        
        return uploaded_count
    
    def list_files(self):
        """List all files in the Dropbox folder"""
        if not self.dbx:
            return []
        
        try:
            result = self._retry_on_auth_error(
                self.dbx.files_list_folder,
                self.folder_path
            )
            files = [entry.name for entry in result.entries]
            return files
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []


# Test script
if __name__ == "__main__":
    print("🎤 Tigrigna Speech Dataset - Dropbox Uploader")
    print("=" * 50)
    
    uploader = DropboxUploader()
    
    if uploader.dbx:
        # Upload all clips
        uploaded = uploader.upload_directory('clips')
        print(f"\n✅ Uploaded {uploaded} files to Dropbox!")
        
        # Upload metadata if it exists
        if os.path.exists('metadata.csv'):
            uploader.upload_file('metadata.csv')
            print("✅ Uploaded metadata.csv")
        
        # List files in Dropbox
        print("\n📁 Files in Dropbox:")
        files = uploader.list_files()
        for f in files:
            print(f"  - {f}")
    else:
        print("❌ Could not connect to Dropbox")
