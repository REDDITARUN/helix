# app/services/sequence_service.py
import json
import google.generativeai as genai
from flask import current_app
from ..extensions import db
from ..models import Session, Sequence

class SequenceService:
    def __init__(self):
        api_key = current_app.config.get('GOOGLE_API_KEY')
        if not api_key: raise ValueError("GOOGLE_API_KEY not configured")
        genai.configure(api_key=api_key)
        self.generation_config_params = { 
             "temperature": 0.8, "top_p": 0.95, "top_k": 40, "max_output_tokens": 4096,
        }
        self.modification_config_params = { 
             "temperature": 0.6, "top_p": 0.95, "top_k": 40, "max_output_tokens": 4096,
        }
        self.model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-04-17")

    def _build_sequence_prompt(self, context):
        prompt = f"""
        Based on the following recruitment requirements, generate exactly 4 new parts of an outreach message suitable for an outreach template.

        Requirements:
        - Target Role: {context.get('target_role', 'N/A')}
        - Company Context: {context.get('company_context', 'N/A')}
        - Key Selling Points: {', '.join(context.get('key_selling_points', []))}
        - Ideal Candidate Persona: {context.get('candidate_persona', 'N/A')}
        - Desired Tone: {context.get('tone', 'professional')}

        Output MUST be a valid JSON object containing ONLY a single key "sequences", which is an array of 4 strings. Each string should be a part of message sequence. DO NOT include any other text or explanations before or after the JSON object.

        Example JSON Output Structure:
        ```json
        {{
          "sequences": [ /* 4 sequence strings here */ ]
        }}
        ```
        Generate the JSON output now:
        """
        return prompt.strip()

    def _build_modification_prompt(self, instruction, previous_sequences):
        previous_sequences_text = "\n".join(f"{i+1}. {seq}" for i, seq in enumerate(previous_sequences))


        prompt = f"""
        You are tasked with modifying a set of 4 previously generated outreach message parts based on a specific instruction.

        Modification Instruction:
        {instruction}

        Previous Message Parts:
        {previous_sequences_text}

        Your goal is to apply the modification instruction to the previous message parts and output the **complete, updated set of 4 message parts**.

        Output MUST be a valid JSON object containing ONLY a single key "sequences", which is an array of the 4 **modified** strings. Each string should be a part of the message sequence. DO NOT include any other text or explanations before or after the JSON object.

        Example JSON Output Structure:
        ```json
        {{
          "sequences": [
            "MODIFIED Sequence 1 text here...",
            "MODIFIED Sequence 2 text here...",
            "MODIFIED Sequence 3 text here...",
            "MODIFIED Sequence 4 text here..."
          ]
        }}
        ```

        Generate the JSON output containing the 4 modified sequences now:
        """
        return prompt.strip()


    def _parse_and_save_sequences(self, session_id, response_text, replace_existing=False):
        raw_text = response_text
        if raw_text.strip().startswith("```json"):
             raw_text = raw_text.strip()[7:]
             if raw_text.strip().endswith("```"):
                 raw_text = raw_text.strip()[:-3]

        try:
            data = json.loads(raw_text.strip())
            generated_sequences_content = data.get("sequences", [])
        except json.JSONDecodeError as e:
             print(f"JSON Decode Error in _parse_and_save: {e}")
             print(f"Raw text was: {raw_text}")
             raise ValueError("Failed to decode JSON response from AI.") from e


        if not isinstance(generated_sequences_content, list) or len(generated_sequences_content) != 4:
             raise ValueError(f"Expected 4 sequences in JSON list, found {len(generated_sequences_content)}")

        if replace_existing:
             try:
                 num_deleted = Sequence.query.filter_by(session_id=session_id).delete()
                 db.session.commit() 
                 print(f"Deleted {num_deleted} existing sequences for session {session_id}.")
             except Exception as e:
                 db.session.rollback()
                 print(f"Error deleting existing sequences: {e}")
                 raise 

        saved_sequence_objects = [] 
        for content in generated_sequences_content:
            if isinstance(content, str) and content.strip():
                
                sequence = Sequence(session_id=session_id, seq_role='generated', seq_content=content)
                db.session.add(sequence)
                saved_sequence_objects.append(sequence)
            else:
                print(f"Warning: Skipping invalid sequence item received: {content}")

        if not saved_sequence_objects:
             raise ValueError("No valid sequences were generated or parsed from AI response.")

        try:
            db.session.commit()
            print(f"Committed {len(saved_sequence_objects)} new sequences for session {session_id}.")
        except Exception as e:
            db.session.rollback() 
            print(f"Error committing new sequences: {e}")
            raise 

        return [
            {
                "seq_id": s.seq_id, 
                "session_id": s.session_id,
                "content": s.seq_content,
                "role": s.seq_role,
                "created_at": s.seq_created_at.isoformat() if s.seq_created_at else None,
                "updated_at": s.seq_updated_at.isoformat() if s.seq_updated_at else None
            }
            for s in saved_sequence_objects
        ]


    def generate_sequences(self, session_id, generation_context):
        session = Session.query.get(session_id)
        if not session: raise ValueError(f"Session {session_id} not found")

        prompt = self._build_sequence_prompt(generation_context)
        try:
            response = self.model.generate_content(
                 contents=[prompt],
                 generation_config=self.generation_config_params
            )
            return self._parse_and_save_sequences(session_id, response.text, replace_existing=True)
        except Exception as e:
            db.session.rollback()
            print(f"Error during sequence generation: {e}")
            print(f"Failed Prompt:\n{prompt}")
            if 'response' in locals(): print(f"Failed Response:\n{response.text if hasattr(response, 'text') else 'N/A'}")
            raise 


    def modify_sequences(self, session_id, modification_instruction):
        session = Session.query.get(session_id)
        if not session: raise ValueError(f"Session {session_id} not found")

        latest_sequences = Sequence.query.filter_by(session_id=session_id)\
                                         .order_by(Sequence.seq_created_at.desc())\
                                         .limit(4).all()
        if len(latest_sequences) != 4:
             raise ValueError(f"Could not find 4 previous sequences for session {session_id} to modify.")
        previous_sequences_content = [seq.seq_content for seq in reversed(latest_sequences)]

        prompt = self._build_modification_prompt(modification_instruction, previous_sequences_content)
        try:
            response = self.model.generate_content(
                 contents=[prompt],
                 generation_config=self.modification_config_params
            )
            return self._parse_and_save_sequences(session_id, response.text, replace_existing=True)
        except Exception as e:
            db.session.rollback()
            print(f"Error during sequence modification: {e}")
            print(f"Failed Prompt:\n{prompt}")
            if 'response' in locals(): print(f"Failed Response:\n{response.text if hasattr(response, 'text') else 'N/A'}")
            raise


    def get_sequences_for_session(self, session_id):
        sequences = Sequence.query.filter_by(session_id=session_id).order_by(Sequence.seq_created_at).all()
        return [{"seq_id": s.seq_id, "session_id": s.session_id, "content": s.seq_content, "role": s.seq_role, "created_at": s.seq_created_at.isoformat(), "updated_at": s.seq_updated_at.isoformat()} for s in sequences]

    def update_sequence(self, sequence_id, new_content):
        sequence = Sequence.query.get(sequence_id)
        if not sequence: raise ValueError(f"Sequence with ID {sequence_id} not found.")
        sequence.seq_content = new_content
        sequence.seq_role = 'edited'
        db.session.commit()
        return {"seq_id": sequence.seq_id, "session_id": sequence.session_id, "content": sequence.seq_content, "role": sequence.seq_role, "created_at": sequence.seq_created_at.isoformat(), "updated_at": sequence.seq_updated_at.isoformat()}