# backend/api/services.py
import time

# Mock function to simulate getting an answer
def mock_get_answer(query: str) -> str:  # Ensure this function name and definition is exact
    """
    Simulates processing a query and returning a mock answer in Tamil.
    """
    print(f"Received query (mock processing): {query}")
    # Simulate some processing time
    time.sleep(0.5)

    # --- Hardcoded Mock Tamil Response ---
    # You can change this text if you like
    mock_answer = f"இது உங்கள் கேள்விக்கான மாதிரி பதில்: '{query}'. உண்மையான பதில் பின்னர் செயல்படுத்தப்படும்."
    # Translation: "This is a sample answer for your query: '{query}'. The real answer will be implemented later."
    # ---

    print(f"Returning mock answer: {mock_answer}")
    return mock_answer