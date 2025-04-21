// src/components/chatbox/ChatBox.tsx
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './ChatBox.css';
import { ChatMessage, FunctionCall, BackendChatResponse } from '../../types';
import ReactMarkdown from 'react-markdown';

const API_BASE_URL = 'http://127.0.0.1:5000/api';

interface ChatBoxProps {
  sessionId: number | null;
  onFunctionCall: (functionCall: FunctionCall) => void;
}

function ChatBox({ sessionId, onFunctionCall }: ChatBoxProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);
  const [isRagLoading, setIsRagLoading] = useState(false);
  const [ragActivated, setRagActivated] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleTriggerRAG = async () => {
    if (!sessionId || isLoading || isRagLoading) return;
    
    setIsRagLoading(true);
    setError(null);
    
    try {
      await axios.post(
        `${API_BASE_URL}/chat/${sessionId}/rag`,
        {}
      );
      
      setMessages(prevMessages => [
        ...prevMessages,
        {
          id: `system-rag-${Date.now()}`,
          text: "Context enhancement activated. The assistant now has access to relevant documents.", 
          sender: 'system'
        }
      ]);
      
      setRagActivated(true);
      
    } catch (error) {
      console.error("Error triggering RAG:", error);
      const errorText = axios.isAxiosError(error) && error.response?.data?.error
        ? error.response.data.error
        : "Failed to enhance context with documents.";
      setError(errorText);
    } finally {
      setIsRagLoading(false);
    }
  };

  useEffect(scrollToBottom, [messages]);

  useEffect(() => {
    setMessages([]);
    setError(null);
    setRagActivated(false);
    if (sessionId) {
      fetchChatHistory(sessionId);
      setTimeout(() => {
        inputRef.current?.focus();
      }, 300);
    } else {
      setMessages([{ 
        id: 'no-session', 
        text: 'Please start a new session using the button above.', 
        sender: 'system'
      }]);
    }
  }, [sessionId]);

  const fetchChatHistory = async (currentSessionId: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.get<{ 
        messages: { 
          msg_id: number, 
          msg_content: string, 
          msg_role: 'user' | 'model' | 'system' | 'tool' 
        }[] 
      }>(`${API_BASE_URL}/chat/${currentSessionId}/history`);
      
      const historyMessages: ChatMessage[] = response.data.messages.map(msg => ({
        id: msg.msg_id,
        text: msg.msg_content,
        sender: msg.msg_role === 'user' ? 'user' : 
               (msg.msg_role === 'model' || msg.msg_role === 'tool' ? 'ai' : 'system')
      }));
      
      setMessages(historyMessages);
      
      const hasRagMessage = historyMessages.some(msg => 
        msg.sender === 'system' && msg.text.includes("Context enhancement activated")
      );
      setRagActivated(hasRagMessage);
      
    } catch (err) {
      console.error("Error fetching chat history:", err);
      setMessages([{ 
        id: 'error-hist', 
        text: 'Welcome! How can I help?', 
        sender: 'system'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (inputValue.trim() === '' || isLoading || !sessionId) return;

    setIsLoading(true);
    setError(null);

    const userMessageText = inputValue;
    const newUserMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      text: userMessageText,
      sender: 'user',
    };
    
    setMessages(prevMessages => [...prevMessages, newUserMessage]);
    setInputValue('');

    try {
      const response = await axios.post<BackendChatResponse>(
        `${API_BASE_URL}/chat/${sessionId}/message`,
        { message: userMessageText }
      );

      const backendResponse = response.data;
      const newMessages: ChatMessage[] = [];

      if (backendResponse.ai_message) {
        newMessages.push({
          id: `ai-${Date.now()}`,
          text: backendResponse.ai_message,
          sender: backendResponse.ai_message.startsWith('[System:') ? 'system' : 'ai',
        });
      }

      if (newMessages.length > 0) {
        setMessages(prevMessages => [...prevMessages, ...newMessages]);
      }

      setRagActivated(false);

      if (backendResponse.function_call) {
        if (backendResponse.function_call.name && backendResponse.function_call.args) {
          console.log("ChatBox: Calling onFunctionCall with:", backendResponse.function_call);
          onFunctionCall(backendResponse.function_call);
        } else {
          console.error("ChatBox: Received incomplete function call object from backend:", backendResponse.function_call);
          setError("Received an invalid function call instruction from the AI.");
          setMessages(prev => [...prev, {
            id: `system-${Date.now()}`, 
            text: `[System Error: Invalid function call received]`, 
            sender: 'system'
          }]);
        }
      }

    } catch (error) {
      console.error("Error sending message:", error);
      const errorText = axios.isAxiosError(error) && error.response?.data?.error
        ? error.response.data.error
        : "Failed to get response from AI. Please try again.";
      
      setError(errorText);
      setMessages(prevMessages => [...prevMessages, {
        id: `error-${Date.now()}`,
        text: `Error: ${errorText}`,
        sender: 'system'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // before react markdown
  // const renderMessageContent = (text: string) => {
  //   return text.split('\n').map((line, index) => (
  //     <React.Fragment key={index}>
  //       {line}
  //       {index < text.split('\n').length - 1 && <br />}
  //     </React.Fragment>
  //   ));
  // };

  return (
    <div className='chatbox-area'>
      <div className='message-list'>
        {isLoading && messages.length === 0 && (
          <div className="loading-indicator">
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          </div>
        )}
        
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.sender}`}>
            {msg.sender === 'ai' ? (
              <ReactMarkdown>{msg.text}</ReactMarkdown>
            ) : (
              msg.text.split('\n').map((line, index) => (
                <React.Fragment key={index}>
                  {line}
                  {index < msg.text.split('\n').length - 1 && <br />}
                </React.Fragment>
              ))
            )}
          </div>
        ))}
        
        {isLoading && messages.length > 0 && (
          <div className="typing-indicator">
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {error && <div className="chat-error">{error}</div>}
      
      <div className='input-area'>
        <input
          ref={inputRef}
          type='text'
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder={sessionId ? 'Type your message...' : 'Start a session first'}
          disabled={isLoading || !sessionId}
        />
        
        <button 
          className={`rag-button ${ragActivated ? 'rag-active' : ''}`}
          onClick={handleTriggerRAG} 
          disabled={isRagLoading || !sessionId || ragActivated}
        >
          {isRagLoading ? 'Enhancing...' : ragActivated ? 'Context Enhanced' : 'Enhance'}
        </button>
        
        <button 
          onClick={handleSendMessage} 
          disabled={isLoading || !sessionId || inputValue.trim() === ''}
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
}

export default ChatBox;