# app/tools/all_tools.py

import os
from google.generativeai import types

# Tool for generating sequences
generate_outreach_sequences_declaration = {
    "name": "generate_outreach_sequences",
    "description": "Generates 4 parts of a single outreach message sequences based on the collected user requirements for recruitment. Or Modifies particular parts of single outresearch message based on the command",
    "parameters": {
        "type": "object", 
        "properties": {
            'target_role': { 
                "type": "string",
                "description": "The job title or role the user is recruiting for."
            },
            'company_context': {
                "type": "string",
                "description": "Brief description of the company or team."
            },
            'key_selling_points': {
                "type": "array",
                 "items": {"type": "string"},
                 "description": "List of key reasons why a candidate should be interested."
            },
            'candidate_persona': {
                "type": "string",
                "description": "Description of the ideal candidate profile."
            },
            'tone': {
                "type": "string",
                "description": "Desired tone of the messages (e.g., formal, casual, enthusiastic)."
             },
            'enhancement_context': {
                "type": "string",
                "description": "Optional. Context for modifying existing sequences (e.g., previous messages, names) or 'NONE FOR NOW' for new sequence generation."
             },
        },
        "required": ['target_role', 'company_context', 'key_selling_points', 'candidate_persona', 'tone']
    }
}


# Tool for modifying sequences
modify_sequences_declaration = {
    "name": "modify_sequences",
    "description": "Modifies previously generated outreach sequences based ONLY on the user's specific instruction. Use this AFTER sequences have been generated and the user asks for changes.",
    "parameters": {
        "type": "object",
        "properties": {
            "modification_instruction": {
                "type": "string",
                "description": "The user's specific request for how to change the existing sequences (e.g., 'use the name Tarun instead of [Candidate Name]', 'make the tone professional')."
            }
            
        },
        "required": ["modification_instruction"] 
    }
}

# list of all tools
ALL_TOOLS = [
    types.Tool(function_declarations=[generate_outreach_sequences_declaration]),
    types.Tool(function_declarations=[modify_sequences_declaration])
]

# Individual exports 
GENERATE_SEQUENCES_TOOL = types.Tool(function_declarations=[generate_outreach_sequences_declaration])
MODIFY_SEQUENCES_TOOL = types.Tool(function_declarations=[modify_sequences_declaration])

