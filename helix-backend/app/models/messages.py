from datetime import datetime
from ..extensions import db

class Message(db.Model):
    session_id = db.Column(db.Integer, db.ForeignKey('session.s_id'), nullable=False)
    msg_id = db.Column(db.Integer, primary_key=True)
    msg_role = db.Column(db.String(20), nullable=False) 
    msg_content = db.Column(db.Text, nullable=False)  
    msg_created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message {self.msg_id} {self.msg_role}>'