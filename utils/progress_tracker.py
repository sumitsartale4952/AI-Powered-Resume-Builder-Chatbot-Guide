from typing import Dict
import logging

class ProgressTracker:
    def __init__(self):
        self.progress_steps = {
            'greeting': 0,
            'domain_selected': 15,
            'experience_selected': 30,
            'education_completed': 45,
            'work_history_completed': 60,
            'skills_added': 75,
            'template_selected': 90,
            'completed': 100
        }
        self.user_progress: Dict[str, float] = {}

    def update_progress(self, session_id: str, current_step: str) -> float:
        try:
            progress = self.progress_steps.get(current_step, 0)
            self.user_progress[session_id] = max(
                self.user_progress.get(session_id, 0),
                progress
            )
            return self.user_progress[session_id]
        except Exception as e:
            logging.error(f"Progress tracking error: {str(e)}")
            return 0

    def get_progress(self, session_id: str) -> float:
        return self.user_progress.get(session_id, 0)

    def reset_progress(self, session_id: str):
        self.user_progress.pop(session_id, None)