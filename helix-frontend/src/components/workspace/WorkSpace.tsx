
import { useState, useEffect } from 'react';
import './WorkSpace.css';
import { Sequence } from '../../types'; 

interface WorkSpaceProps {
  sessionId: number | null;
  sequences: Sequence[];
  isGenerating: boolean;
  onUpdateSequence: (sequenceId: number, newContent: string) => Promise<void>; 
}

function WorkSpace({ sessionId, sequences, isGenerating, onUpdateSequence }: WorkSpaceProps) {

  //  state to manage the content being edited in each textarea
  const [editedContent, setEditedContent] = useState<{ [key: number]: string }>({});
  const [isSaving, setIsSaving] = useState<number | null>(null); 
  const [copySuccess, setCopySuccess] = useState<number | null>(null); 

  //  local edit state when sequences prop changes 
  useEffect(() => {
    const initialEdits: { [key: number]: string } = {};
    sequences.forEach(seq => {
      initialEdits[seq.seq_id] = seq.content;
    });
    setEditedContent(initialEdits);
  }, [sequences]); // dependency on the sequences prop

  const handleContentChange = (id: number, newContent: string) => {
    setEditedContent(prev => ({
      ...prev,
      [id]: newContent
    }));
  };

  const handleCopyToClipboard = (id: number) => {
     const textToCopy = editedContent[id] || '';
     navigator.clipboard.writeText(textToCopy)
       .then(() => {
         console.log(`Copied sequence ${id} to clipboard`);
         setCopySuccess(id);
         setTimeout(() => setCopySuccess(null), 1500); 
       })
       .catch(err => {
         console.error('Failed to copy text: ', err);
         
       });
   };

  const handleSave = async (id: number) => {
     if (isSaving === id) return; 
     setIsSaving(id);
     try {
       await onUpdateSequence(id, editedContent[id]);
      
     } catch (err) {
       
       console.error("Error during save from WorkSpace:", err)
     } finally {
       setIsSaving(null);
     }
   };

  return (
    <div className='workspace-area'>
      <div className='workspace-area-content'>
        <h2>Generated Samples</h2>

        
        {isGenerating && (
          <div className="workspace-loading">Generating sequences... Please wait.</div>
        )}

       
        {!isGenerating && !sessionId && (
          <div className="workspace-placeholder">Start a new session to generate sequences.</div>
        )}
        {!isGenerating && sessionId && sequences.length === 0 && (
          <div className="workspace-placeholder">Chat with the AI to gather information, and sequences will appear here once generated.</div>
        )}

     
        {!isGenerating && sequences.length > 0 && (
          <div className='samples-grid'>
            {sequences.map((sequence) => (
              <div key={sequence.seq_id} className='sample-card'>
                <textarea
                  value={editedContent[sequence.seq_id] || ''} 
                  onChange={(e) => handleContentChange(sequence.seq_id, e.target.value)}
                  rows={6} 
                  disabled={isSaving === sequence.seq_id} 
                />
                <div className="card-actions">
                   <button
                     onClick={() => handleCopyToClipboard(sequence.seq_id)}
                     className="copy-button"
                     disabled={isSaving === sequence.seq_id}
                    >
                     {copySuccess === sequence.seq_id ? 'Copied!' : 'Copy'}
                   </button>
                   <button
                     onClick={() => handleSave(sequence.seq_id)}
                     className="save-button"
                     disabled={
                       isSaving === sequence.seq_id || 
                       editedContent[sequence.seq_id] === sequence.content 
                     }
                     >
                     {isSaving === sequence.seq_id ? 'Saving...' : 'Save Edit'}
                   </button>
                 </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default WorkSpace;