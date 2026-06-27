import traceback
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class GoogleDriveTools:
    def __init__(self, credentials_json):
        # The frontend/firebase sends a json string of the credentials
        if isinstance(credentials_json, str):
            creds_data = json.loads(credentials_json)
            self.credentials = Credentials.from_authorized_user_info(creds_data)
        else:
            self.credentials = credentials_json
            
        self.service = build('drive', 'v3', credentials=self.credentials)

    def search_drive(self, query=""):
        """Search the user's Google Drive. 'query' uses standard Drive API search syntax."""
        print(f"Executing GoogleDriveTools.search_drive with: {query}")
        try:
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, parents)',
                pageSize=20
            ).execute()
            items = results.get('files', [])
            return {"status": "success", "files": items}
        except Exception as e:
            traceback.print_exc()
            return {"status": "error", "message": f"Failed to search Drive: {str(e)}"}

    def get_folder_contents(self, folder_id):
        """List all files and folders inside a specific folder ID."""
        print(f"Executing GoogleDriveTools.get_folder_contents for folder: {folder_id}")
        query = f"'{folder_id}' in parents and trashed = false"
        return self.search_drive(query)

    def create_folder(self, folder_name, parent_folder_id=None):
        """Create a new folder in Drive. Optionally inside a parent_folder_id."""
        print(f"Executing GoogleDriveTools.create_folder: {folder_name}")
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
                
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            return {"status": "success", "folder_id": folder.get('id'), "message": f"Created folder '{folder_name}'"}
        except Exception as e:
            traceback.print_exc()
            return {"status": "error", "message": f"Failed to create folder: {str(e)}"}

    def move_file(self, file_id, new_parent_id):
        """Move a file to a new folder by updating its parents."""
        print(f"Executing GoogleDriveTools.move_file: file {file_id} to folder {new_parent_id}")
        try:
            # Retrieve the existing parents to remove
            file = self.service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents', []))
            
            # Move the file to the new folder
            updated_file = self.service.files().update(
                fileId=file_id,
                addParents=new_parent_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            
            return {"status": "success", "message": f"Successfully moved file {file_id} to folder {new_parent_id}"}
        except Exception as e:
            traceback.print_exc()
            return {"status": "error", "message": f"Failed to move file: {str(e)}"}

    def rename_file(self, file_id, new_name):
        """Rename a file or folder in Google Drive."""
        print(f"Executing GoogleDriveTools.rename_file: {file_id} -> '{new_name}'")
        try:
            updated_file = self.service.files().update(
                fileId=file_id,
                body={'name': new_name},
                fields='id, name'
            ).execute()
            return {"status": "success", "message": f"Renamed to '{updated_file.get('name')}'"}
        except Exception as e:
            traceback.print_exc()
            return {"status": "error", "message": f"Failed to rename file: {str(e)}"}

    def list_drive_root(self):
        """List all files and folders at the root of the user's Drive (not in any subfolder)."""
        print("Executing GoogleDriveTools.list_drive_root")
        query = "'root' in parents and trashed = false"
        return self.search_drive(query)

    def get_tool_declarations(self):
        return [
            {
                "name": "search_drive",
                "description": "Searches Google Drive for files and folders using a query string. Useful for finding root folders to organize. (Use query \"mimeType='application/vnd.google-apps.folder' and name contains 'Projects'\" to find things). Returns JSON with file IDs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query in Drive API format. E.g., 'mimeType=\"application/vnd.google-apps.folder\"'"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_folder_contents",
                "description": "List all files and subfolders contained within a specific folder ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "folder_id": {
                            "type": "string",
                            "description": "The ID of the folder to list contents for"
                        }
                    },
                    "required": ["folder_id"]
                }
            },
            {
                "name": "create_folder",
                "description": "Creates a new folder in Google Drive. Returns the new folder ID so you can move files into it.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "folder_name": {"type": "string", "description": "The name of the new folder"},
                        "parent_folder_id": {"type": "string", "description": "Optional ID of a parent folder to place it in"}
                    },
                    "required": ["folder_name"]
                }
            },
            {
                "name": "move_file",
                "description": "Moves a file (or folder) from its current location into a new parent folder.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string", "description": "The ID of the file to move"},
                        "new_parent_id": {"type": "string", "description": "The ID of the folder to move the file into"}
                    },
                    "required": ["file_id", "new_parent_id"]
                }
            },
            {
                "name": "rename_file",
                "description": "Renames a file or folder in Google Drive. Useful for standardising names during organisation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string", "description": "The ID of the file or folder to rename"},
                        "new_name": {"type": "string", "description": "The new name for the file or folder"}
                    },
                    "required": ["file_id", "new_name"]
                }
            },
            {
                "name": "list_drive_root",
                "description": "Lists all files and folders at the very root of the user's Google Drive. Use this as the first step when the user asks to organize their Drive.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
