"""Result explanation and summarization using LLMs.

Provides natural language explanations for why music items were retrieved
and generates insights about the results.
"""

from typing import List, Dict, Optional, Any
import json
import logging
from openai import OpenAI, APIError, APITimeoutError, RateLimitError

logger = logging.getLogger(__name__)


class ResultExplainer:
    """Generate explanations for retrieval results using LLMs."""

    SYSTEM_PROMPT = """You are a music expert helping users understand search results.

Your task is to explain why music tracks were retrieved for a user's query and provide insights.

Analyze the query and top results to provide:
1. **Overall Summary**: Brief summary of what the results have in common
2. **Individual Explanations**: Why each track matches the query
3. **Listening Recommendations**: Suggested listening order or groupings
4. **Musical Insights**: Key signatures, tempo patterns, mood progressions, etc.
5. **Discovery Suggestions**: How to explore further

Be concise, insightful, and music-savvy in your explanations."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize result explainer.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        if not api_key:
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(api_key=api_key, timeout=timeout, max_retries=max_retries)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        logger.info(f"Result explainer initialized with model: {model}")

    def explain_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Generate explanation for search results.

        Args:
            query: Original search query
            results: List of retrieved music items (dicts)
            top_n: Number of top results to explain in detail

        Returns:
            Dict with explanations and insights
        """
        try:
            # Prepare results summary
            results_summary = self._format_results(results[:top_n])

            # Build prompt
            user_message = f"""Query: "{query}"

Top {top_n} Results:
{results_summary}

Please provide:
1. A brief summary of what these results have in common (2-3 sentences)
2. An explanation for each result (1-2 sentences each)
3. A suggested listening order or groupings
4. Musical insights (keys, tempos, moods, cultural themes)
5. Suggestions for further discovery

Format as JSON:
{{
  "summary": "overall summary",
  "explanations": [
    {{"title": "track title", "explanation": "why it matches"}},
    ...
  ],
  "listening_recommendations": "suggested order/groupings",
  "musical_insights": "key patterns and insights",
  "discovery_suggestions": ["suggestion 1", "suggestion 2", ...]
}}"""

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )

            # Parse response
            explanation = json.loads(response.choices[0].message.content)

            logger.info(f"Generated explanations for {len(results)} results")

            return explanation

        except Exception as e:
            logger.exception("Error generating explanations")
            return self._fallback_explanation(query, results)

    def explain_single_result(
        self,
        query: str,
        result: Dict[str, Any]
    ) -> str:
        """
        Generate explanation for a single result.

        Args:
            query: Search query
            result: Music item dict

        Returns:
            Explanation string
        """
        try:
            result_text = self._format_single_result(result)

            user_message = f"""Query: "{query}"

Result:
{result_text}

Explain in 2-3 sentences why this track matches the query, focusing on musical characteristics."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a music expert providing concise explanations."},
                    {"role": "user", "content": user_message}
                ],
                temperature=self.temperature,
                max_tokens=150
            )

            explanation = response.choices[0].message.content.strip()

            return explanation

        except Exception as e:
            logger.exception("Error explaining single result")
            return "This track matches your search criteria."

    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format results for inclusion in prompt."""
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(f"{i}. {self._format_single_result(result)}")

        return "\n\n".join(formatted)

    def _format_single_result(self, result: Dict[str, Any]) -> str:
        """Format a single result."""
        parts = []

        # Basic info
        if 'title' in result:
            parts.append(f"Title: {result['title']}")
        if 'artist' in result:
            parts.append(f"Artist: {result['artist']}")

        # Metadata
        metadata = result.get('metadata', {})
        if metadata:
            if metadata.get('genre'):
                parts.append(f"Genre: {metadata['genre']}")
            if metadata.get('mood'):
                moods = metadata['mood'] if isinstance(metadata['mood'], str) else ', '.join(metadata['mood'])
                parts.append(f"Mood: {moods}")
            if metadata.get('tempo'):
                parts.append(f"Tempo: {metadata['tempo']} BPM")
            if metadata.get('key'):
                parts.append(f"Key: {metadata['key']}")
            if metadata.get('era'):
                parts.append(f"Era: {metadata['era']}")

        # Score if available
        if 'score' in result:
            parts.append(f"Relevance Score: {result['score']:.3f}")

        return " | ".join(parts)

    def _fallback_explanation(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback explanation when LLM fails."""
        return {
            "summary": f"Found {len(results)} tracks matching '{query}'.",
            "explanations": [
                {"title": r.get('title', 'Unknown'), "explanation": "Matches your search criteria"}
                for r in results[:5]
            ],
            "listening_recommendations": "Start with the top results for best matches.",
            "musical_insights": "Various musical styles and characteristics.",
            "discovery_suggestions": ["Try refining your search with genre or mood filters"]
        }


class MusicInsightGenerator:
    """Generate musical insights and recommendations."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize insight generator.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_playlist_insights(
        self,
        tracks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate insights about a collection of tracks.

        Args:
            tracks: List of music items

        Returns:
            Dict with insights about the collection
        """
        try:
            # Extract key metadata
            genres = []
            moods = []
            tempos = []
            keys = []

            for track in tracks:
                metadata = track.get('metadata', {})
                if metadata.get('genre'):
                    genres.append(metadata['genre'])
                if metadata.get('mood'):
                    mood_list = metadata['mood'] if isinstance(metadata['mood'], list) else [metadata['mood']]
                    moods.extend(mood_list)
                if metadata.get('tempo'):
                    tempos.append(metadata['tempo'])
                if metadata.get('key'):
                    keys.append(metadata['key'])

            # Build summary
            summary = {
                "track_count": len(tracks),
                "genres": list(set(genres)),
                "moods": list(set(moods)),
                "avg_tempo": sum(tempos) / len(tempos) if tempos else None,
                "tempo_range": (min(tempos), max(tempos)) if tempos else None,
                "keys": list(set(keys))
            }

            # Generate insights using LLM
            prompt = f"""Analyze this music collection and provide insights:

Track Count: {summary['track_count']}
Genres: {', '.join(summary['genres'])}
Moods: {', '.join(summary['moods'])}
Average Tempo: {summary['avg_tempo']:.1f if summary['avg_tempo'] else 'N/A'} BPM
Keys: {', '.join(summary['keys'])}

Provide:
1. Overall vibe/theme of the collection
2. Suggested listening context (workout, study, party, etc.)
3. Mood progression suggestions
4. Key compatibility insights
5. Genre blend analysis

Respond in JSON format."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a music curator and playlist expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            insights = json.loads(response.choices[0].message.content)
            insights['metadata_summary'] = summary

            return insights

        except Exception as e:
            logger.exception("Error generating playlist insights")
            return {
                "track_count": len(tracks),
                "error": str(e)
            }
