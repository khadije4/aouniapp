from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models import User, Service
from .. import db

services = Blueprint('services', __name__)

@services.route('/', methods=['GET'])
def get_services():
    """Get all services"""
    # Get query parameters for filtering
    category = request.args.get('category')
    
    # Apply filters if provided
    query = Service.query
    if category:
        query = query.filter_by(category=category)
    
    services_list = query.all()
    return jsonify({
        'services': [service.to_dict() for service in services_list]
    }), 200

@services.route('/<int:service_id>', methods=['GET'])
def get_service(service_id):
    """Get a specific service"""
    service = Service.query.get(service_id)
    if not service:
        return jsonify({'error': 'Service not found'}), 404
    
    return jsonify({
        'service': service.to_dict()
    }), 200

@services.route('/', methods=['POST'])
@jwt_required()
def create_service():
    """Create a new service (admin only)"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Check if user is admin
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
    
    data = request.get_json()
    
    # Check if required fields are present
    for field in ['name', 'category', 'base_price', 'duration_minutes']:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    # Validate category
    valid_categories = ['maid_monthly', 'maid_onetime', 'plumber', 'driver', 'babysitter']
    if data['category'] not in valid_categories:
        return jsonify({'error': f'Invalid category. Must be one of: {", ".join(valid_categories)}'}), 400
    
    try:
        service = Service(
            name=data['name'],
            category=data['category'],
            description=data.get('description', ''),
            base_price=data['base_price'],
            duration_minutes=data['duration_minutes']
        )
        
        db.session.add(service)
        db.session.commit()
        
        return jsonify({
            'message': 'Service created successfully',
            'service': service.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@services.route('/<int:service_id>', methods=['PUT'])
@jwt_required()
def update_service(service_id):
    """Update a service (admin only)"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Check if user is admin
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
    
    service = Service.query.get(service_id)
    if not service:
        return jsonify({'error': 'Service not found'}), 404
    
    data = request.get_json()
    
    try:
        # Update service fields
        if 'name' in data:
            service.name = data['name']
        if 'category' in data:
            # Validate category
            valid_categories = ['maid_monthly', 'maid_onetime', 'plumber', 'driver', 'babysitter']
            if data['category'] not in valid_categories:
                return jsonify({'error': f'Invalid category. Must be one of: {", ".join(valid_categories)}'}), 400
            service.category = data['category']
        if 'description' in data:
            service.description = data['description']
        if 'base_price' in data:
            service.base_price = data['base_price']
        if 'duration_minutes' in data:
            service.duration_minutes = data['duration_minutes']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Service updated successfully',
            'service': service.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@services.route('/<int:service_id>', methods=['DELETE'])
@jwt_required()
def delete_service(service_id):
    """Delete a service (admin only)"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Check if user is admin
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
    
    service = Service.query.get(service_id)
    if not service:
        return jsonify({'error': 'Service not found'}), 404
    
    try:
        db.session.delete(service)
        db.session.commit()
        
        return jsonify({
            'message': 'Service deleted successfully'
        }), 200
    
    except Exception as e:
