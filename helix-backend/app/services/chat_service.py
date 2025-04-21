# app/services/chat_service.py
import os
import json
import google.generativeai as genai
from flask import current_app
from ..extensions import db
from ..models import Session, Message, Sequence
from ..tools.all_tools import ALL_TOOLS
from .document_service import DocumentService


class ChatService:
    
    
    def __init__(self):
        api_key = current_app.config.get('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not configured in Flask app")
        genai.configure(api_key=api_key)
        self.generation_config_params = {
             "temperature": 0.7, "top_p": 0.95, "top_k": 40, "max_output_tokens": 8192,
        }


        self.system_prompt = """
            # SYSTEM PROMPT: Helix Recruitment Assistant

            You are Helix, an expert recruitment assistant chatbot. Your purpose is to engage naturally with users on recruitment topics and assist in crafting personalized outreach message sequences *only when explicitly requested*.

            ## Core Behavior:

            1.  **Conversational First:** Start conversations naturally. Be helpful and answer general recruitment questions or provide advice if asked. Do NOT immediately try to generate outreach messages.
            2.  **Listen for Trigger:** Only initiate the sequence creation process when the user explicitly asks you to **create**, **generate**, or **write** outreach messages/sequences.
            3.  **Maintain Flow:** Keep the conversation intuitive. Avoid robotic interactions.

            ## General Assistance Mode:
            *   If the user is not asking for outreach message creation, act as a knowledgeable recruitment advisor.
            *   Discuss topics like talent acquisition strategies, industry best practices, candidate engagement, sourcing tips, etc.
            *   Answer questions clearly and concisely.
            


            ## RAG FETCH MODE
            In this the user might ask anything like get me the top candidates list or what roles are evailable, if you have them anything related to his asking in context, give startight answer. 
            
            
            ## Outreach Sequence Creation Mode:
            **(Activated ONLY by explicit user request for message creation)**
            
            [**CRITICAL**] -  Depending on the user given info and context you have, you need to adapt the steps of information gathering. 
            
            You need to have the following information before proceeding to generate sequence function, so if you have this information avaiable you can call the function now.
            **Step 1: Information Gathering**
            *   Politely state you need some details to craft effective messages.
            *   Gather the following 5 pieces of information through conversation:
                1.  `target_role`: The specific job title.
                2.  `company_context`: Brief background of the company/team.
                3.  `key_selling_points`: Exactly 3 compelling reasons for a candidate to be interested.
                4.  `candidate_persona`: Description of the ideal candidate's skills/experience.
                5.  `desired_tone`: The tone/style (e.g., formal, casual, enthusiastic).
            *   **CRITICAL:** 
            - If none of available from the context, you need to ask for **one piece** of missing information at a time. Wait for the user's response before asking for the next item. Acknowledge the received information briefly before asking the next question (e.g., "Got it. Now, could you tell me about the company context?").
            - If some available you can ask multiple info at once.
            - If available in the RAG context, ask for review and proceed to generate upon confirmantion.

            **Step 2: Initial Sequence Generation**
            *   **CRITICAL:** **As soon as you have received responses covering ALL 5 required details** (target_role, company_context, 3 key_selling_points, candidate_persona, desired_tone), your **very next response MUST be ONLY the function call `generate_outreach_sequences`**.
            *   Populate the function call's arguments accurately with the collected information.
            *   **DO NOT** add ANY conversational text like "Okay, I have everything..." or "Let me generate..." or ask for confirmation before making the function call. The function call itself is the entire response in this turn.

            **Step 3: Sequence Modification**
            This is anything from adding, modifying, editing, the terminology of the user might be casual and different, but you are supposed to follow his instruction and call the 'generate_outreach_sequences' funtion straight away. No delay.
            *   If, **AFTER** the initial `generate_outreach_sequences` call has occurred (meaning sequences exist), the user asks for **ANY changes** to the sequences (e.g., "use name X", "make it professional", "shorten the second part"), your **very next response MUST be ONLY the function call `modify_sequences`**.
            *   This function requires ONE argument: `modification_instruction`. You MUST extract the user's specific change request (e.g., "use name Judy", "make the tone professional") and populate the `modification_instruction` argument accurately.
            *   **DO NOT** add ANY conversational text or ask for confirmation before making the `modify_sequences` function call. The function call itself is the entire response in this turn.

            ## Overall Rules:

            *   **NEVER** generate or modify sequence text directly in your chat responses. **ALWAYS** use the designated function calls.
            *   `generate_outreach_sequences` is ONLY for the initial creation based on the 5 core details.
            *   `modify_sequences` is for ALL subsequent modification requests the terminilogy of user experssing this may vary, but you need to understand and proceed to modify.
            *   Transitions to function calls (both types) MUST be immediate once the criteria are met, with no intermediate conversational steps or confirmations.
            
            ## INFORMATION OF FUNCTIONS
            - "generate_outreach_sequences_declaration" Creates a 4-part recruitment message sequence based on provided job details, company info, selling points, candidate profile, desired tone, and optional context for new sequences.
            - "modify_sequences_declaration" Edits, modifies, or changes, any modification involving existing outreach sequences based on specific user instructions.
            
            
        """

        self.model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-04-17")
        
        
    # RAG based message generation
    def enhance_with_rag(self, session_id):
        session = self._get_or_create_session(session_id)        
        recent_messages = Message.query.filter_by(
            session_id=session_id, 
            msg_role='user'
        ).order_by(Message.msg_created_at.desc()).limit(3).all()
        
        if not recent_messages:
            return {"status": "warning", "message": "No user messages found for RAG context"}
        
        combined_query = " ".join([msg.msg_content for msg in reversed(recent_messages)])
        
        try:
            doc_service = DocumentService()
            query_embedding = genai.embed_content(
                model=doc_service.embedding_model_name,
                content=combined_query,
                task_type="retrieval_query"
            )['embedding']
            
            query_response = doc_service.index.query(
                vector=query_embedding,
                top_k=30,  
                include_metadata=True
            )
            
            rag_context = []
            if hasattr(query_response, 'matches') and query_response.matches:
                for match in query_response.matches:
                    if hasattr(match, 'metadata') and match.metadata and 'text_preview' in match.metadata:
                        filename = match.metadata.get('filename', 'unknown')
                        rag_context.append(f"Document '{filename}': {match.metadata['text_preview']}")
            
            if not rag_context:
                return {"status": "warning", "message": "No relevant documents found"}
            
            rag_content = "\n\n".join(rag_context)
            system_msg = f"[RAG CONTEXT]\n\nThe following are relevant documents to help with the conversation:\n\n{rag_content}\n\n[END RAG CONTEXT]"
            
            self._save_message(session_id, 'model', system_msg)
            
            return {
                "status": "success", 
                "message": "RAG context added successfully", 
                "doc_count": len(rag_context)
            }
            
        except Exception as e:
            print(f"Error retrieving RAG context: {e}")
            return {"status": "error", "message": f"Failed to retrieve document context: {str(e)}"}

    def _get_or_create_session(self, session_id=None):
        if session_id:
            session = Session.query.get(session_id)
            if session: return session
            else: raise ValueError(f"Session with ID {session_id} not found.")
        new_session = Session()
        db.session.add(new_session)
        db.session.commit()
        return new_session

    def _save_message(self, session_id, role, content):
        if not content: return None
        message = Message(session_id=session_id, msg_role=role, msg_content=content)
        db.session.add(message)
        db.session.commit()
        return message

    def _get_chat_history(self, session_id):
        messages = Message.query.filter_by(session_id=session_id).order_by(Message.msg_created_at).all()
        history = []
        system_prompt_found = False

        if messages and messages[0].msg_role == 'model' and messages[0].msg_content == self.system_prompt:
            system_prompt_found = True

        if not system_prompt_found:
             history.append({"role": "model", "parts": [{"text": self.system_prompt}]})

        for msg in messages:
            if not system_prompt_found and msg.msg_role == 'model' and msg.msg_content == self.system_prompt:
                 continue

            role = 'user' if msg.msg_role == 'user' else 'model'
            history.append({"role": role, "parts": [{"text": msg.msg_content}]})

        return history 

    def start_new_chat(self):
        session = self._get_or_create_session()
        self._save_message(session.s_id, 'model', self.system_prompt)
        return {"session_id": session.s_id}


    def send_message(self, session_id, user_message_content):
        session = self._get_or_create_session(session_id)
        self._save_message(session.s_id, 'user', user_message_content)
        history_for_api = self._get_chat_history(session.s_id)
        

        try:
             response = self.model.generate_content(
                 contents=history_for_api,
                 generation_config=self.generation_config_params,
                 tools=ALL_TOOLS
             )
        except Exception as e:
             print(f"Error calling Gemini API: {e}")
             self._save_message(session_id, 'model', f"[Error communicating with AI: {e}]")
             raise

        ai_response_text_to_return = None 
        function_call_data = None     

        if response.candidates and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]

            if hasattr(part, 'function_call') and part.function_call:
                function_call = part.function_call
                print(f"Detected function call: {function_call.name}") 

                args_dict = {}
                for key, value in function_call.args.items():
                    if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                        args_dict[key] = [item for item in value]
                    else:
                        args_dict[key] = value

                function_call_data = { "name": function_call.name, "args": args_dict }

                if function_call.name == "generate_outreach_sequences":
                    ai_response_text_to_return = "[System: Function call generated. Preparing to generate sequences...]"
                    self._save_message(session.s_id, 'model', ai_response_text_to_return)
                    
                    
                elif function_call.name == "modify_sequences":
                    if "modification_instruction" not in args_dict:
                        print("Error: modify_sequences called without required 'modification_instruction' argument!")
                        ai_response_text_to_return = "[System Error: Modification function called incorrectly by AI. Missing instruction.]"
                        self._save_message(session.s_id, 'model', ai_response_text_to_return)
                        function_call_data = None 
                    else:
                        ai_response_text_to_return = "[System: Modification request received. Preparing to modify sequences...]"
                        self._save_message(session.s_id, 'model', ai_response_text_to_return)
                        
                else:
                    print(f"Warning: Unexpected function call received: {function_call.name}")
                    ai_response_text_to_return = f"[System: Received unexpected function call '{function_call.name}']"
                    self._save_message(session.s_id, 'model', ai_response_text_to_return)
                    function_call_data = None

            elif hasattr(part, 'text'):
                text_content = part.text
                print(f"Detected text response: {text_content[:50]}...")
                if text_content:
                    ai_response_text_to_return = text_content
                    self._save_message(session.s_id, 'model', ai_response_text_to_return)
                else:
                    ai_response_text_to_return = ""
            else:
                print("Warning: Received unexpected part type in Gemini response.")
                ai_response_text_to_return = "[System: Received non-text, non-function response part]"

        elif response.text:
            print("Using fallback response.text")
            ai_response_text_to_return = response.text
            if ai_response_text_to_return:
                 self._save_message(session.s_id, 'model', ai_response_text_to_return)

        if not function_call_data and ai_response_text_to_return is None:
            print("Warning: No function call and no text content found in response.")
            ai_response_text_to_return = "[System: No valid response content received]"

        return {
            "session_id": session_id,
            "ai_message": ai_response_text_to_return,
            "function_call": function_call_data 
        }