"""Hugging Face Space entry point for Music RAG Gradio UI.

This file serves as the entry point for deploying Music RAG to Hugging Face Spaces.
It launches the Gradio interface with auto-initialization of sample data on first run.

For local testing: python app.py
For HF Spaces: This file is automatically detected and run.
"""

import os
import sys
import logging
from pathlib import Path

# Add music_rag to path for proper imports
sys.path.insert(0, str(Path(__file__).parent))

from music_rag.ui.gradio_app import create_interface
from music_rag.cli import MusicRAGSystem
from music_rag.src.data.sample_data_generator import generate_sample_music_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ensure_sample_data(db_path: str):
    """
    Ensure sample data exists in the database.
    Only initializes if the database is empty.

    Args:
        db_path: Path to ChromaDB directory
    """
    logger.info(f"Checking database at {db_path}...")

    # Create database directory if it doesn't exist
    os.makedirs(db_path, exist_ok=True)

    # Check if database has data
    try:
        rag_system = MusicRAGSystem(db_path=db_path)
        stats = rag_system.db.get_stats()
        item_count = stats.get('text_embeddings_count', 0)

        if item_count > 0:
            logger.info(f"Database already contains {item_count} items. Skipping initialization.")
            return

        # Database is empty - initialize with sample data
        logger.info("Database is empty. Initializing with sample music data...")
        sample_items = generate_sample_music_data()
        logger.info(f"Indexing {len(sample_items)} sample music items...")
        rag_system.index_music_items(sample_items)
        logger.info(f"Successfully indexed {len(sample_items)} items!")

    except Exception as e:
        logger.error(f"Error initializing sample data: {e}")
        logger.warning("Continuing without sample data. You can add items via the UI.")


if __name__ == "__main__":
    logger.info("Starting Music RAG Hugging Face Space...")

    # Determine database path (HF Spaces may have specific requirements)
    db_path = os.getenv("CHROMADB_PATH", "./data/chromadb")

    # Ensure sample data exists (idempotent)
    ensure_sample_data(db_path)

    # Get OpenAI API key from environment (optional enhancement)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.info(
            "OPENAI_API_KEY not set. Query enhancement and explanations will be disabled. "
            "To enable these features, add OPENAI_API_KEY to your Space secrets."
        )
    else:
        logger.info("OPENAI_API_KEY found. Enhanced features enabled.")

    # Create and launch Gradio interface
    # Note: create_interface will initialize its own MusicRAGSystem
    logger.info("Creating Gradio interface...")
    app = create_interface(
        db_path=db_path,
        openai_api_key=openai_api_key
    )

    # Launch with settings optimized for Hugging Face Spaces
    logger.info("Launching Gradio app...")
    app.launch(
        server_name="0.0.0.0",  # Required for HF Spaces
        server_port=7860,        # Default Gradio port
        share=False,             # HF Spaces handles sharing
        show_error=True,         # Show errors for debugging
        quiet=False              # Show launch info
    )
