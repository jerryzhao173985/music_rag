"""FastAPI REST API for Music RAG."""

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
from contextlib import asynccontextmanager

from .config import settings
from .logging_config import logger
from .src.models.music_item import RetrievalQuery, QueryResult, MusicItem
from .src.database.vector_db import MusicVectorDB
from .src.embeddings.text_embedder import TextEmbedder
from .src.embeddings.audio_embedder import AudioEmbedder
from .src.retrieval.retrieval_engine import RetrievalEngine


# Global instances
db: Optional[MusicVectorDB] = None
text_embedder: Optional[TextEmbedder] = None
audio_embedder: Optional[AudioEmbedder] = None
retrieval_engine: Optional[RetrievalEngine] = None
music_items_cache: Dict[str, MusicItem] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    # Startup
    logger.info("Starting Music RAG API...")
    global db, text_embedder, audio_embedder, retrieval_engine

    try:
        db = MusicVectorDB(settings.chromadb_path)
        text_embedder = TextEmbedder(settings.text_model)
        audio_embedder = AudioEmbedder(settings.audio_sample_rate, settings.audio_n_mfcc)
        retrieval_engine = RetrievalEngine(db, text_embedder, audio_embedder)

        logger.info(f"Initialized vector database at {settings.chromadb_path}")
        logger.info(f"Text model: {settings.text_model}")

        stats = db.get_stats()
        logger.info(f"Database contains {stats['text_embeddings_count']} text embeddings")
        logger.info("Music RAG API started successfully")

    except Exception as e:
        logger.error(f"Failed to initialize API: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Music RAG API...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Retrieval-Augmented Generation API for Music Discovery",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key security (optional)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    """Verify API key if configured."""
    if settings.api_key and api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        stats = db.get_stats() if db else {}
        return {
            "status": "healthy",
            "database": "connected",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.post("/search", response_model=List[Dict[str, Any]])
async def search(
    query: RetrievalQuery,
    api_key: str = Depends(verify_api_key)
):
    """
    Search for music using text or audio queries.

    Args:
        query: Retrieval query with parameters

    Returns:
        List of search results with music items and scores
    """
    try:
        logger.info(f"Search request: {query.text_query or query.audio_path}")

        if not retrieval_engine:
            raise HTTPException(status_code=503, detail="Retrieval engine not initialized")

        results = retrieval_engine.retrieve(query, music_items_cache)

        # Format results
        formatted_results = [
            {
                "id": r.music_item.id,
                "title": r.music_item.title,
                "artist": r.music_item.artist,
                "description": r.music_item.description,
                "genre": r.music_item.metadata.genre,
                "mood": r.music_item.metadata.mood,
                "cultural_origin": r.music_item.metadata.cultural_origin,
                "tempo": r.music_item.metadata.tempo,
                "score": r.score,
                "retrieval_type": r.retrieval_type
            }
            for r in results
        ]

        logger.info(f"Returning {len(formatted_results)} results")
        return formatted_results

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index")
async def index_music_item(
    item: MusicItem,
    api_key: str = Depends(verify_api_key)
):
    """
    Index a new music item.

    Args:
        item: Music item to index

    Returns:
        Success message
    """
    try:
        logger.info(f"Indexing: {item.title} by {item.artist}")

        if not text_embedder or not db:
            raise HTTPException(status_code=503, detail="Services not initialized")

        # Generate text embedding
        text_emb = text_embedder.embed_music_item(
            title=item.title,
            artist=item.artist,
            description=item.description or "",
            metadata=item.metadata.model_dump()
        )

        # Generate audio embedding if path provided
        audio_emb = None
        if item.audio_path and audio_embedder:
            audio_emb = audio_embedder.embed(item.audio_path)

        # Add to database
        db.add_music_item(
            id=item.id,
            text_embedding=text_emb,
            audio_embedding=audio_emb,
            metadata=item.metadata.model_dump()
        )

        # Cache the item
        music_items_cache[item.id] = item

        logger.info(f"Successfully indexed: {item.id}")

        return {
            "status": "success",
            "id": item.id,
            "message": f"Indexed {item.title} by {item.artist}"
        }

    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index/batch")
async def index_batch(
    items: List[MusicItem],
    api_key: str = Depends(verify_api_key)
):
    """
    Index multiple music items in batch.

    Args:
        items: List of music items to index

    Returns:
        Success message with count
    """
    try:
        logger.info(f"Batch indexing {len(items)} items")

        if not text_embedder or not db:
            raise HTTPException(status_code=503, detail="Services not initialized")

        if len(items) > settings.max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"Batch size {len(items)} exceeds maximum {settings.max_batch_size}"
            )

        ids = []
        text_embeddings = []
        audio_embeddings = []
        metadatas = []

        for item in items:
            # Generate embeddings
            text_emb = text_embedder.embed_music_item(
                title=item.title,
                artist=item.artist,
                description=item.description or "",
                metadata=item.metadata.model_dump()
            )

            ids.append(item.id)
            text_embeddings.append(text_emb)
            metadatas.append(item.metadata.model_dump())

            # Cache the item
            music_items_cache[item.id] = item

            # Audio embeddings (optional)
            if item.audio_path and audio_embedder:
                audio_emb = audio_embedder.embed(item.audio_path)
                audio_embeddings.append(audio_emb)

        # Batch add to database
        db.add_batch(
            ids=ids,
            text_embeddings=text_embeddings,
            audio_embeddings=audio_embeddings if audio_embeddings else None,
            metadatas=metadatas
        )

        logger.info(f"Successfully indexed {len(items)} items")

        return {
            "status": "success",
            "count": len(items),
            "message": f"Indexed {len(items)} music items"
        }

    except Exception as e:
        logger.error(f"Batch indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats(api_key: str = Depends(verify_api_key)):
    """
    Get database statistics.

    Returns:
        Database statistics
    """
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not initialized")

        stats = db.get_stats()
        stats["cached_items"] = len(music_items_cache)

        return stats

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/item/{item_id}")
async def get_item(item_id: str, api_key: str = Depends(verify_api_key)):
    """
    Get a specific music item by ID.

    Args:
        item_id: Music item ID

    Returns:
        Music item details
    """
    if item_id not in music_items_cache:
        raise HTTPException(status_code=404, detail="Item not found")

    item = music_items_cache[item_id]
    return item.model_dump()


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "music_rag.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )
