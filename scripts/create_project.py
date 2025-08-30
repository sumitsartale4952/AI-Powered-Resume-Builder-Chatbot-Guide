import os
from pathlib import Path

def create_project_structure(base_dir="AI-Powered Resume Builder Chatbot Guide"):
    structure = {
        "": ["app.py", "config.yaml", "requirements.txt"],
        "backend": ["__init__.py", "chatbot_engine.py", "resume_generator.py", "ats_analyzer.py"],
        "data_models": ["__init__.py", "user_model.py"],
        "templates": ["modern.html", "classic.html", "minimalist.html"],
        "static/css": [],
        "static/js": [],
        "static/images": [],
        "utils": ["__init__.py", "file_upload.py", "nlp_processor.py"],
        "tests": ["__init__.py", "test_chatbot.py"],
        "scripts": ["create_project.py"]
    }

    for folder, files in structure.items():
        dir_path = Path(base_dir) / folder
        dir_path.mkdir(parents=True, exist_ok=True)
        for file in files:
            file_path = dir_path / file
            file_path.touch(exist_ok=True)
            print(f"Created: {file_path}")

    print("\nProject structure created successfully!")

if __name__ == "__main__":
    create_project_structure()