from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from ..models import User
from .. import db

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Check if required fields are present
    for field in ['name', 'email', 'password', 'role', 'phone']:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    # Validate role
    if data['role'] not in ['client', 'worker']:
        return jsonify({'error': 'Invalid role. Must be client or worker'}), 400
    
    # Create new user
    try:
        user = User(
            name=data['name'],
            email=data['email'],
            password=User.hash_password(data['password']),
            role=data['role'],
            phone=data['phone'],
            city=data.get('city')
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Generate access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth.route('/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.get_json()
    
    # Check if required fields are present
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    # Find the user
    user = User.query.filter_by(email=data['email']).first()
    
    # Check if user exists and password is correct
    if not user or not user.verify_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Generate access token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token
    }), 200

@auth.route('/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get the current user's profile"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': user.to_dict()
    }), 200
