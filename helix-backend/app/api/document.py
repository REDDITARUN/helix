# app/api/document.py
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from ..services.document_service import DocumentService
import os

document_bp = Blueprint('document_bp', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@document_bp.route('/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        print(f"Received file upload request: {filename}")

        try:
            document_service = DocumentService()

            result = document_service.process_and_upsert(file, filename)

            return jsonify(result), 200 if result.get("status") == "success" else 400

        except ValueError as e:
            print(f"ValueError during upload: {e}")
            return jsonify({"error": str(e)}), 400 
        except Exception as e:
            print(f"Unexpected error during upload: {e}")
            return jsonify({"error": "An unexpected error occurred processing the file."}), 500
    else:
        return jsonify({"error": "File type not allowed. Please upload PDF or TXT."}), 400