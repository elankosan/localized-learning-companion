from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Import CORS middleware
from .api import routes # Import the router from api/routes.py

# Create the FastAPI app instance
app = FastAPI(title="Localized Learning Companion MVP - Backend")

# --- CORS Middleware ---
# This allows your frontend (which might be served from a different origin/port)
# to communicate with this backend.
# '*' allows all origins, which is fine for local development.
# For production, you'd restrict this to your frontend's actual domain.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)
# --- End CORS Middleware ---


# Include the API router
# All routes defined in api.routes will be available under /api prefix
#app.include_router(routes.router)

# Simple root endpoint to check if the server is running
@app.get("/")
def read_root():
    return {"message": "Welcome to the Localized Learning Companion Backend!"}