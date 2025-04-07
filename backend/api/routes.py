# backend/api/routes.py
from fastapi import APIRouter, HTTPException, status
# --- Update Model Imports ---
from .models import QueryRequest, AnswerResponse, AddNoteRequest, AddNoteResponse
# --- Update Service Imports ---
from .services import get_rag_answer, add_note_to_classroom # Removed mock, added note service

# Create an API router. All routes defined here will be prefixed with /api
router = APIRouter(prefix="/api")

@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QueryRequest):
    """
    Receives a question and classroom_id, processes it using the RAG pipeline
    for the specified classroom, and returns an answer.
    """
    # Validate inputs
    if not request.query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty")
    if not request.classroom_id:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Classroom ID cannot be empty")

    try:
        # Call the RAG service function, passing both query and classroom_id
        answer_text = get_rag_answer(query=request.query, classroom_id=request.classroom_id)
        return AnswerResponse(answer=answer_text)
    except FileNotFoundError as e:
         # Handle case where the classroom DB doesn't exist
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        # Catch other potential errors from the service layer
        print(f"Error processing /api/ask route: {e}")
        # Avoid leaking internal error details to the client in production
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred while processing the question.")

# --- MVP2: New endpoint for adding notes ---
@router.post("/classrooms/{classroom_id}/notes", response_model=AddNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_note(classroom_id: str, request: AddNoteRequest):
    """
    Adds a new text note to the specified classroom.
    """
    if not request.note_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Note text cannot be empty")

    try:
        # Here you might add checks: Does classroom_id exist? User permissions? (Deferred for now)
        print(f"Received request to add note to classroom: {classroom_id}")
        note_id = add_note_to_classroom(classroom_id=classroom_id, note_text=request.note_text)
        return AddNoteResponse(
            message="Note added successfully.",
            classroom_id=classroom_id,
            note_id=note_id
        )
    except Exception as e:
        print(f"Error processing add_note route for classroom {classroom_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add note.")

# --- Optional: Endpoint to retrieve notes (for testing/debugging) ---
@router.get("/classrooms/{classroom_id}/notes", response_model=list[dict])
async def get_notes(classroom_id: str):
     """Retrieves all notes for a given classroom (from in-memory store)."""
     from .services import get_classroom_notes # Import here or globally
     notes = get_classroom_notes(classroom_id)
     return notes

