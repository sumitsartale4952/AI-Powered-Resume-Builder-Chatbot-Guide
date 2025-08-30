import os
import magic
from werkzeug.utils import secure_filename
from PIL import Image
import io
import logging
from datetime import datetime

class FileUploader:
    def __init__(self, upload_folder, allowed_extensions, max_size_mb):
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions
        self.max_size_bytes = max_size_mb * 1024 * 1024
        os.makedirs(upload_folder, exist_ok=True)

    def is_allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def secure_save_upload(self, file_stream, user_id):
        try:
            # Validate file type using magic numbers
            file_bytes = file_stream.read()
            mime = magic.from_buffer(file_bytes, mime=True)
            
            if not mime.startswith('image/'):
                raise ValueError("Invalid file type")

            # Reset file stream cursor
            file_stream.seek(0)

            # Secure filename
            original_filename = secure_filename(file_stream.filename)
            file_ext = original_filename.rsplit('.', 1)[1].lower()
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_filename = f"user_{user_id}_{timestamp}.{file_ext}"
            
            # Validate file size
            if len(file_bytes) > self.max_size_bytes:
                raise ValueError("File size exceeds limit")

            # Process image
            img = Image.open(io.BytesIO(file_bytes))
            img = self._optimize_image(img)
            
            # Save optimized image
            save_path = os.path.join(self.upload_folder, new_filename)
            img.save(save_path, optimize=True, quality=85)
            
            return save_path

        except Exception as e:
            logging.error(f"File upload error: {str(e)}")
            raise

    def _optimize_image(self, img):
        # Resize if too large
        if img.width > 1024 or img.height > 1024:
            img.thumbnail((1024, 1024))
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
            
        return img

    @staticmethod
    def scan_for_malware(file_path):
        # Placeholder for actual virus scanning integration
        # Consider integrating with ClamAV or cloud service
        return True