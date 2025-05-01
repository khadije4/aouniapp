from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose
from flask_jwt_extended import verify_jwt_token, decode_token
from flask import redirect, url_for, request, session, flash
from functools import wraps

from ..models import User, Service, Booking, Message, Rating

class AdminRequiredMixin:
    """Mixin to ensure only admin users can access admin views"""
    def is_accessible(self):
        # First check if user is authenticated via session
        if session.get('user_id') and session.get('role') == 'admin':
            return True
        
        # If not in session, try to get from JWT token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                decoded_token = decode_token(token)
                user_id = decoded_token.get('sub')  # 'sub' contains the user ID
                
                # Verify this is an admin user
                user = User.query.get(user_id)
                if user and user.role == 'admin':
                    # Store in session for future requests
                    session['user_id'] = user_id
                    session['role'] = 'admin'
                    return True
            except:
                pass
                
        return False
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login_view'))

class AdminLoginView(BaseView):
    """Custom login view for admin"""
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email, role='admin').first()
            
            if user and user.verify_password(password):
                session['user_id'] = user.id
                session['role'] = 'admin'
                return redirect(url_for('admin.index'))
            else:
                flash('Invalid credentials or insufficient permissions')
        
        return self.render('admin/login.html')
    
    @expose('/logout/')
    def logout(self):
        session.pop('user_id', None)
        session.pop('role', None)
        return redirect(url_for('admin.login_view.index'))

class UserModelView(AdminRequiredMixin, ModelView):
    """Admin view for User model"""
    column_list = ['id', 'name', 'email', 'role', 'phone', 'city', 'created_at']
    column_searchable_list = ['name', 'email', 'phone']
    column_filters = ['role', 'city', 'created_at']
    form_excluded_columns = ['password', 'bookings_as_client', 'bookings_as_worker', 
                            'sent_messages', 'received_messages', 'ratings_given', 'ratings_received']
    
    def on_model_change(self, form, model, is_created):
        """Hash password if it's being created or updated"""
        if is_created:
            model.password = User.hash_password(form.password.data)

class ServiceModelView(AdminRequiredMixin, ModelView):
    """Admin view for Service model"""
    column_list = ['id', 'name', 'category', 'base_price', 'duration_minutes']
    column_searchable_list = ['name']
    column_filters = ['category', 'base_price', 'duration_minutes']
    form_excluded_columns = ['bookings']

class BookingModelView(AdminRequiredMixin, ModelView):
    """Admin view for Booking model"""
    column_list = ['id', 'client.name', 'worker.name', 'service.name', 'status', 
                  'scheduled_datetime', 'is_paid', 'created_at']
    column_searchable_list = ['address']
    column_filters = ['status', 'is_paid', 'scheduled_datetime', 'created_at']
    form_excluded_columns = ['rating']

class MessageModelView(AdminRequiredMixin, ModelView):
    """Admin view for Message model"""
    column_list = ['id', 'sender.name', 'receiver.name', 'message', 'timestamp', 'is_read']
    column_searchable_list = ['message']
    column_filters = ['is_read', 'timestamp']

class RatingModelView(AdminRequiredMixin, ModelView):
    """Admin view for Rating model"""
    column_list = ['id', 'booking.id', 'client.name', 'worker.name', 'rating', 'comment', 'created_at']
    column_searchable_list = ['comment']
    column_filters = ['rating', 'created_at']

def register_admin_views(admin, db):
    """Register all admin views"""
    # Add a custom login view
    admin.add_view(AdminLoginView(name='Login', endpoint='login_view'))
    
    # Add model views
    admin.add_view(UserModelView(User, db.session, category='Models'))
    admin.add_view(ServiceModelView(Service, db.session, category='Models'))
    admin.add_view(BookingModelView(Booking, db.session, category='Models'))
    admin.add_view(MessageModelView(Message, db.session, category='Models'))
    admin.add_view(RatingModelView(Rating, db.session, category='Models'))
