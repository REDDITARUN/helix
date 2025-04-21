# app/api/sequence.py
from flask import Blueprint, request, jsonify
from ..services.sequence_service import SequenceService
from ..extensions import db
from ..models import Message, Sequence

sequence_bp = Blueprint('sequence_bp', __name__)

@sequence_bp.route('/<int:session_id>/generate', methods=['POST'])
def trigger_sequence_generation(session_id):
    sequence_service = SequenceService()
    data = request.get_json()
    if not data or 'context' not in data: return jsonify({"error": "Missing 'context' in request body"}), 400
    generation_context = data['context']
    try:
        generated_sequences = sequence_service.generate_sequences(session_id, generation_context)
        sequences_text = "Generated Sequences:\n" + "\n".join([f"{i+1}. {s['content']}" for i, s in enumerate(generated_sequences)])
        sequence_message = Message(session_id=session_id, msg_role='tool', msg_content=sequences_text)
        db.session.add(sequence_message)
        db.session.commit()
        return jsonify(generated_sequences), 201
    except Exception as e:
        db.session.rollback() 
        print(f"Error generating sequences API: {e}")
        return jsonify({"error": "Failed to generate sequences"}), 500


@sequence_bp.route('/<int:session_id>/modify', methods=['POST'])
def trigger_sequence_modification(session_id):

    sequence_service = SequenceService()
    data = request.get_json()
    if not data or 'instruction' not in data:
        return jsonify({"error": "Missing 'instruction' in request body"}), 400

    modification_instruction = data['instruction']

    try:
        modified_sequences = sequence_service.modify_sequences(
            session_id,
            modification_instruction
        )

        sequences_text = "Modified Sequences:\n" + "\n".join([f"{i+1}. {s['content']}" for i, s in enumerate(modified_sequences)])
        sequence_message = Message(session_id=session_id, msg_role='tool', msg_content=sequences_text)
        db.session.add(sequence_message)
        db.session.commit()

        return jsonify(modified_sequences), 200
    except ValueError as e: 
        print(f"Value Error modifying sequences API: {e}")
        return jsonify({"error": str(e)}), 400 
    except Exception as e:
        db.session.rollback() 
        print(f"Error modifying sequences API: {e}")
        return jsonify({"error": "Failed to modify sequences"}), 500

@sequence_bp.route('/<int:session_id>', methods=['GET'])
def get_session_sequences(session_id):
    sequence_service = SequenceService()
    try:
        sequences = Sequence.query.filter_by(session_id=session_id)\
                                  .order_by(Sequence.seq_created_at.desc())\
                                  .limit(4).all()
        sequences.reverse()
        return jsonify([
             {"seq_id": s.seq_id, "session_id": s.session_id, "content": s.seq_content, "role": s.seq_role, "created_at": s.seq_created_at.isoformat(), "updated_at": s.seq_updated_at.isoformat()}
             for s in sequences
        ]), 200
    except Exception as e:
        print(f"Error retrieving sequences for session {session_id}: {e}")
        return jsonify({"error": "Failed to retrieve sequences"}), 500


@sequence_bp.route('/<int:sequence_id>', methods=['PUT'])
def update_sequence_content(sequence_id):
    sequence_service = SequenceService()
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"error": "Missing 'content' in request body"}), 400

    new_content = data['content']

    try:
        updated_sequence = sequence_service.update_sequence(sequence_id, new_content)
        return jsonify(updated_sequence), 200
    except ValueError as e:
        print(f"Value Error updating sequence {sequence_id}: {e}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"Error updating sequence {sequence_id}: {e}")
        return jsonify({"error": "Failed to update sequence"}), 500