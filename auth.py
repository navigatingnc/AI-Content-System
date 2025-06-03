from user import db, User
from ai_provider import AIProvider, ProviderAccount
from task import Task, TaskAssignment, Content
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token
import datetime

jwt = JWTManager()

def init_auth(app):
    """Initialize authentication components"""
    jwt.init_app(app)
    
    # Set JWT configuration
    app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(days=30)

def register_user(username, email, password, role='user'):
    """Register a new user"""
    # Check if user already exists
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return None, "Username or email already exists"
    
    # Create new user
    password_hash = generate_password_hash(password)
    new_user = User(username=username, email=email, password_hash=password_hash, role=role)
    
    db.session.add(new_user)
    db.session.commit()
    
    return new_user, None

def authenticate_user(username_or_email, password):
    """Authenticate a user and return tokens"""
    # Find user by username or email
    user = User.query.filter_by(username=username_or_email).first() or User.query.filter_by(email=username_or_email).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return None, None, "Invalid credentials"
    
    # Update last login time
    user.last_login = datetime.datetime.utcnow()
    db.session.commit()
    
    # Create tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return access_token, refresh_token, None

def get_user_by_id(user_id):
    """Get user by ID"""
    return User.query.get(user_id)

def update_user(user_id, username=None, email=None, password=None, role=None):
    """Update user information"""
    user = User.query.get(user_id)
    if not user:
        return None, "User not found"
    
    if username:
        # Check if username is already taken by another user
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user_id:
            return None, "Username already taken"
        user.username = username
    
    if email:
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user_id:
            return None, "Email already taken"
        user.email = email
    
    if password:
        user.password_hash = generate_password_hash(password)
    
    if role and user.role != role:
        user.role = role
    
    db.session.commit()
    return user, None
