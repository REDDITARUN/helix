// src/types.ts
export interface Sequence {
  seq_id: number;
  session_id: number;
  content: string;
  role: 'generated' | 'edited'; 
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: number | string; 
  text: string;
  sender: 'user' | 'ai' | 'system'; 
}

export interface FunctionCallArgs {
  target_role: string;
  company_context: string;
  key_selling_points: string[];
  candidate_persona: string;
  tone: string;
  [key: string]: any; 
}

export interface FunctionCall {
  name: string;
  args: FunctionCallArgs;
}

export interface BackendChatResponse {
  session_id: number;
  ai_message: string | null;
  function_call: FunctionCall | null;
}