from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from ..models import User, Service, Booking
from .. import db, socketio

bookings = Blueprint('bookings', __name__)

@bookings.route('/', methods=['GET'])
@jwt_required()
def get_bookings():
    """Get bookings for the current user"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get query parameters for filtering
    status = request.args.get('status')
    
    # Apply filters based on role and status
    if current_user.role == 'client':
        query = Booking.query.filter_by(client_id=current_user_id)
    elif current_user.role == 'worker':
        query = Booking.query.filter_by(worker_id=current_user_id)
    else:  # Admin can see all bookings
        query = Booking.query
    
    if status:
        query = query.filter_by(status=status)
    
    # Sort by scheduled date (most recent first)
    query = query.order_by(Booking.scheduled_datetime.desc())
    
    bookings_list = query.all()
    return jsonify({
        'bookings': [booking.to_dict() for booking in bookings_list]
    }), 200

@bookings.route('/<int:booking_id>', methods=['GET'])
@jwt_required()
def get_booking(booking_id):
    """Get a specific booking"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    booking = Booking.query.get(booking_id)
    
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    # Ensure user has permission to view this booking
    if (current_user.role == 'client' and booking.client_id != current_user_id) or \
       (current_user.role == 'worker' and booking.worker_id != current_user_id) and \
       current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
    
    return jsonify({
        'booking': booking.to_dict()
    }), 200

@bookings.route('/', methods=['POST'])
@jwt_required()
def create_booking():
    """Create a new booking (client only)"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user is a client
    if current_user.role != 'client':
        return jsonify({'error': 'Only clients can create bookings'}), 403
    
    data = request.get_json()
    
    # Check if required fields are present
    for field in ['worker_id', 'service_id', 'scheduled_datetime', 'address']:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    # Validate worker and service existence
    worker = User.query.filter_by(id=data['worker_id'], role='worker').first()
    if not worker:
        return jsonify({'error': 'Worker not found'}), 404
    
    service = Service.query.get(data['service_id'])
    if not service:
        return jsonify({'error': 'Service not found'}), 404
    
    # Parse scheduled date
    try:
        scheduled_datetime = datetime.fromisoformat(data['scheduled_datetime'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
    
    try:
        booking = Booking(
            client_id=current_user_id,
            worker_id=data['worker_id'],
            service_id=data['service_id'],
            scheduled_datetime=scheduled_datetime,
            address=data['address'],
            payment_method=data.get('payment_method', 'cash'),
            status='pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Notify worker about new booking request
        socketio.emit(f'booking_notification_{booking.worker_id}', {
            'type': 'new_booking',
            'booking_id': booking.id,
            'client_name': current_user.name
        })
        
        return jsonify({
            'message': 'Booking created successfully',
            'booking': booking.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bookings.route('/<int:booking_id>/status', methods=['PUT'])
@jwt_required()
def update_booking_status(booking_id):
    """Update a booking status"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    # Ensure user has permission to update this booking
    if (current_user.role == 'client' and booking.client_id != current_user_id) or \
       (current_user.role == 'worker' and booking.worker_id != current_user_id) and \
       current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
    
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({'error': 'Missing status field'}), 400
    
    # Validate status transition
    valid_statuses = ['pending', 'accepted', 'in_progress', 'completed', 'paid', 'cancelled']
    if data['status'] not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
    
    # Handle specific role-based status update limitations
    if current_user.role == 'worker':
        # Workers can only accept, start, complete
        if data['status'] in ['paid', 'cancelled'] and booking.status != 'pending':
            return jsonify({'error': 'Unauthorized status change'}), 403
    
    if current_user.role == 'client':
        # Clients can only cancel or mark as paid
        if data['status'] not in ['cancelled', 'paid']:
            return jsonify({'error': 'Unauthorized status change'}), 403
        
        # Client can't cancel after service started
        if data['status'] == 'cancelled' and booking.status in ['in_progress', 'completed', 'paid']:
            return jsonify({'error': 'Cannot cancel booking at this stage'}), 403
    
    try:
        old_status = booking.status
        booking.status = data['status']
        
        # Update payment info if status is paid
        if data['status'] == 'paid':
            booking.is_paid = True
            booking.paid_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send notification to the other party
        target_id = booking.worker_id if current_user.role == 'client' else booking.client_id
        socketio.emit(f'booking_notification_{target_id}', {
            'type': 'status_update',
            'booking_id': booking.id,
            'old_status': old_status,
            'new_status': booking.status
        })
        
        return jsonify({
            'message': 'Booking status updated successfully',
            'booking': booking.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bookings.route('/<int:booking_id>', methods=['DELETE'])
@jwt_required()
def delete_booking(booking_id):
    """Delete a booking (admin only)"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
    
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    try:
        db.session.delete(booking)
        db.session.commit()
        
        return jsonify({
            'message': 'Booking deleted successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
