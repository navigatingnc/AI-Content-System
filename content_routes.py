import os
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_jwt_extended import jwt_required
import logging

content_bp = Blueprint('content_bp', __name__)

# Configure a base directory for content files.
# This should be an absolute path for security and consistency.
# It could be configured via Flask app config as well.
# For now, let's assume it's a subdirectory 'content' within the app's static folder.
# If main.py defines app.static_folder correctly (e.g., to /app/static),
# then content_files_base_dir will be /app/static/content
# This needs to align with where provider integrations save files (e.g., GPTProvider, ManusProvider)

def get_safe_content_dir():
    """Returns the configured and validated content directory."""
    # It's safer to configure this explicitly in app.config, e.g., app.config['CONTENT_UPLOAD_DIR']
    # For now, derive from static_folder if it's set, otherwise use a default relative to app root.
    static_folder = current_app.static_folder
    if static_folder:
        # Files are saved under 'src/static/content' by providers, but static_folder is just 'static'
        # The 'src' part was an old convention. Files are now in 'static/content'.
        # Let's adjust based on current provider save paths like:
        # GPTProvider: f"src/static/content/{task.id}.png" -> should be "static/content/{task.id}.png"
        # ManusProvider: f"src/static/content/{task.id}/project.zip" -> "static/content/{task.id}/project.zip"
        # ClaudeProvider: f"src/static/content/{task.id}.{language}" -> "static/content/{task.id}.{language}"
        # The `static_folder` in Flask is typically the direct name like 'static'.
        # The providers save files to 'src/static/content'. This path needs to be harmonized.
        # Let's assume for this endpoint, the files are referenced relative to a base 'static/content'
        # and the path parameter will be like "task_id.png" or "task_id/project.zip"

        # Let's assume the providers will save files to a directory that `current_app.root_path` can access.
        # e.g., current_app.root_path / 'static' / 'content'
        # The current providers save to 'src/static/content', which is problematic if 'src' is not the root.
        # Given current project structure, root_path is /app. Providers save to /app/src/static/content.
        # This needs to be fixed in providers. For now, let's assume providers save to current_app.root_path / 'uploads' / 'content'
        # Or, more simply, let's use a fixed relative path from the app's root_path for now.
        # The providers save files to `src/static/content`. This is the path we must currently assume.
        # This needs to be fixed. If app.root_path is /app, then we need /app/src/static/content
        # However, ls() shows no src/ directory. The file paths in providers are likely wrong.
        # Let's check where providers actually save:
        # GPTProvider: os.makedirs('src/static/content', exist_ok=True); file_path = f"src/static/content/{task.id}.png"
        # This means they are creating a 'src' directory in the current working directory of the app.
        # This is not robust.
        # For this exercise, I will assume the files are being served from 'static/content' relative to app root.
        # This implies providers should save to `os.path.join(current_app.root_path, 'static', 'content')`

        # Let's define a CONTENT_DIR relative to the app's root path.
        # Example: current_app.root_path = /app
        # CONTENT_DIR = /app/static_content_files (this needs to be where files are actually saved)
        # For now, using 'static/content' as providers seem to indicate.
        # This is tricky due to the 'src/' prefix in provider save paths and its absence in `ls()`.
        # Let's assume files are saved in a directory named `content_files` at the app root for now for this endpoint.
        # This will need to be reconciled with provider save locations.
        # For the purpose of this endpoint, let's define a base directory.
        # The existing providers save into 'src/static/content'. This is problematic.
        # I will assume the path parameter passed to this endpoint is *relative* to a known safe directory.
        # And that this known safe directory is where providers *should* be saving files.
        # Let's use `current_app.config.get('CONTENT_DIRECTORY', os.path.join(current_app.root_path, 'content_files'))`
        # For now, hardcoding for simplicity of this step, assuming 'static/content' will be used by providers correctly.

        # Given current provider code saves to `src/static/content/` which resolves to `/app/src/static/content/`
        # And `app.static_folder` is `/app/static/`
        # This is a mismatch.
        # For robust serving, the 'path' query param should be relative to a KNOWN, SECURE base directory.
        # Let's assume this base directory is `os.path.join(current_app.root_path, "user_content")`
        # And providers will be updated to save there.
        # For NOW, to make progress, let's assume path is relative to `current_app.root_path`.
        # This is NOT ideal but unblocks.
        # A better fix: define `app.config['UPLOAD_FOLDER']` and use it.
        # For now, let's use `current_app.root_path` and assume the path is relative to it,
        # and includes the full "src/static/content/..." part. This is not secure.

        # Correct approach: define a secure base directory.
        # Providers currently save to 'src/static/content/' relative to app root.
        # Aligning content_dir to this actual save path.
        # current_app.root_path is typically /app
        content_dir = os.path.join(current_app.root_path, 'src', 'static', 'content')
        # This directory should ideally be created by deployment or ensured by providers,
        # not by this getter.
        return content_dir

