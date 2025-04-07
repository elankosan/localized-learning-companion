# backend/main.py (Updated to serve frontend)
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
# Import the API router
from .api import routes

# --- Define Paths ---
# Get the directory where main.py is located (backend/)
CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (one level up from backend/)
PROJECT_ROOT = os.path.dirname(CURRENT_SCRIPT_DIR)
# Define the path to the index.html file within the frontend directory
INDEX_HTML_PATH = os.path.join(PROJECT_ROOT, "frontend", "index.html")
# --- END DEFINE PATHS ---

# Create the FastAPI app instance
app = FastAPI(title="Localized Learning Companion MVP - Backend")

# --- CORS Middleware ---
# Allows the frontend served potentially on a different origin (like IDX preview URL)
# to make requests to this backend API. '*' is permissive for development.
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all standard methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)
# --- End CORS Middleware ---

# Include the API router from api/routes.py
# All routes defined in there will be prefixed with /api
app.include_router(routes.router)

# --- Root route to serve the frontend ---
@app.get("/")
async def serve_index():
    """Serves the index.html file when the root URL is accessed."""
    # Check if the index.html file exists at the calculated path
    if not os.path.exists(INDEX_HTML_PATH):
        print(f"ERROR: index.html not found at expected path: {INDEX_HTML_PATH}")
        # Return a simple error message if the file is missing
        return {"error": "Frontend not found."}
    # Return the index.html file as a response
    return FileResponse(INDEX_HTML_PATH)
# --- END NEW ROOT ROUTE ---

# Example of how you might serve other static files (CSS, JS) if needed later:
# from fastapi.staticfiles import StaticFiles
# FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
# app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
# Then link to them in index.html like <link rel="stylesheet" href="/static/styles.css">

