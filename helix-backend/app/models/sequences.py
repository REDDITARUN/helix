from datetime import datetime
from ..extensions import db

class Sequence(db.Model):
    session_id = db.Column(db.Integer, db.ForeignKey('session.s_id'), nullable=False)
    seq_id = db.Column(db.Integer, primary_key=True)
    seq_role = db.Column(db.String(50), nullable=False, default='generated')
    seq_content = db.Column(db.Text, nullable=False)  
    seq_created_at = db.Column(db.DateTime, default=datetime.utcnow)
    seq_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Sequence {self.seq_id} Session {self.session_id}>'