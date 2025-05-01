import os
from app import create_app, db, socketio
from app.models import User, Service, Booking, Message, Rating

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    """Add database instance and models to flask shell context"""
    return {
        'db': db,
        'User': User,
        'Service': Service,
        'Booking': Booking,
        'Message': Message,
        'Rating': Rating
    }

@app.cli.command("init-db")
def init_db():
    """Initialize the database with some sample data"""
    # Create tables
    db.create_all()
    
    # Check if there's already an admin user
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        # Create admin user
        admin = User(
            name='Admin User',
            email='admin@aouni.com',
            password=User.hash_password('admin123'),
            role='admin',
            phone='+1234567890',
            city='Admin City'
        )
        db.session.add(admin)
    
    # Add some sample services if none exist
    if Service.query.count() == 0:
        services = [
            Service(
                name='Ménage mensuel',
                category='maid_monthly',
                description='Service régulier de nettoyage',
                base_price=120.00,
                duration_minutes=180
            ),
            Service(
                name='Ménage ponctuel',
                category='maid_onetime',
                description='Intervention unique',
                base_price=80.00,
                duration_minutes=120
            ),
            Service(
                name='Plomberie',
                category='plumber',
                description='Réparation et installation',
                base_price=50.00,
                duration_minutes=60
            ),
            Service(
                name='Chauffeur',
                category='driver',
                description='Transport privé',
                base_price=25.00,
                duration_minutes=60
            ),
            Service(
                name='Garde d\'enfants',
                category='babysitter',
                description='Babysitting',
                base_price=15.00,
                duration_minutes=60
            )
        ]
        
        for service in services:
            db.session.add(service)
    
    # Commit changes
    db.session.commit()
    print('Database initialized with sample data!')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
