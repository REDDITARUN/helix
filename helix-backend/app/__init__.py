from flask import Flask
from flask_cors import CORS
from .config import Config
from .extensions import db, migrate, socketio

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*") 
    
    from .api import chat_bp, sequence_bp, document_bp
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(sequence_bp, url_prefix='/api/sequence')
    app.register_blueprint(document_bp, url_prefix='/api/documents')
    
    return app