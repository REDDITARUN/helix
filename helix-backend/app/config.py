import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    
    PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
    PINECONE_INDEX_NAME = os.environ.get('PINECONE_INDEX_NAME', 'helix-documents')
    EMBEDDING_MODEL_NAME = 'models/text-embedding-004'
    
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///helix.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY') 
    
    