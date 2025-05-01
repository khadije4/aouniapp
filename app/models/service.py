from .. import db

class Service(db.Model):
    """Service model for different service categories"""
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.Enum('maid_monthly', 'maid_onetime', 'plumber', 'driver', 'babysitter'), nullable=False)
    description = db.Column(db.Text)
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    
    # Relations
    bookings = db.relationship('Booking', backref='service', lazy='dynamic')
    
    def to_dict(self):
        """Convert service object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'base_price': float(self.base_price),
            'duration_minutes': self.duration_minutes
        }
    
    def __repr__(self):
        return f'<Service {self.name}, {self.category}>'
