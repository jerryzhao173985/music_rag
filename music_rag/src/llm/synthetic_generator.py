"""Synthetic data generation using LLMs for testing and evaluation.

Generates diverse music queries, descriptions, and evaluation datasets
for comprehensive system testing.
"""

from typing import List, Dict, Optional, Any
import json
import logging
from openai import OpenAI
import random

logger = logging.getLogger(__name__)


class SyntheticDataGenerator:
    """Generate synthetic music data for testing and evaluation."""

    QUERY_GENERATION_PROMPT = """You are a music search expert generating diverse test queries.

Generate {count} realistic music search queries that cover:
- Different search intents (discovery, mood-based, artist similarity, genre exploration)
- Various music genres (pop, rock, jazz, classical, electronic, hip-hop, world music, etc.)
- Different moods and emotions
- Specific and general queries
- Simple and complex queries
- Cultural diversity

Respond with JSON array of query objects:
[
  {{
    "query": "the search query text",
    "intent": "discovery/mood-based/artist-similarity/genre-exploration/contextual",
    "expected_genres": ["genre1", "genre2"],
    "expected_moods": ["mood1", "mood2"],
    "complexity": "simple/medium/complex"
  }},
  ...
]"""

    DESCRIPTION_GENERATION_PROMPT = """You are a music journalist writing engaging descriptions.

For a music track with the following metadata, write a rich, detailed description:
Title: {title}
Artist: {artist}
Genre: {genre}
Mood: {mood}
Tempo: {tempo} BPM
Key: {key}
Era: {era}

Write a 2-3 sentence description that captures the essence, mood, and musical characteristics.
Be specific and evocative. Format as JSON: {{"description": "your description here"}}"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.8
    ):
        """
        Initialize synthetic data generator.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            temperature: Sampling temperature (higher = more creative)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

        logger.info(f"Synthetic data generator initialized with model: {model}")

    def generate_queries(
        self,
        count: int = 100,
        seed: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic music search queries.

        Args:
            count: Number of queries to generate
            seed: Optional random seed for reproducibility

        Returns:
            List of query dicts
        """
        if seed is not None:
            random.seed(seed)

        try:
            prompt = self.QUERY_GENERATION_PROMPT.format(count=count)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a test data generator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )

            # Parse response
            result = json.loads(response.choices[0].message.content)

            # Handle both array and object with queries key
            if isinstance(result, list):
                queries = result
            elif 'queries' in result:
                queries = result['queries']
            else:
                logger.warning("Unexpected response format, using empty list")
                queries = []

            logger.info(f"Generated {len(queries)} synthetic queries")

            return queries

        except Exception as e:
            logger.exception("Error generating synthetic queries")
            return self._fallback_queries(count)

    def generate_description(
        self,
        title: str,
        artist: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Generate a rich description for a music track.

        Args:
            title: Track title
            artist: Artist name
            metadata: Track metadata

        Returns:
            Generated description string
        """
        try:
            prompt = self.DESCRIPTION_GENERATION_PROMPT.format(
                title=title,
                artist=artist,
                genre=metadata.get('genre', 'Unknown'),
                mood=', '.join(metadata.get('mood', ['Unknown'])) if isinstance(metadata.get('mood'), list) else metadata.get('mood', 'Unknown'),
                tempo=metadata.get('tempo', 'Unknown'),
                key=metadata.get('key', 'Unknown'),
                era=metadata.get('era', 'Unknown')
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a music journalist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=200,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            description = result.get('description', '')

            logger.debug(f"Generated description for '{title}'")

            return description

        except Exception as e:
            logger.exception("Error generating description")
            return f"A {metadata.get('genre', 'music')} track by {artist}."

    def generate_evaluation_dataset(
        self,
        num_queries: int = 50,
        items_per_query: int = 10
    ) -> Dict[str, Any]:
        """
        Generate a complete evaluation dataset with queries and relevance judgments.

        Args:
            num_queries: Number of evaluation queries
            items_per_query: Number of items to judge per query

        Returns:
            Dict with queries and relevance judgments
        """
        logger.info(f"Generating evaluation dataset: {num_queries} queries")

        # Generate queries
        queries = self.generate_queries(count=num_queries)

        # For each query, we would need to generate relevance judgments
        # This is a simplified version - in practice, you'd retrieve actual items
        # and ask the LLM to judge relevance

        evaluation_data = {
            "queries": queries,
            "relevance_judgments": {},
            "metadata": {
                "num_queries": num_queries,
                "items_per_query": items_per_query,
                "model": self.model,
                "generated_at": None  # Would add timestamp
            }
        }

        return evaluation_data

    def generate_music_metadata(
        self,
        title: str,
        artist: str
    ) -> Dict[str, Any]:
        """
        Generate realistic metadata for a music track.

        Args:
            title: Track title
            artist: Artist name

        Returns:
            Generated metadata dict
        """
        try:
            prompt = f"""Generate realistic music metadata for this track:
Title: {title}
Artist: {artist}

Include: genre, subgenre, mood (list), tempo (BPM), key, time_signature, era, cultural_origin,
instrumentation (list), duration (seconds), energy_level (0-1), danceability (0-1).

Respond with JSON matching this schema."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a music metadata expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400,
                response_format={"type": "json_object"}
            )

            metadata = json.loads(response.choices[0].message.content)

            logger.debug(f"Generated metadata for '{title}'")

            return metadata

        except Exception as e:
            logger.exception("Error generating metadata")
            return self._fallback_metadata()

    def augment_dataset(
        self,
        existing_items: List[Dict[str, Any]],
        target_count: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Augment existing dataset by generating variations.

        Args:
            existing_items: List of existing music items
            target_count: Target total number of items

        Returns:
            Augmented list of music items
        """
        if len(existing_items) >= target_count:
            return existing_items[:target_count]

        augmented = existing_items.copy()
        needed = target_count - len(existing_items)

        logger.info(f"Augmenting dataset from {len(existing_items)} to {target_count} items")

        # Generate new items based on existing ones
        for i in range(needed):
            # Pick a random template
            template = random.choice(existing_items)

            # Generate variation
            # This is simplified - in practice, you'd use LLM to create variations
            new_item = self._create_variation(template, i)
            augmented.append(new_item)

        logger.info(f"Dataset augmented to {len(augmented)} items")

        return augmented

    def _create_variation(self, template: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Create a variation of an existing item."""
        # This is a simple placeholder - ideally use LLM for more realistic variations
        new_item = template.copy()
        new_item['id'] = f"{template.get('id', 'item')}_var_{index}"
        new_item['title'] = f"{template.get('title', 'Track')} (Variation {index})"

        return new_item

    def _fallback_queries(self, count: int) -> List[Dict[str, Any]]:
        """Fallback queries when generation fails."""
        templates = [
            {"query": "upbeat dance music", "intent": "mood-based", "expected_genres": ["Pop", "Electronic"], "expected_moods": ["happy", "energetic"], "complexity": "simple"},
            {"query": "relaxing classical piano", "intent": "mood-based", "expected_genres": ["Classical"], "expected_moods": ["calm", "meditative"], "complexity": "simple"},
            {"query": "intense rock with powerful drums", "intent": "genre-exploration", "expected_genres": ["Rock"], "expected_moods": ["energetic", "powerful"], "complexity": "medium"},
            {"query": "jazz fusion from the 1970s", "intent": "discovery", "expected_genres": ["Jazz"], "expected_moods": ["sophisticated"], "complexity": "complex"},
            {"query": "world music with traditional instruments", "intent": "genre-exploration", "expected_genres": ["World Music"], "expected_moods": ["cultural"], "complexity": "medium"},
        ]

        # Repeat templates to reach count
        queries = []
        while len(queries) < count:
            queries.extend(templates)

        return queries[:count]

    def _fallback_metadata(self) -> Dict[str, Any]:
        """Fallback metadata."""
        return {
            "genre": "Pop",
            "mood": ["neutral"],
            "tempo": 120.0,
            "key": "C major",
            "era": "2020s"
        }
