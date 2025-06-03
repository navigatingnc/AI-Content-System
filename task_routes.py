from flask import Blueprint, request, jsonify
from user import db # Assuming db is initialized in user.py and accessible
from task import Task
from task_queue import TaskQueue # Assuming TaskQueue is in task_queue.py
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity # For user_id

task_bp = Blueprint('task_bp', __name__)

@task_bp.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    data = request.get_json()
    user_id = get_jwt_identity()

    if not data or not all(k in data for k in ['title', 'task_type']):
        return jsonify({'error': 'Missing required fields: title, task_type'}), 400

    title = data['title']
    task_type = data['task_type']
    description = data.get('description')
    priority = data.get('priority', 1) # Default priority

    try:
        priority = int(priority)
        if not 1 <= priority <= 5:
            raise ValueError("Priority out of range")
    except ValueError:
        return jsonify({'error': 'Invalid priority value. Must be an integer between 1 and 5.'}), 400

    new_task = Task(
        user_id=user_id,
        title=title,
        description=description,
        task_type=task_type,
        priority=priority,
        status='pending',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    try:
        db.session.add(new_task)
        db.session.commit()

        # Enqueue the task
        # The TaskQueue.enqueue_task expects task_id, not the object
        TaskQueue.enqueue_task(task_id=new_task.id, priority=new_task.priority)

        return jsonify({'message': 'Task created successfully', 'task_id': new_task.id}), 201
    except Exception as e:
        db.session.rollback()
        # Log the exception e
        return jsonify({'error': f'Failed to create task: {str(e)}'}), 500

@task_bp.route('/tasks/<string:task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    # user_id = get_jwt_identity() # Potentially use to ensure user can only access their tasks

    task = Task.query.get(task_id)

    if not task:
        return jsonify({'error': 'Task not found'}), 404

    # Optional: Check if the user is authorized to view this task
    # if task.user_id != user_id:
    #     return jsonify({'error': 'Unauthorized to view this task'}), 403

    # Also include assignments and content items in the response
    # This matches the TaskDetail interface expected by the frontend
    assignments_data = []
    for assignment in task.assignments:
        # Basic assignment data; provider_name might need to be fetched if not directly on assignment model
        # Assuming TaskAssignment has a `provider` relationship that has a `name`
        provider_name = assignment.provider.name if assignment.provider else "Unknown Provider"
        assignments_data.append({
            'id': assignment.id,
            'provider_id': assignment.provider_id,
            'provider_name': provider_name, # Make sure provider relationship is loaded
            'status': assignment.status,
            'tokens_used': assignment.tokens_used,
            'created_at': assignment.created_at.isoformat() if assignment.created_at else None,
            'updated_at': assignment.updated_at.isoformat() if assignment.updated_at else None,
            # Add other relevant TaskAssignment fields if needed by frontend
        })

    content_items_data = [item.to_dict() for item in task.content_items]

    response_data = {
        'task': task.to_dict(),
        'assignments': assignments_data,
        'content': content_items_data
    }

    return jsonify(response_data), 200
