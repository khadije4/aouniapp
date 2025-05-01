from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_admin import Admin

from .config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO()
admin = Admin(name='aouni Admin', template_mode='bootstrap3')

def create_app(config_name='default'):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    CORS(app)
    admin.init_app(app)
    
    # Register blueprints
    from .api.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/api/auth')
    
    from .api.users import users as users_blueprint
    app.register_blueprint(users_blueprint, url_prefix='/api/users')
    
    from .api.services import services as services_blueprint
    app.register_blueprint(services_blueprint, url_prefix='/api/services')
    
    from .api.bookings import bookings as bookings_blueprint
    app.register_blueprint(bookings_blueprint, url_prefix='/api/bookings')
    
    from .api.messages import messages as messages_blueprint
    app.register_blueprint(messages_blueprint, url_prefix='/api/messages')
    
    # Register admin views
    from .admin.views import register_admin_views
    register_admin_views(admin, db)
    
    return app
