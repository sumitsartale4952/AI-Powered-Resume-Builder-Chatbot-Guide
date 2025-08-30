import re
from typing import Dict
import spacy
import yaml
from data_models.user_model import UserData

class ATSAnalyzer:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        with open("config.yaml") as f:
            self.config = yaml.safe_load(f)

    def calculate_score(self, resume_text: str) -> Dict:
        score = 0
        max_score = len(self.config["ats"]["keywords"])
        
        # Keyword matching
        keyword_matches = [
            kw for kw in self.config["ats"]["keywords"]
            if kw.lower() in resume_text.lower()
        ]
        
        # Section completeness
        sections_found = [
            section for section in self.config["ats"]["required_sections"]
            if re.search(rf"\b{section}\b", resume_text, re.IGNORECASE)
        ]
        
        # Formatting checks
        has_bullet_points = bool(re.search(r"•|⸰|◦|‣", resume_text))
        has_dates = bool(re.search(r"\b(20\d{2}|present)\b", resume_text))
        
        return {
            "score": len(keyword_matches),
            "max_score": max_score,
            "keywords_missing": list(set(self.config["ats"]["keywords"]) - set(keyword_matches)),
            "sections_missing": list(set(self.config["ats"]["required_sections"]) - set(sections_found)),
            "formatting": {
                "has_bullet_points": has_bullet_points,
                "has_dates": has_dates
            }
        }

    def generate_improvement_tips(self, analysis: Dict) -> list:
        tips = []
        if analysis["keywords_missing"]:
            tips.append(f"Add missing keywords: {', '.join(analysis['keywords_missing'][:3])}")
        if analysis["sections_missing"]:
            tips.append(f"Add missing sections: {', '.join(analysis['sections_missing'])}")
        if not analysis["formatting"]["has_bullet_points"]:
            tips.append("Use bullet points for better readability")
        return tips