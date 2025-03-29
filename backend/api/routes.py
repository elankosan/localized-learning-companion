from fastapi import APIRouter, HTTPException
from .models import QueryRequest, AnswerResponse
from .services import mock_get_answer

# Create an API router
# All routes defined here will be prefixed with /api
router = APIRouter(prefix="/api")

@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QueryRequest):
    """
    Receives a question, processes it (mocked), and returns an answer.
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        # Get the mock answer using the service function
        answer_text = mock_get_answer(request.query)
        return AnswerResponse(answer=answer_text)
    except Exception as e:
        # Basic error handling
        print(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error processing the query")