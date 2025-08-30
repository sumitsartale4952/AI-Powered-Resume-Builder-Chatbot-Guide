from flask import Flask, render_template, request, jsonify, send_file, session
from backend.chatbot_engine import Chatbot
from backend.resume_generator import ResumeGenerator
from backend.ats_analyzer import ATSAnalyzer
from backend.database import Database
from data_models.user_model import UserData
from pydantic import ValidationError
from utils.file_upload import FileUploader
from utils.nlp_processor import NLPProcessor
from utils.progress_tracker import ProgressTracker
import os
import yaml
from datetime import datetime
import logging
from werkzeug.utils import secure_filename
from typing import Dict, Any
from http import HTTPStatus

# Initialize Flask app with proper configurations
app = Flask(__name__)
app.secret_key = os.urandom(24)

def load_config() -> Dict[str, Any]:
    """Load and validate configuration"""
    if not os.path.exists('config.yaml'):
        raise FileNotFoundError("config.yaml not found. Please ensure it exists in the root directory.")
    with open("config.yaml") as f:
        return yaml.safe_load(f)

def setup_logging(config: Dict[str, Any]) -> None:
    """Configure logging with rotation"""
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        filename=os.path.join('logs', 'app.log'),
        level=config.get('logging', {}).get('level', logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_required_directories(config: Dict[str, Any]) -> None:
    """Create necessary directories"""
    directories = [
        config['storage']['image_upload_dir'],
        'generated_resumes',
        'templates',
        'static/images',
        'logs',
        'uploads'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Load configuration and setup directories/logging
config = load_config()
setup_logging(config)
create_required_directories(config)

# Initialize components
try:
    chatbot = Chatbot()
    resume_gen = ResumeGenerator()
    ats_analyzer = ATSAnalyzer()
    db = Database()
    nlp_processor = NLPProcessor()
    progress_tracker = ProgressTracker()
    
    file_uploader = FileUploader(
        upload_folder=config['storage']['image_upload_dir'],
        allowed_extensions=config['storage']['allowed_extensions'],
        max_size_mb=config['storage']['max_file_size_bytes'] // (1024 * 1024)
    )
except Exception as e:
    logging.critical(f"Failed to initialize components: {str(e)}")
    raise

def get_session_id() -> str:
    """Generate or retrieve session ID"""
    return session.get('session_id', datetime.now().strftime("%Y%m%d%H%M%S%f"))

def handle_api_error(e: Exception, status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR) -> tuple:
    """Centralized API error handling"""
    error_message = str(e) if isinstance(e, ValidationError) else "Internal server error"
    logging.error(f"API error: {str(e)}", exc_info=True)
    return jsonify({'error': error_message}), status_code

@app.route('/')
@app.route('/')
def home():
    """Render main chat interface with session initialization"""
    try:
        session_id = get_session_id()
        session['session_id'] = session_id
        if session_id not in chatbot.sessions:
            chatbot._initialize_session(session_id)
        progress_tracker.reset_progress(session_id)
        return render_template('index.html', config=config)
    except Exception as e:
        logging.critical(f"Session initialization failed: {str(e)}", exc_info=True)
        # Instead of showing an error page, you could redirect to home   
        return render_template('index.html', config=config), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route('/chat', methods=['POST'])
def handle_chat():
    """Handle chat messages with NLP integration and progress tracking"""
    try:
        session_id = session.get('session_id')
        user_message = request.json.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'Empty message received'}), HTTPStatus.BAD_REQUEST

        # Process message and update state
        bot_response = chatbot.process_message(user_message, session_id, nlp_processor)
        current_progress = progress_tracker.update_progress(
            session_id,
            bot_response.get('current_state')
        )

        # Save session state
        db.save_user_session(
            session_id=session_id,
            data={
                'user_data': chatbot.sessions[session_id]['user_data'],
                'last_state': chatbot.sessions[session_id]['state'],
                'progress': current_progress
            }
        )

        return jsonify({
            'response': bot_response['text'],
            'options': bot_response.get('options', []),
            'progress': current_progress,
            'session_id': session_id,
            'current_state': bot_response.get('current_state')
        })
    except ValidationError as e:
        return handle_api_error(e, HTTPStatus.BAD_REQUEST)
    except Exception as e:
        return handle_api_error(e)

