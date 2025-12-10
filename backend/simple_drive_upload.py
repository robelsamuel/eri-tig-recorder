"""

Simple Google Drive uploader using PyDrive (no billing required)
This method uses OAuth2 authentication with your Gmail account directly.

Setup Instructions:
1. Install PyDrive: pip install PyDrive
2. Run this script once to authorize: python simple_drive_upload.py
3. A browser will open - sign in with your Gmail
4. Grant permissions
5. Files will be uploaded to your Gmail's Google Drive automatically
"""

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

class SimpleDriveUploader:
    def __init__(self):
        """Initialize Google Drive connection using PyDrive"""
        self.drive = None
        self.folder_id = None
        
    def authenticate(self):
        """Authenticate using Gmail account (opens browser once)"""
        try:
            gauth = GoogleAuth()
            
            # Try to load saved credentials
            gauth.LoadCredentialsFile("drive_credentials.txt")
            
            if gauth.credentials is None:
                # Authenticate if they're not there
                print("🔐 Opening browser for Gmail authentication...")
                gauth.LocalWebserverAuth()
            elif gauth.access_token_expired:
                # Refresh them if expired
                gauth.Refresh()
            else:
                # Initialize the saved credentials
                gauth.Authorize()
            
            # Save credentials for next run
            gauth.SaveCredentialsFile("drive_credentials.txt")
            
            self.drive = GoogleDrive(gauth)
            print("✅ Successfully connected to your Gmail's Google Drive!")
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def create_or_find_folder(self, folder_name='Tigrigna Speech Dataset'):
        """Create or find the recordings folder in Google Drive"""
        if not self.drive:
            return None
        
        try:
            # Search for existing folder
            file_list = self.drive.ListFile({
                'q': f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            }).GetList()
            
            if file_list:
                self.folder_id = file_list[0]['id']
                print(f"✅ Found existing folder: {folder_name}")
            else:
                # Create new folder
                folder_metadata = {
                    'title': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.drive.CreateFile(folder_metadata)
                folder.Upload()
                self.folder_id = folder['id']
                print(f"✅ Created new folder: {folder_name}")
            
            return self.folder_id
            
        except Exception as e:
            print(f"❌ Error with folder: {e}")
            return None
    
    def upload_file(self, file_path):
        """Upload a file to Google Drive"""
        if not self.drive or not self.folder_id:
            print("❌ Not authenticated or folder not set")
            return False
        
        try:
            file_name = os.path.basename(file_path)
            
            # Create file in Drive
            file_drive = self.drive.CreateFile({
                'title': file_name,
                'parents': [{'id': self.folder_id}]
            })
            
            # Upload the file
            file_drive.SetContentFile(file_path)
            file_drive.Upload()
            
            print(f"✅ Uploaded: {file_name}")
            return True
            
        except Exception as e:
            print(f"❌ Upload failed for {file_path}: {e}")
            return False
    
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


# Example usage and test
if __name__ == "__main__":
    print("🎤 Tigrigna Speech Dataset - Google Drive Uploader")
    print("=" * 50)
    
    uploader = SimpleDriveUploader()
    
    # Authenticate
    if uploader.authenticate():
        # Create/find folder
        if uploader.create_or_find_folder('Tigrigna Speech Dataset'):
            # Upload all clips
            uploaded = uploader.upload_directory('clips')
            print(f"\n✅ Uploaded {uploaded} files to your Gmail's Google Drive!")
            
            # Upload metadata if it exists
            if os.path.exists('metadata.csv'):
                uploader.upload_file('metadata.csv')
                print("✅ Uploaded metadata.csv")
        else:
            print("❌ Could not create/find folder")
    else:
        print("❌ Authentication failed")
