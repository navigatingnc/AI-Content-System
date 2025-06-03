from src.models.user import db
from src.models.ai_provider import AIProvider, ProviderAccount
from datetime import datetime
import uuid
import json

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    task_type = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.Integer, nullable=False, default=1)  # 1-5, 5 being highest
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    assignments = db.relationship('TaskAssignment', backref='task', lazy=True)
    content_items = db.relationship('Content', backref='task', lazy=True)
    
    def __repr__(self):
        return f'<Task {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class TaskAssignment(db.Model):
    __tablename__ = 'task_assignments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = db.Column(db.String(36), db.ForeignKey('tasks.id'), nullable=False)
    provider_id = db.Column(db.String(36), db.ForeignKey('ai_providers.id'), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey('provider_accounts.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, processing, completed, failed
    attempt_count = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text, nullable=True)
    tokens_used = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    provider = db.relationship('AIProvider', backref='task_assignments')
    
    def __repr__(self):
        return f'<TaskAssignment {self.id}>'


class Content(db.Model):
    __tablename__ = 'content'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = db.Column(db.String(36), db.ForeignKey('tasks.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # text, code, image, etc.
    content_data = db.Column(db.Text, nullable=True)  # For text/code content
    file_path = db.Column(db.String(255), nullable=True)  # For file-based content like images
    metadata = db.Column(db.Text, nullable=True)  # JSON string of metadata
    version = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default='draft')  # draft, final, archived
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Content {self.title}>'
    
    def get_metadata(self):
        if self.metadata:
            return json.loads(self.metadata)
        return {}
    
    def set_metadata(self, metadata_dict):
        self.metadata = json.dumps(metadata_dict)
