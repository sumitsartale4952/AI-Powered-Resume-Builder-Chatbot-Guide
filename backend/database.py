from pymongo import MongoClient
from pymongo.errors import PyMongoError
from typing import Dict, Optional
import yaml
from data_models.user_model import UserData

class Database:
    def __init__(self):
        with open("config.yaml") as f:
            config = yaml.safe_load(f)
        
        self.client = MongoClient(config["database"]["uri"])
        self.db = self.client[config["database"]["name"]]
        self.users = self.db.users
        self.resumes = self.db.resumes

    def save_user_session(self, session_id: str, data: Dict) -> bool:
        try:
            self.users.update_one(
                {"session_id": session_id},
                {"$set": {
                    "data": data,
                    "last_modified": datetime.now()
                }},
                upsert=True
            )
            return True
        except PyMongoError as e:
            print(f"Database error: {str(e)}")
            return False

    def get_user_session(self, session_id: str) -> Optional[Dict]:
        try:
            result = self.users.find_one({"session_id": session_id})
            return result["data"] if result else None
        except PyMongoError:
            return None

    def save_resume(self, user_data: Dict, pdf_path: str) -> str:
        try:
            result = self.resumes.insert_one({
                "user_data": user_data,
                "pdf_path": pdf_path,
                "created_at": datetime.now()
            })
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Resume save failed: {str(e)}")
            return ""