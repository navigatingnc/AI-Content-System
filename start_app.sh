#!/bin/bash

# This script builds the frontend and starts the backend server
# for the AI Content Generation System.

echo "Starting AI Content Generation System..."

# --- Python Backend Setup ---
echo "Setting up Python backend..."

# Check for virtual environment
if [ ! -d "venv" ]; then
  echo "Python virtual environment 'venv' not found."
  echo "Please create it first: "
  echo "  python3 -m venv venv"
  echo "Then activate it and install backend dependencies (if any, e.g., from requirements.txt):"
  echo "  source venv/bin/activate"
  echo "  pip install -r requirements.txt  # If you have a requirements.txt"
  # (Note: The current project doesn't explicitly list a requirements.txt,
  # but Flask is used in main.py. Users might need to install Flask in their venv)
  echo "Ensure Flask is installed in your venv: pip install Flask"
  exit 1
fi

# Activate virtual environment
source venv/bin/activate
echo "Python virtual environment activated."

# --- Frontend Build ---
echo "Building frontend assets..."

# Check for pnpm and node_modules
if ! command -v pnpm &> /dev/null && [ ! -d "node_modules" ]; then
    echo "pnpm command could not be found and node_modules directory doesn't exist."
    echo "Please install pnpm and then run 'pnpm install' to install frontend dependencies."
    echo "Installation instructions for pnpm can be found at https://pnpm.io/installation"
    exit 1
elif [ ! -d "node_modules" ]; then
    echo "node_modules directory doesn't exist. Frontend dependencies are likely not installed."
    echo "Please run 'pnpm install' first."
    exit 1
elif ! command -v pnpm &> /dev/null; then
     echo "pnpm command could not be found, but node_modules exists."
     echo "Attempting to run build with 'npx pnpm run build', but installing pnpm globally is recommended."
     if ! npx pnpm run build; then
        echo "Frontend build failed with npx pnpm run build."
        echo "Please ensure pnpm is installed and 'pnpm run build' works, or check Vite logs."
        exit 1
     fi
else
    if ! pnpm run build; then
      echo "Frontend build failed. Check Vite logs for errors."
      exit 1
    fi
fi

echo "Frontend build successful. Assets are in the 'static' directory."

# --- Start Backend Server ---
echo "Starting Python Flask backend server..."
echo "Access the application through your browser (typically http://localhost:3000 if Vite proxies, or directly via Flask's port if Vite dev server isn't used for access)"
echo "Flask server will run on http://localhost:5000 (unless configured otherwise in main.py)"

python main.py

# Deactivate virtual environment when script exits (optional, usually handled by shell)
# deactivate
echo "Backend server stopped."
