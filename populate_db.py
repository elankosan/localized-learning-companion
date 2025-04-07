# populate_db.py (MVP2 Version - Handles multiple classrooms)
print("--- Script Start ---") # Diagnostic print

import os
import shutil
from dotenv import load_dotenv
from glob import glob # Import glob for finding files

# LangChain components
# Ensure these are installed in your venv:
# pip install langchain-google-vertexai langchain-community langchain python-dotenv chromadb pypdf2
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader # Added TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- Configuration ---

# Base directory where individual classroom DBs will be stored
CHROMA_DBS_ROOT = "chroma_dbs"
# Base directory where source curriculum documents are located
DOCUMENTS_ROOT = "documents"

# Define your classrooms here
# Key: A unique classroom ID (string, used for directory names)
# Value: A dictionary containing 'name' and 'curriculum_path' (relative to DOCUMENTS_ROOT)
#        and optionally 'glob_pattern' for files to load.
CLASSROOMS = {
    "math_g10_tamil": {
        "name": "Grade 10 Math (Tamil)",
        "curriculum_path": "classroom_math_g10", # Subfolder within DOCUMENTS_ROOT
        "glob_pattern": "**/*[.pdf|.txt]" # Files to load
    },
    "ai_intro_eng": {
        "name": "AI Introduction (English)",
        "curriculum_path": "classroom_ai_intro", # Subfolder within DOCUMENTS_ROOT
        "glob_pattern": "**/*[.pdf|.txt]" # Files to load
    },
    # Add more classrooms here following the pattern
    # "example_id": {
    #    "name": "Example Name",
    #    "curriculum_path": "example_folder_in_documents",
    #    "glob_pattern": "**/*.pdf" # Only load PDFs
    # }
}

# Chunking parameters (can be adjusted)
CHUNK_SIZE = 1000 # Size of text chunks (in characters)
CHUNK_OVERLAP = 200 # Overlap between chunks

