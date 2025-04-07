# run_backend.py
# Simple script to run the FastAPI backend server using Uvicorn.
# Assumes this script is in the project root directory,
# and the FastAPI app instance is named 'app' in 'backend/main.py'.

import uvicorn
import os

if __name__ == "__main__":
    # Get the directory where this script is located (project root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Define the directory containing the backend code relative to the script dir
    backend_dir = os.path.join(script_dir, 'backend')

    print("Starting Uvicorn server...")
    print("Watching for changes in:", backend_dir)
    print("Access API docs at http://127.0.0.1:8000/docs")
    print("Access Frontend at http://127.0.0.1:8000/")

    # Run the Uvicorn server
    uvicorn.run(
        "backend.main:app",   # Path to the FastAPI app instance (module.module:variable)
        host="127.0.0.1",     # Bind to localhost
        port=8000,            # Standard port for development
        reload=True,          # Enable auto-reload when code changes
        reload_dirs=[backend_dir] # Specify directory to watch for changes
    )
