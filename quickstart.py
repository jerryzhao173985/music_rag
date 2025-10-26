#!/usr/bin/env python3
"""Quick start script for Music RAG system."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from music_rag.cli import MusicRAGSystem
from music_rag.src.models.music_item import RetrievalQuery
from music_rag.src.data.sample_data_generator import generate_sample_music_data


def main():
    """Run a quick demonstration of the Music RAG system."""

    print("=" * 70)
    print("  MUSIC RAG - Quick Start Demo")
    print("  Retrieval Augmented Generation for Music Discovery")
    print("=" * 70)
    print()

    # Initialize system
    print("1. Initializing system...")
    system = MusicRAGSystem(db_path="./data/chromadb_quickstart")

    # Generate and index sample data
    print("2. Loading sample music dataset...")
    sample_items = generate_sample_music_data()
    system.index_music_items(sample_items)

    print(f"\n✓ Indexed {len(sample_items)} diverse music tracks")
    print(f"  Including: Classical, Jazz, Indian Classical, Electronic, Rock, etc.\n")

    # Demo queries
    print("=" * 70)
    print("  DEMO QUERIES")
    print("=" * 70)
    print()

    demo_queries = [
        {
            "query": "upbeat energetic dance music",
            "filters": {},
        },
        {
            "query": "meditative spiritual music",
            "filters": {"genre_filter": ["Indian Classical", "Middle Eastern"]},
        },
        {
            "query": "powerful orchestral symphony",
            "filters": {},
        },
        {
            "query": "live performance with drums",
            "filters": {},
        }
    ]

    for i, demo in enumerate(demo_queries, 1):
        print(f"\nQuery {i}: '{demo['query']}'")
        if demo['filters']:
            print(f"Filters: {demo['filters']}")
        print("-" * 70)

        query = RetrievalQuery(
            text_query=demo['query'],
            top_k=3,
            **demo['filters']
        )

        results = system.search(query)

        for j, result in enumerate(results, 1):
            item = result.music_item
            print(f"\n  {j}. {item.title} - {item.artist}")
            print(f"     Genre: {item.metadata.genre}")
            print(f"     Mood: {', '.join(item.metadata.mood[:2]) if item.metadata.mood else 'N/A'}")
            print(f"     Score: {result.score:.3f} ({result.retrieval_type})")

        print()

    # Show stats
    print("=" * 70)
    print("  DATABASE STATISTICS")
    print("=" * 70)
    stats = system.db.get_stats()
    print(f"\n  Text embeddings: {stats['text_embeddings_count']}")
    print(f"  Audio embeddings: {stats['audio_embeddings_count']}")

    # Next steps
    print("\n" + "=" * 70)
    print("  NEXT STEPS")
    print("=" * 70)
    print("""
1. Try the CLI:
   python -m music_rag.cli search "your query here" --top-k 5

2. Run the interactive demo:
   python -m music_rag.cli demo

3. Explore the Jupyter notebook:
   jupyter notebook notebooks/demo_notebook.ipynb

4. Read the documentation:
   cat README.md

For more information, see README.md
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        print("Please ensure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
