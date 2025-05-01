from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models import User
from .. import db

users = Blueprint('users', __name__)

@users.route('/', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users (admin only)"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Check if user is admin
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Get query parameters for filtering
    role = request.args.get('role')
    
    # Apply filters if provided
    query = User.query
    if role:
        query = query.filter_by(role=role)
    
    users_list = query.all()
    return jsonify({
        'users': [user.to_dict() for user in users_list]
    }), 200

@users.route('/workers', methods=['GET'])
def get_workers():
    """Get all workers (public endpoint)"""
    workers = User.query.filter_by(role='worker').all()
    return jsonify({
        'workers': [worker.to_dict() for worker in workers]
    }), 200

@users.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get a specific user"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Users can view their own profile or admins can view any profile
    if current_user_id != user_id and (not current_user or current_user.role != 'admin'):
        return jsonify({'error': 'Unauthorized access'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': user.to_dict()
    }), 200

@users.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update a user's profile"""
    current_user_id = get_jwt_identity()
    
    # Users can only update their own profile
    if current_user_id != user_id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    try:
        # Update user fields (excluding email and role)
        if 'name' in data:
            user.name = data['name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'city' in data:
            user.city = data['city']
        if 'password' in data:
            user.password = User.hash_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
