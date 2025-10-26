"""Audio embedding generation using librosa features."""

from typing import Optional
import numpy as np
import librosa


class AudioEmbedder:
    """Generate audio embeddings from music files."""

    def __init__(self, sr: int = 22050, n_mfcc: int = 40):
        """
        Initialize audio embedder.

        Args:
            sr: Sample rate for audio processing
            n_mfcc: Number of MFCC coefficients
        """
        self.sr = sr
        self.n_mfcc = n_mfcc
        self.embedding_dim = n_mfcc * 3  # MFCCs + chroma + spectral features

    def embed(self, audio_path: str, duration: Optional[float] = 30.0) -> np.ndarray:
        """
        Generate embedding from audio file.

        Args:
            audio_path: Path to audio file
            duration: Maximum duration to process (seconds)

        Returns:
            Audio embedding vector
        """
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sr, duration=duration)

            # Extract MFCCs (mean across time)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.n_mfcc)
            mfcc_mean = np.mean(mfccs, axis=1)

            # Extract chroma features
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)

            # Extract spectral features
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
            spectral_features = np.array([
                np.mean(spectral_centroid),
                np.std(spectral_centroid),
                np.mean(spectral_rolloff),
                np.std(spectral_rolloff)
            ])

            # Pad chroma to match MFCC dimensions for concatenation
            chroma_padded = np.pad(chroma_mean, (0, self.n_mfcc - len(chroma_mean)))

            # Combine features
            embedding = np.concatenate([
                mfcc_mean,
                chroma_padded,
                np.pad(spectral_features, (0, self.n_mfcc - len(spectral_features)))
            ])

            return embedding

        except Exception as e:
            print(f"Error processing audio {audio_path}: {e}")
            # Return zero vector on error
            return np.zeros(self.embedding_dim)

    def extract_metadata(self, audio_path: str) -> dict:
        """
        Extract basic metadata from audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with tempo, duration, etc.
        """
        try:
            y, sr = librosa.load(audio_path, sr=self.sr)

            # Estimate tempo
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

            # Get duration
            duration = librosa.get_duration(y=y, sr=sr)

            return {
                "tempo": float(tempo),
                "duration": float(duration)
            }

        except Exception as e:
            print(f"Error extracting metadata from {audio_path}: {e}")
            return {}
