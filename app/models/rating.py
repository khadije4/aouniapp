from datetime import datetime
from .. import db

class Rating(db.Model):
    """Rating model for service evaluations"""
    __tablename__ = 'ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Scale of 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert rating object to dictionary"""
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'client_id': self.client_id,
            'worker_id': self.worker_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Rating {self.id}, {self.rating}/5>'
