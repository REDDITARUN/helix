from datetime import datetime
from ..extensions import db

class Session(db.Model):
    s_id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = db.relationship('Message', backref='session', lazy='dynamic')
    sequences = db.relationship('Sequence', backref='session', lazy='dynamic')
    
    def __repr__(self):
        return f'<Session {self.id}>'