def process_classroom(classroom_id: str, config: dict, embeddings: VertexAIEmbeddings):
    """
    Loads, splits, embeds, and stores documents for a single classroom.
    Returns True on success, False on failure for this classroom.
    """
    classroom_name = config.get("name", classroom_id)
    curriculum_subdir = config.get("curriculum_path")
    glob_pattern = config.get("glob_pattern", "**/*[.pdf|.txt]") # Default pattern

    print(f"\n--- Processing Classroom: {classroom_name} (ID: {classroom_id}) ---")

    if not curriculum_subdir:
        print(f"ERROR: Missing 'curriculum_path' for classroom {classroom_id}. Skipping.")
        return False

    # --- Define Paths ---
    # Path to the source documents for this classroom
    source_docs_path = os.path.join(DOCUMENTS_ROOT, curriculum_subdir)
    # Path where the vector database for this classroom will be stored
    vectorstore_path = os.path.join(CHROMA_DBS_ROOT, classroom_id) # Unique DB path per classroom

    if not os.path.isdir(source_docs_path):
        print(f"ERROR: Source document directory not found: '{source_docs_path}'. Skipping classroom.")
        return False

    # --- Load Documents Individually ---
    documents = [] # Initialize list for loaded document sections/pages
    print(f"Scanning for files in: '{source_docs_path}' using pattern '{glob_pattern}'")
    try:
        # Construct the search pattern
        file_search_pattern = os.path.join(source_docs_path, glob_pattern)
        # Find all matching files recursively
        file_paths = glob(file_search_pattern, recursive=True)

        if not file_paths:
            print(f"WARNING: No documents found matching pattern in '{source_docs_path}'. Skipping classroom.")
            return False # Treat as non-fatal for this classroom, but report failure

        print(f"Found {len(file_paths)} files to process.")
        # Loop through each found file path
        for file_path in file_paths:
            try:
                print(f"--> Loading file: {file_path}")
                # Select loader based on file extension
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext == ".pdf":
                    loader = PyPDFLoader(file_path)
                elif file_ext == ".txt":
                    loader = TextLoader(file_path, encoding='utf-8') # Specify encoding for text
                else:
                    print(f"    Skipping unsupported file type: {file_path}")
                    continue # Skip to next file

                # Load returns a list of Documents (pages for PDF, one doc for TXT)
                file_docs = loader.load()

                if file_docs is None: # Explicitly check if loader returned None
                     print(f"WARNING: Loader returned None for file: {file_path}. Skipping.")
                     continue

                # Add document source metadata (useful for RAG later)
                for doc in file_docs:
                    # Ensure metadata exists
                    if not hasattr(doc, 'metadata') or doc.metadata is None:
                         doc.metadata = {}
                    doc.metadata["source"] = os.path.basename(file_path)

                documents.extend(file_docs)
                print(f"    Loaded {len(file_docs)} sections from {os.path.basename(file_path)}. Total sections now: {len(documents)}")

            except Exception as e_file:
                # Catch errors during loading/processing of a single file
                print(f"ERROR: Failed to load or process file '{file_path}': {e_file}. Skipping this file.")
                # Continue processing other files

        # Check if any documents were successfully loaded after the loop
        if not documents:
            print(f"ERROR: No documents could be successfully loaded for classroom {classroom_id}. Skipping.")
            return False
        print(f"Successfully finished loading files. Total loaded sections: {len(documents)}")

    except Exception as e_outer:
         # Catch unexpected errors during the file listing/looping process itself
         print(f"ERROR: An unexpected error occurred during the document loading loop for {classroom_id}: {e_outer}")
         return False

    # --- Filter Problematic Loaded Content ---
    print("DEBUG: Checking loaded content for validity...")
    problematic_indices = []
    valid_documents = [] # Keep track of documents with valid content
    for i, doc in enumerate(documents):
        page_meta = doc.metadata.get('page', 'N/A') # Get page number if available
        source_meta = doc.metadata.get('source', 'N/A') # Get source filename

        is_problematic = False
        # Check if page_content exists, is a string, and is not empty/whitespace
        if not hasattr(doc, 'page_content') or doc.page_content is None:
            print(f"DEBUG: Invalid content (None) - Index {i}, Source: {source_meta}, Page: {page_meta}")
            is_problematic = True
        elif not isinstance(doc.page_content, str):
            print(f"DEBUG: Invalid content (Non-string: {type(doc.page_content)}) - Index {i}, Source: {source_meta}, Page: {page_meta}")
            is_problematic = True
        elif not doc.page_content.strip():
            print(f"DEBUG: Invalid content (Empty/Whitespace) - Index {i}, Source: {source_meta}, Page: {page_meta}")
            is_problematic = True

        if not is_problematic:
            valid_documents.append(doc) # Add to list of valid documents

    if len(valid_documents) < len(documents):
        print(f"DEBUG: Filtered out {len(documents) - len(valid_documents)} problematic sections.")
    if not valid_documents:
        print(f"ERROR: No valid content remaining after filtering for classroom {classroom_id}. Skipping.")
        return False
    documents = valid_documents # Replace original list with the filtered list
    print(f"DEBUG: Kept {len(documents)} valid sections for splitting.")
    # --- End Filtering block ---

    # --- Split Documents ---
    print("Splitting valid document sections into manageable chunks...")
    docs_split = None # Initialize
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len, # Use standard length function
            is_separator_regex=False, # Standard separators
        )
        docs_split = text_splitter.split_documents(documents) # Use the filtered 'documents' list

        if not docs_split:
             # Check if splitting resulted in empty list
             raise ValueError("Text splitting resulted in zero chunks. Check content and splitter settings.")

        print(f"Split valid sections into {len(docs_split)} chunks.")
    except Exception as e_split:
        print(f"ERROR: Failed during text splitting for {classroom_id}: {e_split}")
        return False # Exit if splitting fails

    # --- Create or Clear Classroom's Chroma DB ---
    # For MVP simplicity, we clear the DB each time to avoid duplicates if run multiple times
    if os.path.exists(vectorstore_path):
        print(f"Clearing existing database for classroom {classroom_id} at '{vectorstore_path}'...")
        try:
            shutil.rmtree(vectorstore_path)
            print(f"Successfully cleared old database.")
        except Exception as e_rm:
            print(f"ERROR: Could not remove existing database directory '{vectorstore_path}': {e_rm}")
            return False # Exit if we can't clear the old DB
    else:
         print(f"No existing database found at '{vectorstore_path}'. Creating new.")


    print(f"Creating vector database for classroom {classroom_id} at: '{vectorstore_path}'")
    # Directory will be created by Chroma automatically if it doesn't exist

    # --- Embed and Store Documents ---
    try:
        print("Embedding document chunks and storing them in ChromaDB...")
        print(f"(Using embedding model: {embeddings.model_name})") # Project ID known globally
        print("(This step might take a while)...")

        # This function handles embedding generation and storage
        vectorstore = Chroma.from_documents(
            documents=docs_split, # Use the split documents
            embedding=embeddings,
            persist_directory=vectorstore_path # Tell Chroma to save to disk here
        )
        print(f"Successfully embedded and stored {len(docs_split)} chunks in '{vectorstore_path}'.")
        print(f"--- Successfully processed classroom {classroom_name} (ID: {classroom_id}) ---")
        return True # Indicate success for this classroom
    except Exception as e_embed:
        print(f"ERROR: Failed during embedding or storing documents in ChromaDB for {classroom_id}: {e_embed}")
        print("Troubleshooting suggestions:")
        print("- Check your Google Cloud API quota for Vertex AI Embeddings.")
        print("- Ensure sufficient disk space and permissions for the '{vectorstore_path}' directory.")
        print("- Check network connectivity.")
        return False # Indicate failure for this classroom


