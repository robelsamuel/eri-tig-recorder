"""
Google Drive Helper for automatic backup of audio recordings.


Setup Instructions:
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable Google Drive API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials and save as 'credentials.json' in backend folder
6. First run will open browser for authorization
7. Token will be saved as 'token.json' for future use
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pickle

# Google Drive API scope
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveUploader:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        """Initialize Google Drive uploader with credentials"""
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.folder_id = None
        
    def authenticate(self):
        """Authenticate with Google Drive API"""
        creds = None
        
        # Check if token file exists
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"❌ Credentials file not found: {self.credentials_file}")
                    print("Please follow setup instructions in google_drive_helper.py")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
        print("✅ Successfully authenticated with Google Drive")
        return True
    
    def create_folder(self, folder_name='Tigrigna Speech Dataset'):
        """Create or find the backup folder in Google Drive"""
        if not self.service:
            return None
        
        try:
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, spaces='drive').execute()
            items = results.get('files', [])
            
            if items:
                self.folder_id = items[0]['id']
                print(f"✅ Found existing folder: {folder_name}")
            else:
                # Create new folder
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(body=file_metadata, fields='id').execute()
                self.folder_id = folder.get('id')
                print(f"✅ Created new folder: {folder_name}")
            
            return self.folder_id
        
        except Exception as e:
            print(f"❌ Error creating/finding folder: {e}")
            return None
    
    def upload_file(self, file_path, folder_id=None):
        """Upload a file to Google Drive"""
        if not self.service:
            print("❌ Not authenticated. Call authenticate() first.")
            return None
        
        try:
            file_name = os.path.basename(file_path)
            
            file_metadata = {
                'name': file_name
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            print(f"✅ Uploaded: {file_name} (ID: {file.get('id')})")
            return file.get('id'), file.get('webViewLink')
        
        except Exception as e:
            print(f"❌ Error uploading {file_path}: {e}")
            return None
    
    def upload_directory(self, directory_path, folder_id=None):
        """Upload all files from a directory to Google Drive"""
        if not os.path.exists(directory_path):
            print(f"❌ Directory not found: {directory_path}")
            return []
        
        uploaded_files = []
        
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            
            if os.path.isfile(file_path):
                result = self.upload_file(file_path, folder_id)
                if result:
                    uploaded_files.append((filename, result[0], result[1]))
        
        return uploaded_files


# Example usage:
if __name__ == "__main__":
    # Initialize uploader
    uploader = GoogleDriveUploader()
    
    # Authenticate
    if uploader.authenticate():
        # Create/find folder
        folder_id = uploader.create_folder('Tigrigna Speech Dataset')
        
        # Upload all clips
        if folder_id:
            uploaded = uploader.upload_directory('clips', folder_id)
            print(f"\n✅ Uploaded {len(uploaded)} files to Google Drive")
            
            # Also upload metadata
            if os.path.exists('metadata.csv'):
                uploader.upload_file('metadata.csv', folder_id)
                print("✅ Uploaded metadata.csv")
