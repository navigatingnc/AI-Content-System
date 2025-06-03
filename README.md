# AI Content Generation System

This project is an AI Content Generation System.

## Development Setup

### Prerequisites

- Git
- Python 3.8+
- Node.js and pnpm

### Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Set up a Python virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install backend dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install frontend dependencies:**
    Since `pnpm-lock.yaml` is present, use pnpm:
    ```bash
    pnpm install
    ```

5.  **Run the backend:**
    The backend is a Flask application.
    ```bash
    flask run
    ```
    By default, it will run on `http://127.0.0.1:5000`.

6.  **Run the frontend:**
    The frontend is a Vite React application.
    ```bash
    pnpm start
    ```
    This will typically start the development server on `http://localhost:5173`.

### Running the Application

-   Access the frontend at the URL provided by the `pnpm start` command.
-   The frontend will interact with the backend API running on port 5000.

7.  **Run the Worker Process:**
    The worker process is responsible for picking up tasks from the queue and processing them.
    Open a new terminal, activate the virtual environment, and run:
    ```bash
    python worker.py
    ```
    The worker will log its activity to the console. Ensure Redis is running and accessible by the worker (configure `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` environment variables if not using defaults).

## Environment Variables

The application uses several environment variables for configuration:

-   **`FERNET_KEY`**: A secret key used for encrypting and decrypting provider credentials.
    -   **SECURITY WARNING**: This key **MUST** be changed from any default value and kept secret in a production environment. It should be a URL-safe base64-encoded 32-byte key. You can generate one using Python:
        ```python
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        print(key.decode())
        ```
    -   Store this key securely (e.g., in your deployment environment's secret management). Failure to do so can lead to exposure of sensitive provider API keys.
-   **`REDIS_HOST`**: Hostname for the Redis server (default: `localhost`).
-   **`REDIS_PORT`**: Port for the Redis server (default: `6379`).
-   **`REDIS_DB`**: Redis database number (default: `0`).
-   **`OPENAI_API_URL`** (Optional): Overrides the default API endpoint for OpenAI (e.g., for proxies or specific versions).
-   **`MANUS_API_URL`** (Optional): Overrides the default API endpoint for Manus.ai.
-   **`CLAUDE_API_URL`** (Optional): Overrides the default API endpoint for Anthropic Claude.

You can set these environment variables in your shell, using a `.env` file (if your setup supports it, e.g., with `python-dotenv`), or through your deployment platform's configuration.

## Automated Jobs

-   **Token Reset:** Provider account token usage (`token_used`) is automatically reset daily by a scheduled job. The next `reset_date` for each account is also updated. This job runs at 02:00 UTC.

## Main Technologies Used

### Backend
- Python, Flask
- Flask-SQLAlchemy (for database interaction)
- Flask-JWT-Extended (for authentication)
- Redis (for task queue)
- Werkzeug (WSGI utility)
- Cryptography (for encrypting credentials)
- APScheduler (for scheduled jobs like token reset)

### Frontend
- React (with Vite)
- TypeScript
- pnpm (package manager)
```