# --- Main Execution Logic ---
if __name__ == "__main__":
    print("--- Main execution started ---")
    # Load environment variables from .env file at the start
    load_dotenv()
    google_project_id = os.getenv("GOOGLE_PROJECT_ID")

    # Crucial check for Project ID needed for embeddings
    if not google_project_id:
        print("FATAL ERROR: GOOGLE_PROJECT_ID not found in .env file. Please ensure it is set.")
        exit(1) # Exit script if project ID is missing

    # Initialize embeddings model once globally
    embeddings_client = None
    try:
        print("Initializing embeddings model globally...")
        embeddings_client = VertexAIEmbeddings(
            model_name="text-embedding-004",
            project=google_project_id
            )
        print("Embeddings model initialized.")
    except Exception as e:
        print(f"FATAL ERROR: Failed to initialize embeddings model: {e}. Please check credentials and GCP setup.")
        exit(1) # Exit script if embedding client fails

    processed_count = 0
    failed_count = 0
    # Create the root DB directory if it doesn't exist
    try:
        os.makedirs(CHROMA_DBS_ROOT, exist_ok=True)
    except OSError as e:
        print(f"FATAL ERROR: Could not create root DB directory '{CHROMA_DBS_ROOT}': {e}")
        exit(1)


    # Loop through defined classrooms and process each
    if not CLASSROOMS:
         print("WARNING: No classrooms defined in the CLASSROOMS dictionary. Nothing to process.")
    else:
        for c_id, c_config in CLASSROOMS.items():
            if process_classroom(c_id, c_config, embeddings_client):
                processed_count += 1
            else:
                failed_count += 1

    print("\n--- Processing Summary ---")
    print(f"Successfully processed: {processed_count} classroom(s)")
    print(f"Failed to process: {failed_count} classroom(s)")
    print("--- Script End ---")

else:
    # This part likely won't be used if script is run directly
    print(f"--- Script loaded as module (__name__: {__name__}). Main processing skipped. ---")

