from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, and_

from ..models import User, Message
from .. import db, socketio

messages = Blueprint('messages', __name__)

@messages.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """Get all conversations for the current user"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get all users that the current user has exchanged messages with
    sent_messages = Message.query.filter_by(sender_id=current_user_id).all()
    received_messages = Message.query.filter_by(receiver_id=current_user_id).all()
    
    # Extract unique user IDs
    conversation_user_ids = set()
    for message in sent_messages:
        conversation_user_ids.add(message.receiver_id)
    for message in received_messages:
        conversation_user_ids.add(message.sender_id)
    
    # Get user details for each conversation
    conversations = []
    for user_id in conversation_user_ids:
        user = User.query.get(user_id)
        if user:
            # Get the last message exchanged
            last_message = Message.query.filter(
                or_(
                    and_(Message.sender_id == current_user_id, Message.receiver_id == user_id),
                    and_(Message.sender_id == user_id, Message.receiver_id == current_user_id)
                )
            ).order_by(Message.timestamp.desc()).first()
            
            conversations.append({
                'user': user.to_dict(),
                'last_message': last_message.to_dict() if last_message else None,
                'unread_count': Message.query.filter_by(
                    sender_id=user_id, receiver_id=current_user_id, is_read=False
                ).count()
            })
    
    return jsonify({
        'conversations': conversations
    }), 200

@messages.route('/conversation/<int:user_id>', methods=['GET'])
@jwt_required()
def get_conversation(user_id):
    """Get messages between current user and another user"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    other_user = User.query.get(user_id)
    if not other_user:
        return jsonify({'error': 'Conversation user not found'}), 404
    
    # Get all messages between the two users
    messages_list = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user_id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == current_user_id)
        )
    ).order_by(Message.timestamp.asc()).all()
    
    # Mark all received messages as read
    unread_messages = Message.query.filter_by(
        sender_id=user_id, receiver_id=current_user_id, is_read=False
    ).all()
    
    for message in unread_messages:
        message.is_read = True
    
    db.session.commit()
    
    return jsonify({
        'messages': [message.to_dict() for message in messages_list]
    }), 200

@messages.route('/', methods=['POST'])
@jwt_required()
def send_message():
    """Send a message to another user"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Check if required fields are present
    if 'receiver_id' not in data or 'message' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if receiver exists
    receiver = User.query.get(data['receiver_id'])
    if not receiver:
        return jsonify({'error': 'Receiver not found'}), 404
    
    try:
        message = Message(
            sender_id=current_user_id,
            receiver_id=data['receiver_id'],
            message=data['message']
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Emit real-time notification
        socketio.emit(f'message_notification_{data["receiver_id"]}', {
            'message': message.to_dict(),
            'sender': current_user.to_dict()
        })
        
        return jsonify({
            'message': 'Message sent successfully',
            'data': message.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
