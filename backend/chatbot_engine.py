import os
import yaml
from typing import Dict, Any
from datetime import datetime, timedelta
import threading
import time
from pydantic import ValidationError
from data_models.user_model import UserData, ChatResponse

class Chatbot:
    def __init__(self):
        # Load configuration from config.yaml
        with open("config.yaml") as f:
            self.config = yaml.safe_load(f)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.cleanup_thread = None
        self.running = False

    def _initialize_session(self, session_id: str) -> None:
        """Initialize a new session with default user data"""
        default_user = UserData(
            name="",
            email="user@example.com",
            phone="+1234567890",
            domain="IT",
            experience_level="Fresher",
            skills=[],
            experiences=[],
            education=[],
            certifications=[],
            photo_url=None
        )
        self.sessions[session_id] = {
            "state": "greeting",
            "user_data": default_user.dict(),
            "last_interaction": datetime.now()
        }

    def process_message(self, message: str, session_id: str, nlp_processor=None) -> Dict:
        if session_id not in self.sessions:
            self._initialize_session(session_id)
        
        # Update last interaction time
        self.sessions[session_id]["last_interaction"] = datetime.now()
        session = self.sessions[session_id]
        response = {"text": "", "options": [], "completed": False}
        
        try:
            # Simple state machine handling (expand as needed)
            if session["state"] == "greeting":
                response = self._handle_greeting(message, session)
            elif session["state"] == "domain":
                response = self._handle_domain(message, session)
            # Add additional state handlers as required...
            
            # Validate and update user data
            validated_data = UserData(**session["user_data"])
            session["user_data"] = validated_data.dict()
        except ValidationError as e:
            response["text"] = f"Validation error: {str(e)}"
            response["options"] = ["Restart conversation"]
        
        session["last_interaction"] = datetime.now()
        return ChatResponse(**response).dict()

    def _handle_greeting(self, message: str, session: Dict) -> Dict:
        if "hi" in message.lower() or "hello" in message.lower():
            session["state"] = "domain"
            return {
                "text": "Welcome to AI Resume Builder! What's your domain of expertise?",
                "options": self.config["chatbot"].get("domains", []),
            }
        return {"text": "Please greet with 'Hi' to start the conversation."}

    def _handle_domain(self, message: str, session: Dict) -> Dict:
        domains = self.config["chatbot"].get("domains", [])
        if message.lower() in [d.lower() for d in domains]:
            session["user_data"]["domain"] = message
            session["state"] = "experience"
            return {
                "text": f"Great choice! How many years of experience do you have?",
                "options": self.config["chatbot"].get("experience_levels", []),
            }
        return {
            "text": "Please select a valid domain.",
            "options": domains
        }

    def start_session_cleanup_job(self):
        """Start the background thread to clean expired sessions."""
        if not self.cleanup_thread:
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_sessions_loop)
            self.cleanup_thread.daemon = True
            self.cleanup_thread.start()

    def _cleanup_sessions_loop(self):
        """Continuously clean up expired sessions every 5 minutes."""
        while self.running:
            self._cleanup_expired_sessions()
            time.sleep(300)

    def _cleanup_expired_sessions(self):
        """Remove expired sessions based on the response_timeout value."""
        timeout = timedelta(seconds=self.config['chatbot'].get('response_timeout', 300))
        current_time = datetime.now()
        expired_sessions = [
            session_id for session_id, session_data in self.sessions.items()
            if current_time - session_data["last_interaction"] > timeout
        ]
        for session_id in expired_sessions:
            del self.sessions[session_id]

    def stop_session_cleanup_job(self):
        """Stop the background session cleanup thread."""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
            self.cleanup_thread = None