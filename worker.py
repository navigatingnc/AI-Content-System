import time
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Flask App Context Setup ---
# This is crucial for the worker to interact with Flask-SQLAlchemy models
# and the database session correctly.
# It needs to be done before importing db, models, or app-dependent modules.

# Option 1: Create a minimal Flask app instance for the worker context
from flask import Flask
from user import db # Import db from your user.py or equivalent
from main import app as main_app # Import the main app for its config

app = Flask(__name__)
app.config.from_object(main_app.config) # Copy config from main app

# Initialize extensions that worker needs, if not already handled by app config copy
# For SQLAlchemy, it's typically db.init_app(app) if not done in user.py
# However, if user.py defines db = SQLAlchemy() without app, it might be picked up by app.app_context()
# Let's ensure db is associated with our worker's app instance if it wasn't already by main_app import
if not hasattr(db, 'app'): # A simple check, might need more robust one
    db.init_app(app)

# --- End Flask App Context Setup ---

from task_queue import TaskQueue, TaskPrioritizer
from task import Task, TaskAssignment # Import your Task and TaskAssignment models
from ai_provider_integration import AIProviderFactory # For getting provider instance

MAX_ATTEMPTS = 3

def process_task(task_id): # app_context argument removed
    """
    Processes a single task:
    - Fetches task from DB.
    - Assigns provider and account.
    - Simulates execution.
    - Updates status and handles retries.
    """
    # This function assumes it's called within an active Flask app context
    task = Task.query.get(task_id)

    if not task:
            logging.warning(f"Task ID {task_id} not found in database. Skipping.")
            return

        if task.status not in ['pending', 'queued_for_retry']: # Avoid reprocessing completed/failed tasks unless specifically re-queued
            logging.info(f"Task {task.id} status is '{task.status}'. Skipping.")
            return

        logging.info(f"Processing task {task.id}: {task.title}")

        # 1. Assign Provider and Account
        # TaskPrioritizer.assign_task updates task status to 'processing' but doesn't commit.
        # It returns an assignment object or (None, error_message)
        assignment, error_msg = TaskPrioritizer.assign_task(task)

        if error_msg:
            logging.error(f"Could not assign provider for task {task.id}: {error_msg}")
            task.status = 'failed'
            task.error_message = error_msg
            task.updated_at = datetime.utcnow()
            db.session.commit()
            return

        if not assignment: # Should be caught by error_msg, but as a safeguard
            logging.error(f"Failed to create assignment for task {task.id}, no specific error.")
            task.status = 'failed'
            task.error_message = "Assignment creation failed without specific error."
            task.updated_at = datetime.utcnow()
            db.session.commit()
            return

        # Increment attempt count for the new assignment
        # Note: assign_task from task_queue.py does not set attempt_count.
        # We should initialize it or retrieve an existing assignment if this is a retry.
        # For simplicity, let's assume assign_task always creates a *new* assignment object
        # or we fetch the latest pending one if that's the design.
        # The current TaskPrioritizer.assign_task always creates a new one.

        # Let's find if there was a previous attempt to increment its count,
        # or if this is a brand new assignment, it starts at 1.
        # A better approach might be for assign_task to handle finding/creating assignments
        # and their attempt counts.
        # For now, we'll assume this assignment is fresh from assign_task.

        # The assignment created by TaskPrioritizer has status 'pending'
        # and attempt_count 0 by default.
        assignment.attempt_count += 1 # This is the first attempt for *this* assignment
        assignment.status = 'processing' # Update assignment status

        # Task status is already 'processing' by assign_task
        task.updated_at = datetime.utcnow()

        db.session.add(assignment)
        db.session.commit() # Commit task status change and new/updated assignment

        logging.info(f"Task {task.id} assigned to provider {assignment.provider_id}, account {assignment.account_id}. Attempt {assignment.attempt_count}.")

        # 2. Actual Task Execution using AIProviderFactory
        try:
            provider_model = assignment.provider # Assuming backref 'provider' from TaskAssignment to AIProvider model
            if not provider_model:
                raise Exception(f"AIProvider model not found for assignment {assignment.id}")

            provider_instance = AIProviderFactory.get_provider(provider_model.name)

            if not provider_instance:
                logging.error(f"Provider implementation for '{provider_model.name}' not found for task {task.id}.")
                task.status = 'failed'
                task.error_message = f"Provider implementation for '{provider_model.name}' not found."
                assignment.status = 'failed'
                assignment.error_message = f"Provider implementation '{provider_model.name}' not found in factory."
            else:
                logging.info(f"Executing task {task.id} with provider {provider_model.name} (Attempt {assignment.attempt_count})...")
                # Decryption of credentials will happen inside provider_instance.generate_content
                content_object, error = provider_instance.generate_content(task, assignment)

                if error:
                    raise Exception(f"generate_content failed: {error}")

                if content_object:
                    logging.info(f"Task {task.id} content generated successfully by {provider_model.name}.")
                    db.session.add(content_object) # Add new content to session
                    task.status = 'completed'
                    task.completed_at = datetime.utcnow()
                    assignment.status = 'completed'
                    # Token usage should be updated by the provider_instance.generate_content method
                    # and set on assignment.tokens_used
                else:
                    # This case should ideally be an error from generate_content
                    raise Exception("generate_content returned no content and no error.")

        except Exception as e:
            logging.error(f"Task {task.id} execution attempt {assignment.attempt_count} failed: {str(e)}")
            assignment.status = 'failed'
            assignment.error_message = str(e)

            if assignment.attempt_count < MAX_ATTEMPTS:
                logging.info(f"Re-enqueuing task {task.id} for retry ({assignment.attempt_count}/{MAX_ATTEMPTS}).")
                task.status = 'pending' # Set task status back to pending for re-queueing
                TaskQueue.enqueue_task(task.id, task.priority) # Re-enqueue with original priority
            else:
                logging.warning(f"Task {task.id} failed after {MAX_ATTEMPTS} attempts. Last error: {str(e)}")
                task.status = 'failed'
                task.error_message = f"Task failed after {MAX_ATTEMPTS} attempts. Last error on assignment {assignment.id}: {str(e)}"

        task.updated_at = datetime.utcnow()
        assignment.updated_at = datetime.utcnow()
        db.session.commit() # Commit all changes for this task processing cycle


def main_loop():
    logging.info("Worker started. Waiting for tasks...")
    while True:
        try:
            task_id = TaskQueue.dequeue_task()
            if task_id:
                logging.info(f"Dequeued task ID: {task_id}")
                with app.app_context(): # Create context for each task processing
                     process_task(task_id)
            else:
                # No task, wait a bit
                time.sleep(2) # Sleep longer when queue is empty
        except redis.exceptions.ConnectionError as e:
            logging.error(f"Redis connection error: {e}. Retrying in 10 seconds...")
            time.sleep(10) # Sleep longer if Redis error, before retrying connection
        except Exception as e:
            logging.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
            time.sleep(5) # Brief pause for other unexpected errors

if __name__ == '__main__':
    main_loop()
