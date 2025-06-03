import redis
import json
from datetime import datetime
import uuid
from task import Task, TaskAssignment
from ai_provider import AIProvider, ProviderAccount

import os

# Initialize Redis client
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

class TaskQueue:
    """Task queue manager using Redis"""
    
    QUEUE_KEY = 'ai_content_system:task_queue'
    
    @staticmethod
    def enqueue_task(task_id, priority=1):
        """Add a task to the queue with priority"""
        # Redis sorted sets use score for ordering (lower score = higher priority)
        # We invert priority so higher priority tasks come first
        score = 10 - priority  # Priority 5 becomes score 5, priority 1 becomes score 9
        
        # Add timestamp to ensure FIFO ordering within same priority
        timestamp = datetime.utcnow().timestamp()
        final_score = score + (timestamp / 1000000)  # Add tiny fraction for timestamp
        
        redis_client.zadd(TaskQueue.QUEUE_KEY, {task_id: final_score})
        return True
    
    @staticmethod
    def dequeue_task():
        """Get the highest priority task from the queue"""
        # Get the task with the lowest score (highest priority)
        result = redis_client.zpopmin(TaskQueue.QUEUE_KEY, 1)
        if not result:
            return None
        
        task_id = result[0][0].decode('utf-8')
        return task_id
    
    @staticmethod
    def peek_tasks(count=10):
        """View tasks in the queue without removing them"""
        tasks = redis_client.zrange(TaskQueue.QUEUE_KEY, 0, count-1, withscores=True)
        return [(task_id.decode('utf-8'), score) for task_id, score in tasks]
    
    @staticmethod
    def remove_task(task_id):
        """Remove a specific task from the queue"""
        return redis_client.zrem(TaskQueue.QUEUE_KEY, task_id)
    
    @staticmethod
    def queue_length():
        """Get the number of tasks in the queue"""
        return redis_client.zcard(TaskQueue.QUEUE_KEY)


class TaskPrioritizer:
    """Task prioritization logic"""
    
    @staticmethod
    def select_provider_for_task(task):
        """Select the best AI provider for a given task"""
        # Get all active providers
        providers = AIProvider.query.filter_by(status='active').all()
        if not providers:
            return None, "No active AI providers available"
        
        # Filter providers by competency match
        matching_providers = []
        for provider in providers:
            competencies = provider.get_competencies()
            if task.task_type in competencies:
                matching_providers.append((provider, competencies[task.task_type]))
        
        if not matching_providers:
            return None, f"No providers with competency for task type: {task.task_type}"
        
        # Sort by competency score (higher is better)
        matching_providers.sort(key=lambda x: x[1], reverse=True)
        
        # Check for available accounts with tokens
        for provider, _ in matching_providers:
            accounts = ProviderAccount.query.filter_by(
                provider_id=provider.id,
                status='active'
            ).all()
            
            available_accounts = [acc for acc in accounts if acc.tokens_available() > 0]
            if available_accounts:
                # Sort accounts by available tokens (higher is better)
                available_accounts.sort(key=lambda x: x.tokens_available(), reverse=True)
                return provider, available_accounts[0], None
        
        return None, None, "No providers with available tokens"
    
    @staticmethod
    def assign_task(task):
        """Assign a task to the best provider and account"""
        provider, account, error = TaskPrioritizer.select_provider_for_task(task)
        
        if error:
            task.status = 'failed'
            task.updated_at = datetime.utcnow()
            return None, error
        
        # Create task assignment
        assignment = TaskAssignment(
            task_id=task.id,
            provider_id=provider.id,
            account_id=account.id,
            status='pending'
        )
        
        # Update task status
        task.status = 'processing'
        task.started_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        
        return assignment, None
