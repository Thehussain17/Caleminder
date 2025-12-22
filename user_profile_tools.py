# user_profile_tools.py
from user_database import UserDB

class UserProfileTools:
    """
    --- USER PROFILE COMPONENT ---
    Provides high-level tools for the AI to manage user context.
    This class acts as an interface between the Orchestrator and the UserDB.
    """
    def __init__(self):
        # We initialize UserDB internally or accept it?
        # Since this tool is stateless regarding user creds but stateful regarding DB,
        # we can just init UserDB.
        self.db = UserDB()

    def get_user_profile(self, user_id: str) -> dict:
        """Retrieves the user's profile, including their name and preferences."""
        profile = self.db.get_user_profile(user_id)
        if not profile:
            return {"status": "not_found", "message": "No profile found for this user yet."}
        return {"status": "success", "profile": profile}

    def update_user_profile(self, user_id: str, updates: dict) -> dict:
        """
        Updates the user's profile with new information. 
        For example, to set a name, use updates={'name': 'John'}. 
        To add a preference, use updates={'preferences': {'meeting_style': 'afternoon'}}.
        """
        try:
            # We need to load the full user record first if we want to preserve other fields,
            # but UserDB.save_user handles overwrites.
            # However, UserDB.save_user takes (user_info, creds).
            # We want to update just the 'profile' column json blob.

            current_profile = self.db.get_user_profile(user_id)

            # Deep merge the updates into the current profile
            for key, value in updates.items():
                if isinstance(value, dict) and isinstance(current_profile.get(key), dict):
                    current_profile[key].update(value)
                else:
                    current_profile[key] = value
            
            # We need a method in UserDB to update JUST the profile column without needing the rest.
            # Or we fetch the user first.
            # Let's add a dedicated method in UserDB or use SQL.

            # Quick fix: execute SQL directly here since we imported UserDB but UserDB abstracts connection.
            # Ideally, UserDB should have `update_profile_data(user_id, profile_dict)`

            # Since I can't easily change UserDB from here without another overwrite, let's assume UserDB has `save_user_profile`
            # Wait, the previous `user_profile_tools.py` called `self.db.save_user_profile`.
            # But my NEW `user_database.py` does NOT have `save_user_profile`. It has `save_user`.

            # I must update `user_database.py` to support profile updates, OR use `save_user` if I have all info.
            # But `save_user` requires email/name/creds which I might not have here.

            # I will update `user_database.py` to add `update_user_profile_data`.
            self.db.update_user_profile_data(user_id, current_profile)

            return {"status": "success", "message": "Profile updated."}
        except Exception as e:
            return {"status": "error", "message": f"Failed to update profile: {str(e)}"}
