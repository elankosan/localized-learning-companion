# backend/api/models.py
from pydantic import BaseModel

class QueryRequest(BaseModel):  # Ensure this class name is exact
    query: str

class AnswerResponse(BaseModel):
    answer: str
    # In the future, we could add sources here, e.g.:
    # sources: list[str] = []