@app.route('/generate-resume', methods=['POST'])
def generate_resume():
    """Generate resume with comprehensive ATS analysis"""
    try:
        session_id = session.get('session_id')
        template_name = request.json.get('template', config['templates'].get('default_template', 'default'))
        session_data = db.get_user_session(session_id)
        if not session_data or 'user_data' not in session_data:
            return jsonify({'error': 'Session data not found'}), HTTPStatus.NOT_FOUND

        user_data = UserData(**session_data['user_data'])
        pdf_path = resume_gen.generate_resume(
            user_data.dict(),
            f"{template_name}.html",
            nlp_processor
        )
        
        ats_report = ats_analyzer.full_analysis(
            pdf_path,
            config['ats']['keywords'],
            user_data.domain
        )

        resume_id = db.save_resume(
            user_data=user_data.dict(),
            pdf_path=pdf_path,
            analysis_data=ats_report
        )

        return jsonify({
            'pdf_url': f'/download-resume/{resume_id}',
            'ats_score': ats_report['score'],
            'ats_tips': ats_report['improvement_tips'],
            'keyword_matches': ats_report['keyword_matches'],
            'preview': resume_gen.get_html_preview(user_data.dict())
        })
    except ValidationError as e:
        return handle_api_error(e, HTTPStatus.BAD_REQUEST)
    except Exception as e:
        return handle_api_error(e)

@app.route('/download-resume/<resume_id>')
def download_resume(resume_id: str):
    """Secure resume download endpoint"""
    try:
        resume_data = db.get_resume(resume_id)
        if not resume_data or not os.path.exists(resume_data['pdf_path']):
            return jsonify({'error': 'Resume not found'}), HTTPStatus.NOT_FOUND
        return send_file(
            resume_data['pdf_path'],
            as_attachment=True,
            download_name=f"{resume_data['user_data']['name']}_Resume.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return handle_api_error(e)

@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    """Secure photo upload with advanced processing"""
    try:
        session_id = session.get('session_id')
        if 'photo' not in request.files:
            return jsonify({'error': 'No file uploaded'}), HTTPStatus.BAD_REQUEST

        file = request.files['photo']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), HTTPStatus.BAD_REQUEST

        try:
            file_path = file_uploader.secure_save_upload(file, session_id)
        except ValueError as err:
            return jsonify({'error': str(err)}), HTTPStatus.BAD_REQUEST

        relative_path = f"/uploads/{os.path.basename(file_path)}"
        db.update_user_data(session_id=session_id, update_data={'photo_url': relative_path})
        return jsonify({'photo_url': f"/static/images/{os.path.basename(file_path)}"})
    except Exception as e:
        return handle_api_error(e)

@app.route('/analyze-text', methods=['POST'])
def analyze_text():
    """NLP analysis endpoint for real-time feedback"""
    try:
        text = request.json.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), HTTPStatus.BAD_REQUEST
        analysis = nlp_processor.comprehensive_analysis(text)
        return jsonify(analysis)
    except Exception as e:
        return handle_api_error(e)

@app.errorhandler(HTTPStatus.NOT_FOUND)
def handle_not_found(e):
    return jsonify({'error': 'Resource not found'}), HTTPStatus.NOT_FOUND

@app.errorhandler(HTTPStatus.INTERNAL_SERVER_ERROR)
def handle_server_error(e):
    return jsonify({'error': 'Internal server error'}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.errorhandler(413)
def handle_file_size_error(e):
    return jsonify({'error': f'File size exceeds {config["storage"]["max_file_size_bytes"] // (1024*1024)}MB'}), 413

if __name__ == '__main__':
    try:
        print("Starting Resume Builder Application...")
        print(f"Server running on http://{config['app']['host']}:{config['app']['port']}")
        print("Available endpoints:")
        print("  - GET  /")
        print("  - POST /chat")
        print("  - POST /generate-resume")
        print("  - GET  /download-resume/<resume_id>")
        print("  - POST /upload-photo")
        print("  - POST /analyze-text")
        print("\nPress CTRL+C to stop the server")
        app.run(
            host=config['app']['host'],
            port=config['app']['port'],
            debug=config['app']['debug'],
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        chatbot.stop_session_cleanup_job()
    except Exception as e:
        logging.critical(f"Application failed to start: {str(e)}", exc_info=True)
        raise
    finally:
        print("Application shutdown complete.")