from datetime import datetime
import bcrypt
from .. import db

class User(db.Model):
    """User model for clients, workers and admins"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    role = db.Column(db.Enum('client', 'worker', 'admin'), nullable=False)
    phone = db.Column(db.String(15))
    city = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    bookings_as_client = db.relationship('Booking', foreign_keys='Booking.client_id', backref='client', lazy='dynamic')
    bookings_as_worker = db.relationship('Booking', foreign_keys='Booking.worker_id', backref='worker', lazy='dynamic')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy='dynamic')
    ratings_given = db.relationship('Rating', foreign_keys='Rating.client_id', backref='client', lazy='dynamic')
    ratings_received = db.relationship('Rating', foreign_keys='Rating.worker_id', backref='worker', lazy='dynamic')
    
    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password):
        """Verify password against stored hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'phone': self.phone,
            'city': self.city,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.name}, {self.role}>'
