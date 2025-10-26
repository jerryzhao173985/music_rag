"""Command-line interface for Music RAG system."""

import click
import json
from pathlib import Path
from typing import Dict
from .src.database.vector_db import MusicVectorDB
from .src.embeddings.text_embedder import TextEmbedder
from .src.embeddings.audio_embedder import AudioEmbedder
from .src.retrieval.retrieval_engine import RetrievalEngine
from .src.models.music_item import MusicItem, MusicMetadata, RetrievalQuery
from .src.data.sample_data_generator import generate_sample_music_data


class MusicRAGSystem:
    """Main Music RAG system."""

    def __init__(self, db_path: str = "./data/chromadb"):
        self.db = MusicVectorDB(db_path)
        self.text_embedder = TextEmbedder()
        self.audio_embedder = AudioEmbedder()
        self.retrieval_engine = RetrievalEngine(self.db, self.text_embedder, self.audio_embedder)
        self.music_items_cache: Dict[str, MusicItem] = {}

    def index_music_items(self, items: list[MusicItem]):
        """Index music items into the database."""
        click.echo(f"Indexing {len(items)} music items...")

        for item in items:
            # Generate text embedding
            text_emb = self.text_embedder.embed_music_item(
                title=item.title,
                artist=item.artist,
                description=item.description or "",
                metadata=item.metadata.model_dump()
            )

            # For now, we'll skip audio embeddings unless audio_path exists
            audio_emb = None
            if item.audio_path:
                audio_emb = self.audio_embedder.embed(item.audio_path)

            # Add to database
            self.db.add_music_item(
                id=item.id,
                text_embedding=text_emb,
                audio_embedding=audio_emb,
                metadata=item.metadata.model_dump()
            )

            # Cache the full item
            self.music_items_cache[item.id] = item

        click.echo(f"✓ Indexed {len(items)} items")
        click.echo(f"Database stats: {self.db.get_stats()}")

    def search(self, query: RetrievalQuery) -> list:
        """Execute search query."""
        results = self.retrieval_engine.retrieve(query, self.music_items_cache)
        return results


@click.group()
def cli():
    """Music RAG - Retrieval Augmented Generation for Music Discovery."""
    pass


@cli.command()
@click.option('--db-path', default='./data/chromadb', help='Path to vector database')
def init_sample_data(db_path: str):
    """Initialize system with sample music data."""
    click.echo("Initializing Music RAG with sample data...")

    system = MusicRAGSystem(db_path)

    # Generate and index sample data
    sample_items = generate_sample_music_data()
    system.index_music_items(sample_items)

    click.echo(f"\n✓ System initialized with {len(sample_items)} sample tracks")


@cli.command()
@click.argument('query_text')
@click.option('--top-k', default=5, help='Number of results to return')
@click.option('--genre', help='Filter by genre')
@click.option('--mood', help='Filter by mood')
@click.option('--db-path', default='./data/chromadb', help='Path to vector database')
def search(query_text: str, top_k: int, genre: str, mood: str, db_path: str):
    """Search for music using text query."""
    click.echo(f"Searching for: {query_text}\n")

    system = MusicRAGSystem(db_path)

    # Load cached items (in production, this would be more sophisticated)
    sample_items = generate_sample_music_data()
    for item in sample_items:
        system.music_items_cache[item.id] = item

    # Build query
    query = RetrievalQuery(
        text_query=query_text,
        top_k=top_k,
        genre_filter=[genre] if genre else None,
        mood_filter=[mood] if mood else None
    )

    results = system.search(query)

    # Display results
    if not results:
        click.echo("No results found.")
        return

    click.echo(f"Found {len(results)} results:\n")
    for i, result in enumerate(results, 1):
        item = result.music_item
        click.echo(f"{i}. {item.title} - {item.artist}")
        click.echo(f"   Genre: {item.metadata.genre or 'N/A'}")
        click.echo(f"   Mood: {', '.join(item.metadata.mood) if item.metadata.mood else 'N/A'}")
        click.echo(f"   Score: {result.score:.3f} ({result.retrieval_type})")
        if item.description:
            click.echo(f"   Description: {item.description}")
        click.echo()


@cli.command()
@click.option('--db-path', default='./data/chromadb', help='Path to vector database')
def stats(db_path: str):
    """Show database statistics."""
    system = MusicRAGSystem(db_path)
    stats = system.db.get_stats()

    click.echo("Database Statistics:")
    click.echo(f"  Text embeddings: {stats['text_embeddings_count']}")
    click.echo(f"  Audio embeddings: {stats['audio_embeddings_count']}")


@cli.command()
def demo():
    """Run interactive demo."""
    click.echo("=== Music RAG System Demo ===\n")

    # Initialize system
    click.echo("Initializing system...")
    system = MusicRAGSystem()

    # Load sample data
    sample_items = generate_sample_music_data()
    system.index_music_items(sample_items)

    click.echo("\n" + "="*50)
    click.echo("Sample queries to try:")
    click.echo("="*50 + "\n")

    demo_queries = [
        {
            "text": "upbeat energetic dance music",
            "description": "Finding upbeat, energetic tracks"
        },
        {
            "text": "relaxing meditative spiritual music",
            "description": "Finding calm, meditative pieces"
        },
        {
            "text": "powerful orchestral symphony",
            "description": "Finding epic classical music"
        },
        {
            "text": "traditional world music with drums",
            "description": "Finding percussive world music"
        }
    ]

    for demo in demo_queries:
        click.echo(f"\n{demo['description']}")
        click.echo(f"Query: '{demo['text']}'")
        click.echo("-" * 50)

        query = RetrievalQuery(text_query=demo['text'], top_k=3)
        results = system.search(query)

        for i, result in enumerate(results, 1):
            item = result.music_item
            click.echo(f"{i}. {item.title} - {item.artist}")
            click.echo(f"   {item.metadata.genre} | {', '.join(item.metadata.mood[:2])}")
            click.echo(f"   Score: {result.score:.3f}\n")


if __name__ == '__main__':
    cli()
