from flask import Blueprint, request, jsonify
from ai_provider import AIProvider, ProviderAccount
from ai_provider_integration import AIProviderFactory
from flask_jwt_extended import jwt_required, get_jwt_identity
from user import db, User
import json
from datetime import datetime, timedelta
import base64 # Added for encoding encrypted credentials
from utils.security import encrypt_data # Added for credential encryption

provider_bp = Blueprint('provider', __name__)

@provider_bp.route('/providers', methods=['GET'])
@jwt_required()
def get_providers():
    """Get all AI providers"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Only admin users can view all providers
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    providers = AIProvider.query.all()
    
    result = []
    for provider in providers:
        accounts = ProviderAccount.query.filter_by(provider_id=provider.id).all()
        
        result.append({
            'id': provider.id,
            'name': provider.name,
            'api_endpoint': provider.api_endpoint,
            'auth_type': provider.auth_type,
            'competencies': provider.get_competencies(),
            'status': provider.status,
            'accounts': [{
                'id': account.id,
                'account_name': account.account_name,
                'token_limit': account.token_limit,
                'token_used': account.token_used,
                'reset_date': account.reset_date.isoformat() if account.reset_date else None,
                'status': account.status
            } for account in accounts]
        })
    
    return jsonify({'providers': result}), 200

@provider_bp.route('/providers/<provider_id>', methods=['GET'])
@jwt_required()
def get_provider(provider_id):
    """Get a specific AI provider"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Only admin users can view provider details
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    provider = AIProvider.query.get(provider_id)
    if not provider:
        return jsonify({'error': 'Provider not found'}), 404
    
    accounts = ProviderAccount.query.filter_by(provider_id=provider_id).all()
    
    return jsonify({
        'id': provider.id,
        'name': provider.name,
        'api_endpoint': provider.api_endpoint,
        'auth_type': provider.auth_type,
        'competencies': provider.get_competencies(),
        'status': provider.status,
        'accounts': [{
            'id': account.id,
            'account_name': account.account_name,
            'token_limit': account.token_limit,
            'token_used': account.token_used,
            'reset_date': account.reset_date.isoformat() if account.reset_date else None,
            'status': account.status
        } for account in accounts]
    }), 200

@provider_bp.route('/providers/<provider_id>/status', methods=['GET'])
@jwt_required()
def get_provider_status(provider_id):
    """Get provider status including token availability"""
    provider = AIProvider.query.get(provider_id)
    if not provider:
        return jsonify({'error': 'Provider not found'}), 404
    
    accounts = ProviderAccount.query.filter_by(provider_id=provider_id).all()
    
    return jsonify({
        'id': provider.id,
        'name': provider.name,
        'status': provider.status,
        'accounts': [{
            'id': account.id,
            'account_name': account.account_name,
            'token_limit': account.token_limit,
            'token_used': account.token_used,
            'available_tokens': account.token_limit - account.token_used,
            'reset_date': account.reset_date.isoformat() if account.reset_date else None,
            'status': account.status
        } for account in accounts]
    }), 200

@provider_bp.route('/providers/<provider_id>/test', methods=['POST'])
@jwt_required()
def test_provider(provider_id):
    """Test connection to a provider"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Only admin users can test providers
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    account_id = data.get('account_id')
    
    if not account_id:
        return jsonify({'error': 'Account ID is required'}), 400
    
    provider = AIProvider.query.get(provider_id)
    if not provider:
        return jsonify({'error': 'Provider not found'}), 404
    
    account = ProviderAccount.query.get(account_id)
    if not account or account.provider_id != provider_id:
        return jsonify({'error': 'Account not found or does not belong to this provider'}), 404
    
    # Get provider instance
    provider_instance = AIProviderFactory.get_provider(provider.name)
    if not provider_instance:
        return jsonify({'error': 'Provider not implemented'}), 400
    
    # Test authentication
    # Pass the provider model instance for API URL configuration
    success, error = provider_instance.authenticate(account.auth_credentials, provider_model_instance=provider)
    
    if not success:
        return jsonify({
            'success': False,
            'message': error
        }), 200
    
    return jsonify({
        'success': True,
        'message': 'Connection successful'
    }), 200

@provider_bp.route('/providers/<provider_id>/accounts', methods=['POST'])
@jwt_required()
def add_account(provider_id):
    """Add a new account for a provider"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Only admin users can add accounts
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    provider = AIProvider.query.get(provider_id)
    if not provider:
        return jsonify({'error': 'Provider not found'}), 404
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['account_name', 'auth_credentials', 'token_limit']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    raw_credentials = data['auth_credentials']
    try:
        encrypted_credentials_bytes = encrypt_data(raw_credentials)
        # Fernet output is already URL-safe base64 encoded bytes.
        # For storing in text column, decode to utf-8.
        encrypted_credentials_str = encrypted_credentials_bytes.decode('utf-8')
    except Exception as e:
        # In a real app, log this error: logging.error(f"Credential encryption failed: {e}")
        return jsonify({'error': 'Failed to secure credentials due to encryption error.'}), 500
    
    # Create new account
    account = ProviderAccount(
        provider_id=provider_id,
        account_name=data['account_name'],
        auth_credentials=encrypted_credentials_str, # Store encrypted string
        token_limit=data['token_limit'],
        token_used=0,
        reset_date=data.get('reset_date'),
        status='active'
    )
    
    db.session.add(account)
    db.session.commit()
    
    return jsonify({
        'message': 'Account added successfully',
        'account': {
            'id': account.id,
            'account_name': account.account_name,
            'token_limit': account.token_limit,
            'token_used': account.token_used,
            'reset_date': account.reset_date.isoformat() if account.reset_date else None,
            'status': account.status
        }
    }), 201

