"""CLAP (Contrastive Language-Audio Pretraining) embeddings for unified audio-text space.

CLAP provides state-of-the-art joint embeddings for audio and text, enabling
powerful cross-modal retrieval. This is significantly better than separate
text and audio models for music information retrieval.

Reference: https://github.com/LAION-AI/CLAP
"""

from typing import List, Union, Optional
import numpy as np
import torch
from transformers import ClapModel, ClapProcessor
import librosa
import logging

logger = logging.getLogger(__name__)


class CLAPEmbedder:
    """Generate unified audio-text embeddings using CLAP model."""

    def __init__(
        self,
        model_name: str = "laion/clap-htsat-unfused",
        device: Optional[str] = None,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize CLAP embedder.

        Args:
            model_name: HuggingFace model name for CLAP
            device: Device to run model on ('cuda', 'cpu', or None for auto)
            cache_dir: Directory to cache downloaded models
        """
        logger.info(f"Loading CLAP model: {model_name}")

        # Set device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Load model and processor
        try:
            self.model = ClapModel.from_pretrained(
                model_name,
                cache_dir=cache_dir
            ).to(self.device)
            self.model.eval()  # Set to evaluation mode

            self.processor = ClapProcessor.from_pretrained(
                model_name,
                cache_dir=cache_dir
            )
        except Exception as e:
            logger.exception(f"Failed to load CLAP model '{model_name}'")
            raise RuntimeError(f"CLAP model initialization failed: {e}") from e

        # Get embedding dimension from model config
        # CLAP projection dimension varies by model (typically 512 or 1024)
        self.embedding_dim = self.model.config.projection_dim

        logger.info(f"CLAP model loaded successfully on {self.device}, embedding_dim={self.embedding_dim}")

    def embed_text(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text(s).

        Args:
            texts: Single text string or list of text strings

        Returns:
            Numpy array of embeddings (n_texts, embedding_dim)
        """
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            raise ValueError("Empty text list provided")

        try:
            # Process texts
            inputs = self.processor(
                text=texts,
                return_tensors="pt",
                padding=True,
                truncation=True
            ).to(self.device)

            # Generate embeddings
            with torch.no_grad():
                text_embeds = self.model.get_text_features(**inputs)

            # Normalize embeddings (CLAP uses normalized embeddings for similarity)
            text_embeds = text_embeds / text_embeds.norm(p=2, dim=-1, keepdim=True)

            return text_embeds.cpu().numpy()

        except Exception as e:
            logger.exception("Error generating text embeddings")
            raise RuntimeError(f"Text embedding generation failed: {e}") from e

    def embed_audio(
        self,
        audio_paths: Union[str, List[str]],
        sample_rate: int = 48000,
        max_duration: float = 10.0
    ) -> np.ndarray:
        """
        Generate embeddings for audio file(s).

        Args:
            audio_paths: Single audio file path or list of paths
            sample_rate: Sample rate for audio (CLAP expects 48kHz)
            max_duration: Maximum duration in seconds to process

        Returns:
            Numpy array of embeddings (n_audios, embedding_dim)
        """
        if isinstance(audio_paths, str):
            audio_paths = [audio_paths]

        if not audio_paths:
            raise ValueError("Empty audio paths list provided")

        audio_arrays = []
        failed_files = []

        for audio_path in audio_paths:
            try:
                # Load audio file
                audio, _ = librosa.load(
                    audio_path,
                    sr=sample_rate,
                    duration=max_duration,
                    mono=True
                )
                audio_arrays.append(audio)
            except Exception as e:
                logger.warning(f"Failed to load audio file {audio_path}: {e}")
                failed_files.append(audio_path)
                # Use zeros as fallback to maintain batch size
                audio_arrays.append(np.zeros(int(sample_rate * max_duration), dtype=np.float32))

        if failed_files and len(failed_files) == len(audio_paths):
            raise RuntimeError(f"All audio files failed to load: {failed_files}")

        try:
            # Process audio
            inputs = self.processor(
                audios=audio_arrays,
                return_tensors="pt",
                sampling_rate=sample_rate,
                padding=True
            ).to(self.device)

            # Generate embeddings
            with torch.no_grad():
                audio_embeds = self.model.get_audio_features(**inputs)

            # Normalize embeddings (CLAP uses normalized embeddings for similarity)
            audio_embeds = audio_embeds / audio_embeds.norm(p=2, dim=-1, keepdim=True)

            return audio_embeds.cpu().numpy()

        except Exception as e:
            logger.exception("Error generating audio embeddings")
            raise RuntimeError(f"Audio embedding generation failed: {e}") from e

    def embed_music_item(
        self,
        title: str,
        artist: str,
        description: str = "",
        metadata: Optional[dict] = None,
        audio_path: Optional[str] = None,
        mode: str = "text"
    ) -> np.ndarray:
        """
        Generate embedding for a music item.

        Args:
            title: Track title
            artist: Artist name
            description: Track description
            metadata: Additional metadata dict
            audio_path: Optional path to audio file
            mode: Embedding mode - 'text', 'audio', or 'hybrid'

        Returns:
            Single embedding vector
        """
        if mode == "text" or (mode == "hybrid" and audio_path is None):
            # Generate text embedding
            parts = [f"Title: {title}", f"Artist: {artist}"]

            if description:
                parts.append(f"Description: {description}")

            if metadata:
                if metadata.get("genre"):
                    parts.append(f"Genre: {metadata['genre']}")
                if metadata.get("mood"):
                    moods = ", ".join(metadata["mood"]) if isinstance(metadata["mood"], list) else metadata["mood"]
                    parts.append(f"Mood: {moods}")
                if metadata.get("cultural_origin"):
                    parts.append(f"Cultural Origin: {metadata['cultural_origin']}")
                if metadata.get("instrumentation"):
                    instruments = ", ".join(metadata["instrumentation"]) if isinstance(metadata["instrumentation"], list) else metadata["instrumentation"]
                    parts.append(f"Instruments: {instruments}")

            combined_text = " | ".join(parts)
            embedding = self.embed_text(combined_text)
            return embedding[0]

        elif mode == "audio" and audio_path:
            # Generate audio embedding
            embedding = self.embed_audio(audio_path)
            return embedding[0]

        elif mode == "hybrid" and audio_path:
            # Generate both and average (simple fusion)
            text_parts = [f"Title: {title}", f"Artist: {artist}"]
            if description:
                text_parts.append(f"Description: {description}")
            combined_text = " | ".join(text_parts)

            text_emb = self.embed_text(combined_text)[0]
            audio_emb = self.embed_audio(audio_path)[0]

            # Average the embeddings (both are normalized)
            hybrid_emb = (text_emb + audio_emb) / 2
            # Re-normalize
            hybrid_emb = hybrid_emb / np.linalg.norm(hybrid_emb)

            return hybrid_emb

        else:
            raise ValueError(f"Invalid mode '{mode}' or missing audio_path for audio/hybrid mode")

    def compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            emb1: First embedding vector
            emb2: Second embedding vector

        Returns:
            Cosine similarity score (0-1, higher is more similar)
        """
        # Ensure embeddings are normalized
        emb1_norm = emb1 / (np.linalg.norm(emb1) + 1e-8)
        emb2_norm = emb2 / (np.linalg.norm(emb2) + 1e-8)

        # Cosine similarity
        similarity = np.dot(emb1_norm, emb2_norm)

        # Clip to [0, 1] range (should already be there for normalized embeddings)
        similarity = np.clip(similarity, 0.0, 1.0)

        return float(similarity)
