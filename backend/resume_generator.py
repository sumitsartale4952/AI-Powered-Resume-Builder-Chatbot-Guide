from typing import Dict
import pdfkit
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import yaml
from data_models.user_model import UserData

class ResumeGenerator:
    def __init__(self):
        with open("config.yaml") as f:
            self.config = yaml.safe_load(f)
        self.env = Environment(loader=FileSystemLoader("templates"))
        
    def generate_resume(self, user_data: Dict, template_name: str) -> str:
        # Validate input
        user = UserData(**user_data)
        
        # Load template
        template = self.env.get_template(template_name)
        
        # Add ATS optimization tips
        context = user.dict()
        context["ats_tips"] = self._generate_ats_tips(user)
        
        # Render HTML
        html_content = template.render(**context)
        
        # Generate PDF
        output_path = f"generated_resumes/{user.name.replace(' ', '_')}_resume.pdf"
        Path("generated_resumes").mkdir(exist_ok=True)
        
        pdfkit.from_string(
            html_content, 
            output_path,
            options={
                'encoding': 'UTF-8',
                'quiet': '',
                'enable-local-file-access': ''
            }
        )
        return output_path

    def _generate_ats_tips(self, user: UserData) -> list:
        tips = []
        # Check for missing sections
        for section in self.config["ats"]["required_sections"]:
            if not getattr(user, section.lower()):
                tips.append(f"Add {section} section for better ATS scoring")
        return tips

    def get_html_preview(self, user_data: Dict) -> str:
        user = UserData(**user_data)
        template = self.env.get_template("preview.html")
        return template.render(**user.dict())