import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# Flask app context for db operations
# Similar to worker.py, we need a way to get the app context.
# We'll assume main.py creates the app and db, and we can import them.
# This setup is for when scheduler is run alongside the Flask app.

# --- Flask App Context Setup ---
from flask import Flask
# Assuming db is initialized in user.py and app in main.py
# This might need adjustment based on your actual app structure.
# If main.py is where app is created:
from main import app as flask_app
from user import db
from ai_provider import ProviderAccount # Model for ProviderAccount
# --- End Flask App Context Setup ---


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - Scheduler - %(message)s')

scheduler = BackgroundScheduler(daemon=True)

def scheduled_token_reset():
    """
    Job to automatically reset token usage for provider accounts.
    This function needs to run within a Flask application context.
    """
    with flask_app.app_context():
        logging.info("Running scheduled token reset job...")
        now = datetime.utcnow()
        accounts_to_reset = ProviderAccount.query.filter(
            ProviderAccount.reset_date <= now,
            ProviderAccount.token_used > 0
        ).all()

        if not accounts_to_reset:
            logging.info("No accounts require token reset at this time.")
            return

        reset_count = 0
        for account in accounts_to_reset:
            try:
                logging.info(f"Resetting tokens for account: {account.account_name} (ID: {account.id})")
                account.token_used = 0

                # Calculate next reset date (e.g., 30 days from the current reset_date)
                # This ensures that if a reset_date was in the past, the next one is relative to that,
                # not `now`, to maintain the original billing cycle day if possible.
                if account.reset_date:
                if account.reset_date:
                    # Add 30 days to the last reset_date to maintain the cycle.
                    next_reset_candidate = account.reset_date + timedelta(days=30)
                    # If the last reset_date was significantly in the past,
                    # ensure the next one is in the future.
                    while next_reset_candidate <= now:
                        next_reset_candidate += timedelta(days=30)
                    account.reset_date = next_reset_candidate
                else:
                    # If reset_date was null, set it 30 days from now.
                    account.reset_date = now + timedelta(days=30)

                logging.info(f"Account {account.id} tokens reset. Next reset date: {account.reset_date.isoformat() if account.reset_date else 'N/A'}")
                reset_count += 1
            except Exception as e:
                logging.error(f"Error resetting tokens for account {account.id}: {e}", exc_info=True)

        if reset_count > 0:
            try:
                db.session.commit()
                logging.info(f"Successfully reset tokens for {reset_count} accounts.")
            except Exception as e:
                db.session.rollback()
                logging.error(f"Failed to commit database changes after token reset: {e}", exc_info=True)
        else:
            logging.info("No accounts were actually reset in this run (possibly due to errors).")

# Schedule the job
# For example, run daily at 2:00 AM UTC
scheduler.add_job(scheduled_token_reset, trigger='cron', hour=2, minute=0, timezone='UTC')

# It's good practice to have a way to gracefully shut down the scheduler
def shutdown_scheduler():
    if scheduler.running:
        logging.info("Shutting down scheduler...")
        scheduler.shutdown()

# Example: If you were to run this file directly for testing the scheduler part
if __name__ == '__main__':
    # This part is for testing the scheduler independently and won't run when imported.
    # For the Flask app, scheduler.start() will be called in main.py.
    logging.info("Starting scheduler independently for testing...")
    scheduler.start()
    try:
        # Keep the main thread alive to allow the scheduler to run in the background
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        shutdown_scheduler()
