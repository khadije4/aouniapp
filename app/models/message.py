from datetime import datetime
from .. import db

class Message(db.Model):
    """Message model for user communications"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        """Convert message object to dictionary"""
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message': self.message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_read': self.is_read
        }
    
    def __repr__(self):
        return f'<Message {self.id}, {self.sender_id} -> {self.receiver_id}>'
