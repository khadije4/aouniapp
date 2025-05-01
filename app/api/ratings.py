from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models import User, Booking, Rating
from .. import db, socketio

ratings = Blueprint('ratings', __name__)

@ratings.route('/worker/<int:worker_id>', methods=['GET'])
def get_worker_ratings(worker_id):
    """Get all ratings for a specific worker"""
    worker = User.query.filter_by(id=worker_id, role='worker').first()
    if not worker:
        return jsonify({'error': 'Worker not found'}), 404
    
    ratings_list = Rating.query.filter_by(worker_id=worker_id).all()
    
    # Calculate average rating
    ratings_count = len(ratings_list)
    average_rating = 0
    if ratings_count > 0:
        average_rating = sum(rating.rating for rating in ratings_list) / ratings_count
    
    return jsonify({
        'worker': worker.to_dict(),
        'ratings': [rating.to_dict() for rating in ratings_list],
        'average_rating': round(average_rating, 1),
        'count': ratings_count
    }), 200

@ratings.route('/booking/<int:booking_id>', methods=['POST'])
@jwt_required()
def create_rating(booking_id):
    """Create a rating for a booking (client only)"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user is a client
    if current_user.role != 'client':
        return jsonify({'error': 'Only clients can create ratings'}), 403
    
    # Check if booking exists and belongs to this client
    booking = Booking.query.filter_by(id=booking_id, client_id=current_user_id).first()
    if not booking:
        return jsonify({'error': 'Booking not found or not authorized'}), 404
    
    # Check if booking is completed or paid
    if booking.status not in ['completed', 'paid']:
        return jsonify({'error': 'Cannot rate an incomplete booking'}), 400
    
    # Check if rating already exists
    existing_rating = Rating.query.filter_by(booking_id=booking_id).first()
    if existing_rating:
        return jsonify({'error': 'Rating already exists for this booking'}), 400
    
    data = request.get_json()
    
    # Check if required fields are present
    if 'rating' not in data:
        return jsonify({'error': 'Rating value is required'}), 400
    
    # Validate rating value
    if not isinstance(data['rating'], int) or data['rating'] < 1 or data['rating'] > 5:
        return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400
    
    try:
        rating = Rating(
            booking_id=booking_id,
            client_id=current_user_id,
            worker_id=booking.worker_id,
            rating=data['rating'],
            comment=data.get('comment', '')
        )
        
        db.session.add(rating)
        db.session.commit()
        
        # Notify worker about the new rating
        socketio.emit(f'rating_notification_{booking.worker_id}', {
            'type': 'new_rating',
            'rating': rating.to_dict()
        })
        
        return jsonify({
            'message': 'Rating created successfully',
            'rating': rating.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
