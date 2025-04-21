import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import ChatBox from './components/chatbox/ChatBox';
import WorkSpace from './components/workspace/WorkSpace';
import NavBar from './components/navbar/NavBar';
import DocumentUpload from './components/documents/DocumentUpload';
import { Sequence, FunctionCall } from './types'; 

const API_BASE_URL = 'http://127.0.0.1:5000/api'; // i'll change this later! [Dont Forget]

type ActiveView = 'workspace' | 'documents';

function App() {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [sequences, setSequences] = useState<Sequence[]>([]);
  const [isProcessingSequence, setIsProcessingSequence] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<ActiveView>('workspace');
  
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const handleNewSession = async () => {
    console.log('Starting new session...');
    setError(null);
    setSequences([]);
    setIsProcessingSequence(false); 
    try {
      const response = await axios.post<{ session_id: number }>(`${API_BASE_URL}/chat/`);
      setSessionId(response.data.session_id);
      console.log('New session created:', response.data.session_id);
    } catch (err) {
      console.error("Error starting new session:", err);
      setError("Failed to start a new session. Please try again.");
      setSessionId(null);
    }
  };


  const handleFunctionCall = async (functionCall: FunctionCall) => { 
      if (!sessionId) {
        setError("Cannot process sequences without an active session.");
        return;
      }
      console.log(`Function call received: ${functionCall.name}`, functionCall.args);
      setIsProcessingSequence(true); 
      setError(null);
      

      try {
          let response;
          
          if (functionCall.name === 'generate_outreach_sequences') {
              
               console.log('App: Calling GENERATE endpoint');
               
               setSequences([]);
               response = await axios.post<Sequence[]>(
                  `${API_BASE_URL}/sequence/${sessionId}/generate`,
                  
                  { context: functionCall.args }
              );
               setSequences(response.data); 
               console.log('App: Sequences generated:', response.data);

          } else if (functionCall.name === 'modify_sequences') {
              
               console.log('App: Calling MODIFY endpoint');
               
               if (!functionCall.args.modification_instruction) {
                   throw new Error("Modification function called by AI without modification_instruction.");
               }
               response = await axios.post<Sequence[]>(
                   `${API_BASE_URL}/sequence/${sessionId}/modify`,
                   {
                       
                       instruction: functionCall.args.modification_instruction
                   }
               );
               setSequences(response.data); 
               console.log('App: Sequences modified:', response.data);
          } else {
             
               throw new Error(`Unknown function call received in App: ${functionCall.name}`);
          }

      } catch (err: any) {
          console.error("Error processing sequence function call:", err);
          const errorMsg = axios.isAxiosError(err) && err.response?.data?.error
              ? err.response.data.error
              : err.message || "Failed to process sequence request.";
          setError(errorMsg);
         
      } finally {
          setIsProcessingSequence(false); 
      }
  };



  const handleUpdateSequence = async (sequenceId: number, newContent: string) => {
   
     if (!sessionId) return;
     setError(null);
     const originalSequences = [...sequences];
     setSequences(prev => prev.map(seq =>
       seq.seq_id === sequenceId ? { ...seq, content: newContent, role: 'edited' } : seq
     ));
     try {
       await axios.put(
         `${API_BASE_URL}/sequence/${sequenceId}`,
         { content: newContent }
       );
       console.log(`Sequence ${sequenceId} updated successfully.`);
     } catch (err) {
       console.error(`Error updating sequence ${sequenceId}:`, err);
       setError(`Failed to save changes for sequence ${sequenceId}.`);
       setSequences(originalSequences);
     }
  };


  const showWorkspace = () => setActiveView('workspace');
  const showDocuments = () => setActiveView('documents');

  return (
    <div className="app-container">
      <NavBar
        onNewSession={handleNewSession}
        currentSessionId={sessionId}
        activeView={activeView} 
        onShowWorkspace={showWorkspace} 
        onShowDocuments={showDocuments}
      />
       {error && <div className="global-error">Error: {error}</div>}
      <div className="main-content">
      
        <ChatBox
          sessionId={sessionId}
          onFunctionCall={handleFunctionCall}
          key={sessionId}
        />
        
        <div className="right-panel">
          {activeView === 'workspace' && (
            <WorkSpace
              sessionId={sessionId}
              sequences={sequences}
              isGenerating={isProcessingSequence}
              onUpdateSequence={handleUpdateSequence}
            />
          )}
          {activeView === 'documents' && (
            <DocumentUpload />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;