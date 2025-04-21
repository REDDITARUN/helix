import { useState, useCallback } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import './DocumentUpload.css'; 
const API_BASE_URL = 'http://127.0.0.1:5000/api';

interface UploadResponse {
    message: string;
    filename: string;
    vector_count?: number;
    status: 'success' | 'warning' | 'error';
}

function DocumentUpload() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Only take the first file for single upload
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
      setUploadStatus(`Selected file: ${acceptedFiles[0].name}`);
      setUploadError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
    },
    multiple: false 
  });

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadError("Please select a file first.");
      return;
    }

    setIsUploading(true);
    setUploadStatus(`Uploading ${selectedFile.name}...`);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', selectedFile); 

    try {
      const response = await axios.post<UploadResponse>(
        `${API_BASE_URL}/documents/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      setUploadStatus(response.data.message || `Successfully processed ${response.data.filename}.`);
      setSelectedFile(null); // Clear selection after successful upload
    } catch (err: any) {
      console.error("Upload failed:", err);
      const errorMsg = axios.isAxiosError(err) && err.response?.data?.error
        ? err.response.data.error
        : err.message || "An unknown error occurred during upload.";
      setUploadError(`Upload failed: ${errorMsg}`);
      setUploadStatus(null); 
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="document-upload-area">
      <h2>Upload Documents</h2>
      <p>Upload company, job description, or candidate information (PDF or TXT).</p>

      <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
        <input {...getInputProps()} />
        {
          isDragActive ?
            <p>Drop the file here ...</p> :
            <p>Drag 'n' drop a file here, or click to select a file</p>
        }
        <p className="dropzone-hint">(Only *.pdf and *.txt files)</p>
      </div>

      {selectedFile && !isUploading && (
        <div className="file-info">
          Selected: {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
        </div>
      )}

      {uploadStatus && <div className="upload-status">{uploadStatus}</div>}
      {uploadError && <div className="upload-error">{uploadError}</div>}

      <button
        onClick={handleUpload}
        disabled={!selectedFile || isUploading}
        className="upload-button"
      >
        {isUploading ? 'Uploading...' : 'Upload and Process'}
      </button>
    </div>
  );
}

export default DocumentUpload;