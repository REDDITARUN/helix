# app/api/chat.py
from flask import Blueprint, request, jsonify
from ..services.chat_service import ChatService
from ..extensions import db 

chat_bp = Blueprint('chat_bp', __name__)


@chat_bp.route('/', methods=['POST'])
def create_chat_session():
    chat_service = ChatService() 
    try:
        result = chat_service.start_new_chat()
        return jsonify(result), 201
    except Exception as e:
        print(f"Error creating chat session: {e}")
        return jsonify({"error": "Failed to create chat session"}), 500

@chat_bp.route('/<int:session_id>/message', methods=['POST'])
def post_message(session_id):

    chat_service = ChatService() 
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400

    user_message = data['message']

    try:
        response = chat_service.send_message(session_id, user_message)
        return jsonify(response), 200
    except ValueError as e:
        print(f"Value Error processing message for session {session_id}: {e}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"Error processing message for session {session_id}: {e}")
        return jsonify({"error": "Failed to process message"}), 500
    
    
    
@chat_bp.route('/<int:session_id>/rag', methods=['POST'])
def trigger_rag(session_id):
    chat_service = ChatService()
    try:
        result = chat_service.enhance_with_rag(session_id)
        return jsonify(result), 200
    except ValueError as e:
        print(f"Value Error in RAG enhancement for session {session_id}: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Error in RAG enhancement for session {session_id}: {e}")
        return jsonify({"error": "Server error occurred"}), 500