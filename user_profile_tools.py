# user_profile_tools.py
from user_database import UserDB

class UserProfileTools:
    """
    --- USER PROFILE COMPONENT ---
    Provides high-level tools for the AI to manage user context.
    This class acts as an interface between the Orchestrator and the UserDB.
    """
    def __init__(self, db: UserDB):
        self.db = db

    def get_user_profile(self, user_id: str) -> dict:
        """Retrieves the user's profile, including their name and preferences."""
        profile = self.db.load_user_profile(user_id)
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
            current_profile = self.db.load_user_profile(user_id)
            # Deep merge the updates into the current profile
            for key, value in updates.items():
                if isinstance(value, dict) and isinstance(current_profile.get(key), dict):
                    current_profile[key].update(value)
                else:
                    current_profile[key] = value
            
            self.db.save_user_profile(user_id, current_profile)
            return {"status": "success", "message": "Profile updated."}
        except Exception as e:
            return {"status": "error", "message": f"Failed to update profile: {str(e)}"}
