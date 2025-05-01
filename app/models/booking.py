from datetime import datetime
from .. import db

class Booking(db.Model):
    """Booking model for service reservations"""
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    status = db.Column(db.Enum('pending', 'accepted', 'in_progress', 'completed', 'paid', 'cancelled'), 
                     default='pending', nullable=False)
    scheduled_datetime = db.Column(db.DateTime, nullable=False)
    address = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.Enum('cash', 'transfer'))
    is_paid = db.Column(db.Boolean, default=False)
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    rating = db.relationship('Rating', backref='booking', uselist=False)
    
    def to_dict(self):
        """Convert booking object to dictionary"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'worker_id': self.worker_id,
            'service_id': self.service_id,
            'status': self.status,
            'scheduled_datetime': self.scheduled_datetime.isoformat() if self.scheduled_datetime else None,
            'address': self.address,
            'payment_method': self.payment_method,
            'is_paid': self.is_paid,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Booking {self.id}, {self.status}>'
