import os
from flask import Flask, send_from_directory
from user import db  # Assuming db is defined in user.py
from provider import provider_bp
from task_routes import task_bp
from content_routes import content_bp # Import the new content blueprint

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

app.register_blueprint(provider_bp, url_prefix='/api')
app.register_blueprint(task_bp, url_prefix='/api')
app.register_blueprint(content_bp, url_prefix='/api') # Register content_bp

# uncomment if you need to use database
# app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db.init_app(app)
# with app.app_context():
#     db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

# Scheduler integration
from scheduler import scheduler, shutdown_scheduler
import atexit

if __name__ == '__main__':
    # Start the scheduler only once, not in reloader subprocesses.
    # The `WERKZEUG_RUN_MAIN` env var is set by Werkzeug in the main process.
    # In debug mode, app.run() spawns a reloader process.
    # We want the scheduler to run in the main process that Werkzeug manages.
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        if not scheduler.running:
            scheduler.start()
            # Register a function to shut down the scheduler when the app exits
            atexit.register(shutdown_scheduler)
            app.logger.info("APScheduler started.")
        else:
            app.logger.info("APScheduler already running.")
    else:
        if scheduler.running: # If running in a child process, stop it.
            shutdown_scheduler()
            app.logger.info("APScheduler shut down in child process.")


    app.run(host='0.0.0.0', port=5000, debug=True)
