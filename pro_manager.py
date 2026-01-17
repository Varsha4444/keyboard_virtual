from tinydb import TinyDB, Query
import os

class ProfileManager:
    def __init__(self, db_path="data/profiles.json"):
        os.makedirs("data", exist_ok=True)
        self.db = TinyDB(db_path)
        self.Profile = Query()

    def save_profile(self, name, settings):
        self.db.upsert(
            {
                "name": name,
                "settings": settings
            },
            self.Profile.name == name
        )

    def load_profile(self, name):
        result = self.db.search(self.Profile.name == name)
        return result[0]["settings"] if result else None

    def list_profiles(self):
        return [p["name"] for p in self.db.all()]

    def load_default(self):
        profiles = self.db.all()
        if profiles:
            return profiles[0]["settings"]
        return None
