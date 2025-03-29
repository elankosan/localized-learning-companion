# populate_db.py
print("--- Script Start ---") # Diagnostic print

import os
import shutil
from dotenv import load_dotenv
# Ensure necessary LangChain components are imported
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- Configuration ---
# Ensure these paths are correct relative to where you run the script (tec folder)
DOCUMENTS_PATH = "documents"
CHROMA_DB_PATH = "chroma_db"
CHUNK_SIZE = 1000 # Size of text chunks (in characters)
CHUNK_OVERLAP = 200 # Overlap between chunks

def main():
    """
    Main function to load, process, and store documents in ChromaDB.
    """
    print("--- Inside main() function ---") # Diagnostic print
    print("--- Starting Document Processing ---")

    # Load environment variables from .env file
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_project_id = os.getenv("GOOGLE_PROJECT_ID")

    # Validate necessary environment variables
    if not google_api_key:
        print("ERROR: GOOGLE_API_KEY not found in .env file.")
        return # Exit if API key is missing

    if not google_project_id:
        print("ERROR: GOOGLE_PROJECT_ID not found in .env file.")
        print("Please add it to your .env file (e.g., GOOGLE_PROJECT_ID='your-project-id').")
        return # Exit if project ID is missing

    # --- Initialize Embeddings ---
    embeddings = None # Initialize variable to None
    try:
        print("Initializing embeddings model (requires GOOGLE_API_KEY and GOOGLE_PROJECT_ID)...")
        embeddings = VertexAIEmbeddings(
            model_name="text-embedding-004",
            project=google_project_id
        )
        print("Embeddings model initialized successfully.")
    except Exception as e:
        print(f"ERROR: Failed to initialize embeddings model: {e}")
        print("Troubleshooting suggestions:")
        print("- Ensure GOOGLE_API_KEY & GOOGLE_PROJECT_ID in .env are correct.")
        print("- Ensure the Vertex AI API is enabled in your Google Cloud project.")
        print("- Ensure your API key has permissions for Vertex AI.")
        print("- Consider using Application Default Credentials (ADC) for more robust authentication:")
        print("  https://cloud.google.com/docs/authentication/provide-credentials-adc")
        return # Exit if initialization fails

    # --- Load Documents ---
    documents = None # Initialize variable
    print(f"Loading documents from directory: '{DOCUMENTS_PATH}'")
    try:
        # Use DirectoryLoader to load files; specify PyPDFLoader for PDFs
        # It should handle .txt files automatically. Add other loaders if needed.
        loader = DirectoryLoader(
            DOCUMENTS_PATH,
            glob="**/*[.pdf|.txt]", # Load both PDF and TXT files
            loader_cls=PyPDFLoader, # Use PyPDFLoader for PDF files
            show_progress=True,
            use_multithreading=True # Might speed up loading
        )
        documents = loader.load()
        if not documents:
            print(f"WARNING: No documents found in '{DOCUMENTS_PATH}'. Stopping.")
            return # Exit if no documents found
        print(f"Successfully loaded {len(documents)} document section(s).")
    except Exception as e:
         print(f"ERROR: Failed to load documents from '{DOCUMENTS_PATH}': {e}")
         print("Troubleshooting suggestions:")
         print("- Check if the 'documents' folder exists and contains supported files (.pdf, .txt).")
         print("- Ensure PyPDF2 library is correctly installed (`pip install pypdf2`).")
         print("- Check file permissions or if files are corrupted.")
         return # Exit if loading fails

    # --- Split Documents ---
    print("Splitting documents into manageable chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len, # Use standard length function
        is_separator_regex=False, # Standard separators
    )
    docs = text_splitter.split_documents(documents)
    if not docs:
         print("ERROR: Failed to split documents into chunks. Check document content.")
         return # Exit if splitting fails
    print(f"Split documents into {len(docs)} chunks.")

    # --- Create or Clear Chroma DB ---
    # For MVP simplicity, we clear the DB each time to avoid duplicates if run multiple times
    if os.path.exists(CHROMA_DB_PATH):
        print(f"Existing database found at '{CHROMA_DB_PATH}'. Clearing it first...")
        try:
            shutil.rmtree(CHROMA_DB_PATH)
            print(f"Successfully cleared old database.")
        except Exception as e:
            print(f"ERROR: Could not remove existing database directory '{CHROMA_DB_PATH}': {e}")
            return # Exit if we can't clear the old DB

    print(f"Creating new vector database directory at: '{CHROMA_DB_PATH}'")
    # Directory will be created by Chroma automatically

    # --- Embed and Store Documents ---
    try:
        print("Embedding document chunks and storing them in ChromaDB...")
        print(f"(Using embedding model: {embeddings.model_name} in project {google_project_id})")
        print("(This step might take a while depending on document size and number)...")
        # This function handles embedding generation and storage
        vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=CHROMA_DB_PATH # Tell Chroma to save to disk
        )
        print(f"Successfully embedded and stored {len(docs)} chunks in '{CHROMA_DB_PATH}'.")
    except Exception as e:
        print(f"ERROR: Failed during embedding or storing documents in ChromaDB: {e}")
        print("Troubleshooting suggestions:")
        print("- Check your Google Cloud API quota for Vertex AI Embeddings.")
        print("- Ensure sufficient disk space and permissions for the '{CHROMA_DB_PATH}' directory.")
        print("- Check network connectivity during the API calls for embedding.")
        return # Exit if embedding/storing fails

    print("--- Document Processing Complete ---")


# --- Script execution entry point ---
print(f"--- Script loaded. __name__ is: {__name__} ---") # Diagnostic print

if __name__ == "__main__":
    # This block executes only when the script is run directly
    print("--- Running main() because __name__ is '__main__' ---") # Diagnostic print
    main() # Call the main processing function
else:
    # This block executes if the script is imported as a module
    print(f"--- Not running main() because __name__ is '{__name__}' ---") # Diagnostic print

print("--- Script End ---") # Diagnostic print