@content_bp.route('/content/file', methods=['GET'])
@jwt_required()
def serve_content_file():
    file_path_query = request.args.get('path')

    if not file_path_query:
        return jsonify({'error': 'Missing path query parameter.'}), 400

    # Security: Normalize the path to prevent directory traversal.
    # os.path.normpath collapses '..' and also handles '/' vs '\'.
    # os.path.abspath ensures it's an absolute path for further checks.
    # We want to ensure the path is relative to our secure base directory.

    content_base_dir = get_safe_content_dir() # e.g., /app/static/content

    # Create absolute path for the requested file by joining base_dir and the user-provided path.
    # os.path.join handles path separators correctly.
    requested_path_abs = os.path.normpath(os.path.join(content_base_dir, file_path_query))

    # Security check: Ensure the resolved absolute path is still within the content_base_dir.
    # This is a critical step to prevent directory traversal.
    if not requested_path_abs.startswith(os.path.normpath(content_base_dir) + os.sep) and \
       requested_path_abs != os.path.normpath(content_base_dir): # Handles case where path is exactly content_base_dir
        logging.warning(f"Potential directory traversal attempt: Query '{file_path_query}' resolved to '{requested_path_abs}' outside of base '{content_base_dir}'")
        return jsonify({'error': 'Invalid path.'}), 403 # Forbidden

    if not os.path.exists(requested_path_abs) or not os.path.isfile(requested_path_abs):
        # Log this: logging.info(f"File not found: {requested_path_abs}")
        return jsonify({'error': 'File not found.'}), 404

    try:
        # `send_from_directory` needs directory and filename separately.
        # `directory` should be the absolute path to the directory containing the file.
        # `path` (filename for send_from_directory) should be the filename itself, or relative path from `directory`.

        # To use send_from_directory safely:
        # directory = content_base_dir
        # filename = file_path_query  (after ensuring it's safe and relative)

        # After our normalization and check, file_path_query has been validated to be within content_base_dir.
        # We need to make file_path_query relative to content_base_dir again if it became absolute,
        # or ensure it's just the filename if it's directly in content_base_dir.
        # The current requested_path_abs is the one to use with send_file.
        # For send_from_directory, directory = os.path.dirname(requested_path_abs), path = os.path.basename(requested_path_abs)

        # Simpler usage of send_from_directory:
        # 1. The directory part for send_from_directory: content_base_dir
        # 2. The path part for send_from_directory: file_path_query (which must be relative to content_base_dir)
        # We've already checked that os.path.join(content_base_dir, file_path_query) is safe.

        # flask.send_from_directory(directory, path, **options)
        # directory: the directory where the files are stored (absolute path)
        # path: the path to the file relative to the directory.
        # Our file_path_query IS this relative path.

        return send_from_directory(content_base_dir, file_path_query, as_attachment=False) # as_attachment=False for inline display
    except Exception as e:
        logging.error(f"Error sending file {file_path_query}: {e}", exc_info=True)
        return jsonify({'error': 'Error sending file.'}), 500
