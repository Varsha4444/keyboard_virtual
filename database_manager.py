from tinydb import TinyDB, Query

class DatabaseManager:
    def __init__(self, db_path='data/user_profiles.json'):
        self.db = TinyDB(db_path)
        self.User = Query()

    def add_user(self, name):
        if not self.db.search(self.User.name == name):
            self.db.insert({'name': name, 'created': True})

    def get_users(self):
        return self.db.all()
