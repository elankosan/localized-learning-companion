# backend/api/services.py
import os
from dotenv import load_dotenv
import time # For simple note ID generation

# LangChain components
from langchain_google_vertexai import VertexAIEmbeddings, VertexAI # LLM
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableConfig

# --- Configuration ---
# Base directory where individual classroom DBs are stored
# Assumes this script is run from the project root (e.g., via run_backend.py)
CHROMA_DBS_ROOT = "chroma_dbs"
LLM_MODEL_NAME = "gemini-1.0-pro" # Or choose another appropriate Gemini model

# --- Simple In-Memory Storage for Notes (Replace with DB later) ---
# Dictionary to store notes per classroom { classroom_id: [list of notes] }
classroom_notes_store = {}

# --- Global Cache for Initialized Components (per classroom) ---
# { classroom_id: {"vectorstore": Chroma, "llm": VertexAI, "rag_chain": Runnable} }
initialized_components_cache = {}

def _initialize_classroom_components(classroom_id: str):
    """
    Initializes LangChain components for a specific classroom if not already cached.
    Loads vector store, LLM, and creates the RAG chain.
    """
    global initialized_components_cache

    # Check cache first
    if classroom_id in initialized_components_cache:
        # print(f"Using cached components for classroom: {classroom_id}") # Optional: for debugging cache hits
        return initialized_components_cache[classroom_id]

    print(f"Initializing RAG components for classroom: {classroom_id}...")
    load_dotenv()
    google_project_id = os.getenv("GOOGLE_PROJECT_ID")

    if not google_project_id:
        raise ValueError("GOOGLE_PROJECT_ID not found in environment variables.")

    # Define paths specific to this classroom
    vectorstore_path = os.path.join(CHROMA_DBS_ROOT, classroom_id)

    try:
        # 1. Embeddings (reuse the same model used for populating)
        # This could potentially be initialized once globally if desired
        embeddings = VertexAIEmbeddings(
            model_name="text-embedding-004",
            project=google_project_id
        )

        # 2. Load Classroom-Specific Vector Store
        if not os.path.isdir(vectorstore_path):
             raise FileNotFoundError(f"ChromaDB directory not found for classroom '{classroom_id}' at {vectorstore_path}. Did populate_db.py run successfully for this classroom?")

        vectorstore = Chroma(
            persist_directory=vectorstore_path,
            embedding_function=embeddings
        )
        print(f"Vector store loaded from {vectorstore_path}")

        # 3. Initialize LLM (Could also be global if same settings for all classrooms)
        llm = VertexAI(
            model_name=LLM_MODEL_NAME,
            project=google_project_id,
            temperature=0.1, # Lower temperature for more factual answers
            max_output_tokens=1024 # Adjust as needed
        )
        print(f"LLM initialized ({LLM_MODEL_NAME})")

        # 4. Create Retriever for this classroom's vector store
        # Retrieve top 4 most relevant chunks
        retriever = vectorstore.as_retriever(search_kwargs={'k': 4})
        print("Retriever created.")

        # 5. Define Prompt Template (Could also be global)
        template = """
You are an assistant helping answer questions based ONLY on the provided context (Curriculum documents).
If the context doesn't contain the answer, say "Based on the provided documents, I cannot answer that question."
Do not make up information or use external knowledge. Keep your answer concise and relevant to the question.

Context:
{context}

Question:
{question}

Answer:"""
        prompt = PromptTemplate.from_template(template)
        print("Prompt template created.")

        # 6. Define RAG Chain using LangChain Expression Language (LCEL)
        def format_docs(docs):
            # Helper function to join document contents
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            # RunnableParallel allows passing question through and retrieving context
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        print("RAG chain created successfully.")

        # Store initialized components in cache
        initialized_components_cache[classroom_id] = {
            "vectorstore": vectorstore,
            "llm": llm,
            "rag_chain": rag_chain
        }
        print(f"Components cached for classroom: {classroom_id}")
        return initialized_components_cache[classroom_id]

    except Exception as e:
        print(f"ERROR initializing RAG components for classroom {classroom_id}: {e}")
        # Raise the error to prevent the API from running with faulty components
        raise RuntimeError(f"Failed to initialize RAG components for classroom {classroom_id}: {e}")


def get_rag_answer(query: str, classroom_id: str) -> str:
    """
    Processes a query using the RAG pipeline for a specific classroom.
    """
    try:
        # Get or initialize components for the specified classroom
        components = _initialize_classroom_components(classroom_id)
        rag_chain = components.get("rag_chain")

        if not rag_chain:
             raise RuntimeError(f"RAG chain is not initialized for classroom {classroom_id}.")

        print(f"Invoking RAG chain for classroom '{classroom_id}' with query: {query}")
        # Invoke the chain with the user's query
        # Pass config if needed, e.g., for tracing or specific run settings
        answer = rag_chain.invoke(query, config=RunnableConfig(run_name="Classroom RAG Query"))
        print(f"RAG chain returned answer for classroom '{classroom_id}'.")
        return answer

    except FileNotFoundError as e:
         print(f"Error getting RAG answer: {e}")
         return f"Sorry, the data for classroom '{classroom_id}' could not be found. Please ensure it has been processed."
    except Exception as e:
        print(f"Error during RAG chain invocation for classroom {classroom_id}: {e}")
        # Return a generic error message to the user
        return "Sorry, an error occurred while processing your question in this classroom."

# --- MVP2: Service function for adding notes ---
def add_note_to_classroom(classroom_id: str, note_text: str) -> str:
    """
    Adds a text note to the simple in-memory store for a classroom.
    Returns a unique ID for the note (using timestamp for simplicity).
    """
    global classroom_notes_store
    if classroom_id not in classroom_notes_store:
        classroom_notes_store[classroom_id] = []

    # Simple ID generation using timestamp
    note_id = str(time.time())
    classroom_notes_store[classroom_id].append({"id": note_id, "text": note_text})

    print(f"Note added to classroom '{classroom_id}'. Total notes: {len(classroom_notes_store[classroom_id])}")
    # In a real app, save this to a persistent database
    return note_id

def get_classroom_notes(classroom_id: str) -> list[dict]:
     """Retrieves all notes for a given classroom."""
     global classroom_notes_store
     return classroom_notes_store.get(classroom_id, [])