@provider_bp.route('/accounts/<account_id>/status', methods=['PUT'])
@jwt_required()
def update_account_status(account_id):
    """Update account status (active/inactive)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Only admin users can update account status
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    account = ProviderAccount.query.get(account_id)
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    data = request.get_json()
    if 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
    
    if data['status'] not in ['active', 'inactive']:
        return jsonify({'error': 'Invalid status value'}), 400
    
    account.status = data['status']
    db.session.commit()
    
    return jsonify({
        'message': 'Account status updated successfully',
        'account': {
            'id': account.id,
            'account_name': account.account_name,
            'status': account.status
        }
    }), 200

@provider_bp.route('/accounts/<account_id>/tokens', methods=['PUT'])
@jwt_required()
def update_token_usage(account_id):
    """Update token usage for an account"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Only admin users can update token usage
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    account = ProviderAccount.query.get(account_id)
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    data = request.get_json()
    if 'tokens_used' not in data:
        return jsonify({'error': 'Tokens used is required'}), 400
    
    tokens_used = data['tokens_used']
    if not isinstance(tokens_used, int) or tokens_used < 0:
        return jsonify({'error': 'Tokens used must be a non-negative integer'}), 400
    
    account.token_used += tokens_used
    db.session.commit()
    
    return jsonify({
        'message': 'Token usage updated successfully',
        'account': {
            'id': account.id,
            'account_name': account.account_name,
            'token_limit': account.token_limit,
            'token_used': account.token_used,
            'available_tokens': account.token_limit - account.token_used
        }
    }), 200

@provider_bp.route('/tokens/reset', methods=['POST'])
@jwt_required()
def reset_expired_tokens():
    """Reset token usage for accounts that have reached their reset date"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Only admin users can reset tokens
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Find accounts with reset dates in the past
    now = datetime.utcnow()
    accounts = ProviderAccount.query.filter(
        ProviderAccount.reset_date <= now,
        ProviderAccount.token_used > 0
    ).all()
    
    reset_accounts = []
    for account in accounts:
        # Reset token usage
        account.token_used = 0
        
        # Set next reset date (typically one month later)
        if account.reset_date:
            # Calculate next month
            next_month = account.reset_date + timedelta(days=30)
            account.reset_date = next_month
        
        reset_accounts.append({
            'id': account.id,
            'account_name': account.account_name,
            'provider_id': account.provider_id,
            'next_reset': account.reset_date.isoformat() if account.reset_date else None
        })
    
    db.session.commit()
    
    return jsonify({
        'message': 'Token usage reset successfully',
        'reset_count': len(reset_accounts),
        'accounts': reset_accounts
    }), 200

@provider_bp.route('/providers/fallback', methods=['GET'])
@jwt_required()
def get_fallback_providers():
    """Get fallback providers for a task type when primary provider is unavailable"""
    task_type = request.args.get('task_type')
    primary_provider_id = request.args.get('primary_provider_id')
    
    if not task_type or not primary_provider_id:
        return jsonify({'error': 'Task type and primary provider ID are required'}), 400
    
    # Get all active providers except the primary one
    providers = AIProvider.query.filter(
        AIProvider.id != primary_provider_id,
        AIProvider.status == 'active'
    ).all()
    
    result = []
    for provider in providers:
        competencies = provider.get_competencies()
        
        # Check if provider has competency for this task type
        if task_type in competencies:
            # Get active accounts with available tokens
            accounts = ProviderAccount.query.filter_by(
                provider_id=provider.id,
                status='active'
            ).all()
            
            available_account = None
            for account in accounts:
                if account.token_limit > account.token_used:
                    available_account = account
                    break
            
            result.append({
                'id': provider.id,
                'name': provider.name,
                'competency_score': competencies.get(task_type, 0),
                'has_available_tokens': available_account is not None,
                'available_account_id': available_account.id if available_account else None
            })
    
    # Sort by competency score (higher is better)
    result.sort(key=lambda x: x['competency_score'], reverse=True)
    
    return jsonify({
        'providers': result
    }), 200
