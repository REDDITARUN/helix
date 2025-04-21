# app/services/document_service.py
import os
import io
import json 
import time 
from uuid import uuid4
from flask import current_app
from pinecone import Pinecone 
from pypdf import PdfReader
import google.generativeai as genai

def split_text_basic(text: str, chunk_size=1000, chunk_overlap=100):
    if not text:
        return []
    if chunk_overlap >= chunk_size:
        chunk_overlap = int(chunk_size * 0.1) 

    chunks = []
    start_index = 0
    text_len = len(text)

    while start_index < text_len:
        end_index = start_index + chunk_size
        chunks.append(text[start_index:end_index])

        next_start_index = start_index + (chunk_size - chunk_overlap)

        if next_start_index <= start_index:
            print(f"Warning: Text splitting potential loop detected. Moving forward by chunk_size. Start: {start_index}")
            start_index += chunk_size 
        else:
            start_index = next_start_index

    return [chunk for chunk in chunks if chunk.strip()]


class DocumentService:
    def __init__(self):
        self.pinecone_api_key = current_app.config.get('PINECONE_API_KEY')
        self.index_name = current_app.config.get('PINECONE_INDEX_NAME')
        self.embedding_model_name = current_app.config.get('EMBEDDING_MODEL_NAME')
        self.google_api_key = current_app.config.get('GOOGLE_API_KEY')

        if not all([self.pinecone_api_key, self.index_name, self.embedding_model_name, self.google_api_key]):
            raise ValueError("Configuration Error: Missing Pinecone API Key/Index, Google API Key, or Embedding Model name.")

        try:
             if not getattr(genai, '_config', None) or not genai._config.api_key:
                  print("Configuring Google GenAI in DocumentService...")
                  genai.configure(api_key=self.google_api_key)
             else:
                  print("Google GenAI appears already configured.")
        except Exception as e:
             print(f"Error configuring Google GenAI: {e}")
             raise ValueError("Configuration Error: Could not configure Google Generative AI.") from e

        self.embedding_dim = 768

        try:
            print("Initializing Pinecone client...")
            self.pc = Pinecone(api_key=self.pinecone_api_key)

            print(f"Checking for Pinecone index '{self.index_name}'...")
            index_list = self.pc.list_indexes()
            self.index = self.pc.Index(self.index_name)
            index_stats = self.index.describe_index_stats()
            print(f"Successfully connected. Index stats: {index_stats}")

            pinecone_dim = getattr(index_stats, 'dimension', None) 
            if pinecone_dim is None:
                 raise ValueError(f"Could not determine dimension for Pinecone index '{self.index_name}'. Stats: {index_stats}")

            if pinecone_dim != self.embedding_dim:
                raise ValueError(f"Configuration Error: Embedding model dimension ({self.embedding_dim}) for '{self.embedding_model_name}' does not match Pinecone index dimension ({pinecone_dim}) for '{self.index_name}'!")
            print(f"Dimension check passed: Pinecone ({pinecone_dim}) == Embedding Model ({self.embedding_dim}).")

        except Exception as e:
            print(f"Fatal Error during Pinecone Initialization/Verification: {e}")
            raise ValueError(f"Pinecone Error: Could not initialize, connect to, or verify index '{self.index_name}'. Please check API key, index name, and network connectivity. Original error: {e}") from e

        print(f"DocumentService initialized successfully. Using Google model '{self.embedding_model_name}' (Dim: {self.embedding_dim}) and Pinecone index '{self.index_name}'.")


    def _extract_text_from_pdf(self, file_stream) -> str:
        try:
            reader = PdfReader(file_stream)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            print(f"Extracted ~{len(text)} chars from PDF.")
            return text.strip()
        except Exception as e:
            print(f"Error reading PDF stream: {e}")
            return "" 


    def _extract_text_from_txt(self, file_stream) -> str:
        try:
            content_bytes = file_stream.read()
            text = content_bytes.decode('utf-8', errors='replace').strip()
            print(f"Extracted {len(text)} chars from TXT.")
            return text
        except Exception as e:
            print(f"Error reading TXT stream: {e}")
            return "" 


    def process_and_upsert(self, file_storage, filename: str):
        print(f"Starting processing for file: {filename}")
        _, file_extension = os.path.splitext(filename)
        file_extension = file_extension.lower()

        text = ""
        file_stream = file_storage.stream 
        if file_extension == '.pdf':
            text = self._extract_text_from_pdf(file_stream)
        elif file_extension == '.txt':
            text = self._extract_text_from_txt(file_stream)
        else:
            print(f"Error: Unsupported file type received: {file_extension}")
            raise ValueError(f"Unsupported file type: {file_extension}")

        if not text:
            print(f"Warning: No text could be extracted from {filename}.")
            return {"message": "No text content found in the file.", "filename": filename, "status": "warning_no_text"}

        print(f"Chunking text (length: {len(text)})...")
        chunks = split_text_basic(text, chunk_size=1000, chunk_overlap=100) 
        if not chunks:
            print(f"Warning: Text from {filename} resulted in zero chunks after splitting.")
            return {"message": "Could not process text into meaningful chunks.", "filename": filename, "status": "warning_no_chunks"}
        print(f"Split into {len(chunks)} chunks.")

        print(f"Generating embeddings for {len(chunks)} chunks using '{self.embedding_model_name}'...")
        embeddings = []
        try:
            for i, chunk in enumerate(chunks):
                if not chunk.strip(): 
                     print(f"Skipping empty chunk at index {i}")
                     continue
                result = genai.embed_content(
                    model=self.embedding_model_name,
                    content=chunk,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
                if (i + 1) % 20 == 0: 
                     print(f"  Generated embedding for chunk {i+1}/{len(chunks)}")
            print("Finished generating embeddings.")

        except Exception as e:
             print(f"Error generating embeddings with Google API: {e}")
             raise ValueError("Processing Error: Failed to generate text embeddings using Google API.") from e

        if len(embeddings) != len(chunks):
             print(f"Warning: Number of embeddings ({len(embeddings)}) does not match number of chunks ({len(chunks)}). This might indicate skipped chunks.")

        print("Preparing vectors for Pinecone...")
        vectors_to_upsert = []
        valid_chunk_indices = [i for i, chunk in enumerate(chunks) if chunk.strip()]
        if len(valid_chunk_indices) != len(embeddings):
             print(f"Error: Mismatch between valid chunks ({len(valid_chunk_indices)}) and generated embeddings ({len(embeddings)}). Aborting upsert.")
             raise ValueError("Internal Processing Error: Embedding count mismatch.")

        for idx, embedding in enumerate(embeddings):
            original_chunk_index = valid_chunk_indices[idx]
            chunk_content = chunks[original_chunk_index]
            vector_id = f"{filename}-{original_chunk_index}-{uuid4()}" 
            metadata = {
                "filename": filename,
                "chunk_index": original_chunk_index,
                "text_preview": chunk_content[:500]
            }
            vectors_to_upsert.append((vector_id, embedding, metadata))

        batch_size = 100 
        upserted_count = 0
        print(f"Upserting {len(vectors_to_upsert)} vectors to Pinecone index '{self.index_name}'...")
        try:
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                if not batch: continue
                print(f"  Upserting batch {i//batch_size + 1} (size: {len(batch)})...")
                upsert_response = self.index.upsert(vectors=batch)
                
                if hasattr(upsert_response, 'upserted_count') and upsert_response.upserted_count is not None:
                     upserted_count += upsert_response.upserted_count
                     print(f"  Batch {i//batch_size + 1} upserted {upsert_response.upserted_count} vectors.")
                else:
                     print(f"  Batch {i//batch_size + 1} upserted (count not available in response). Assuming {len(batch)}.")
                     upserted_count += len(batch) 

        except Exception as e:
            print(f"Error during Pinecone upsert: {e}")
            raise ValueError(f"Database Error: Failed to save document vectors to Pinecone index '{self.index_name}'.") from e

        print(f"Successfully upserted {upserted_count} vectors for {filename}.")
        return {
            "message": f"Successfully processed and indexed '{filename}'.",
            "filename": filename,
            "vector_count": upserted_count,
            "status": "success"
        }