from user import db
from datetime import datetime
import uuid
import json

class AIProvider(db.Model):
    __tablename__ = 'ai_providers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(80), unique=True, nullable=False)
    api_endpoint = db.Column(db.String(255), nullable=False)
    auth_type = db.Column(db.String(20), nullable=False)  # api_key, oauth, etc.
    competencies = db.Column(db.Text, nullable=False)  # JSON string of competencies
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    accounts = db.relationship('ProviderAccount', backref='provider', lazy=True)
    
    def __repr__(self):
        return f'<AIProvider {self.name}>'
    
    def get_competencies(self):
        return json.loads(self.competencies)
    
    def set_competencies(self, competencies_dict):
        self.competencies = json.dumps(competencies_dict)


class ProviderAccount(db.Model):
    __tablename__ = 'provider_accounts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = db.Column(db.String(36), db.ForeignKey('ai_providers.id'), nullable=False)
    account_name = db.Column(db.String(80), nullable=False)
    auth_credentials = db.Column(db.Text, nullable=False)  # Encrypted credentials
    token_limit = db.Column(db.Integer, nullable=False, default=0)
    token_used = db.Column(db.Integer, nullable=False, default=0)
    reset_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    task_assignments = db.relationship('TaskAssignment', backref='account', lazy=True)
    
    def __repr__(self):
        return f'<ProviderAccount {self.account_name}>'
    
    def tokens_available(self):
        return self.token_limit - self.token_used
