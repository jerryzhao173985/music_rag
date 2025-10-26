"""Query enhancement using LLMs for better music retrieval.

Uses GPT-4 or other LLMs to understand user intent, extract implicit metadata,
and reformulate queries for improved retrieval results.
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class QueryEnhancer(ABC):
    """Abstract base class for query enhancement."""

    @abstractmethod
    def enhance_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enhance a user query with additional information.

        Args:
            query: Original user query
            context: Optional conversation context

        Returns:
            Dict with enhanced query information
        """
        pass


class OpenAIQueryEnhancer(QueryEnhancer):
    """Query enhancer using OpenAI GPT models."""

    SYSTEM_PROMPT = """You are a music information retrieval expert helping to enhance search queries.

Your task is to analyze user queries about music and extract:
1. **Intent**: What is the user looking for? (discovery, mood-based, artist similarity, genre exploration, etc.)
2. **Implicit Metadata**: Extract genre hints, era, mood, energy level, cultural origin, etc.
3. **Enhanced Query**: Reformulate the query with music domain knowledge
4. **Suggested Filters**: Recommend metadata filters (genre, mood, tempo_range, cultural_origin)
5. **Alternative Queries**: Provide 2-3 alternative phrasings that might retrieve relevant results

Respond ONLY with valid JSON in this exact format:
{
  "intent": "string describing user intent",
  "implicit_metadata": {
    "genre": "string or null",
    "mood": ["list", "of", "moods"],
    "era": "string or null",
    "cultural_origin": "string or null",
    "energy_level": "low/medium/high or null",
    "tempo": "slow/medium/fast or null"
  },
  "enhanced_query": "reformulated query with richer music terminology",
  "suggested_filters": {
    "genre_filter": ["list", "of", "genres"],
    "mood_filter": ["list", "of", "moods"],
    "tempo_range": [min_bpm, max_bpm] or null,
    "cultural_origin_filter": ["list"] or null
  },
  "alternative_queries": [
    "alternative query 1",
    "alternative query 2",
    "alternative query 3"
  ],
  "search_strategy": "broad/targeted/hybrid",
  "explanation": "brief explanation of the analysis"
}"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 800
    ):
        """
        Initialize OpenAI query enhancer.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use (gpt-4o-mini recommended for cost)
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens in response
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        logger.info(f"OpenAI query enhancer initialized with model: {model}")

    def enhance_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enhance query using GPT-4.

        Args:
            query: Original user query
            context: Optional conversation context

        Returns:
            Dict with enhanced query information
        """
        try:
            # Build user message
            user_message = f"User query: {query}"

            if context:
                # Add conversation history if available
                if 'previous_queries' in context:
                    user_message += f"\n\nPrevious queries: {context['previous_queries']}"
                if 'user_preferences' in context:
                    user_message += f"\n\nUser preferences: {context['user_preferences']}"

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
            result = json.loads(response.choices[0].message.content)

            # Add original query
            result['original_query'] = query

            logger.info(f"Query enhanced: {query} -> {result['enhanced_query']}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response as JSON: {e}")
            return self._fallback_enhancement(query)

        except Exception as e:
            logger.error(f"Error enhancing query with OpenAI: {e}")
            return self._fallback_enhancement(query)

    def _fallback_enhancement(self, query: str) -> Dict[str, Any]:
        """Fallback enhancement when OpenAI fails."""
        return {
            "original_query": query,
            "intent": "general search",
            "implicit_metadata": {},
            "enhanced_query": query,
            "suggested_filters": {},
            "alternative_queries": [],
            "search_strategy": "hybrid",
            "explanation": "Fallback: Using original query without enhancement"
        }

    def batch_enhance(
        self,
        queries: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Enhance multiple queries in batch.

        Args:
            queries: List of queries to enhance
            context: Optional shared context

        Returns:
            List of enhanced query dicts
        """
        results = []
        for query in queries:
            enhanced = self.enhance_query(query, context)
            results.append(enhanced)

        return results


class QueryExpander:
    """Expand queries into multiple sub-queries for better coverage."""

    def __init__(self, enhancer: QueryEnhancer):
        """
        Initialize query expander.

        Args:
            enhancer: QueryEnhancer instance to use
        """
        self.enhancer = enhancer

    def expand_query(self, query: str) -> List[str]:
        """
        Expand a query into multiple related queries.

        Args:
            query: Original query

        Returns:
            List of expanded queries including the original
        """
        # Enhance query to get alternatives
        enhanced = self.enhancer.enhance_query(query)

        # Collect all query variations
        queries = [query]  # Original query

        # Add enhanced query if different
        if enhanced['enhanced_query'] != query:
            queries.append(enhanced['enhanced_query'])

        # Add alternative queries
        if 'alternative_queries' in enhanced:
            queries.extend(enhanced['alternative_queries'])

        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            q_lower = q.lower().strip()
            if q_lower not in seen:
                seen.add(q_lower)
                unique_queries.append(q)

        logger.info(f"Expanded query '{query}' into {len(unique_queries)} variations")

        return unique_queries


class ContextualQueryEnhancer:
    """
    Enhancer that maintains conversation context for multi-turn interactions.
    """

    def __init__(self, base_enhancer: QueryEnhancer, max_history: int = 5):
        """
        Initialize contextual enhancer.

        Args:
            base_enhancer: Base QueryEnhancer to use
            max_history: Maximum number of previous queries to remember
        """
        self.base_enhancer = base_enhancer
        self.max_history = max_history
        self.sessions: Dict[str, Dict] = {}

    def enhance_query(
        self,
        query: str,
        session_id: str = "default",
        user_feedback: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Enhance query with conversation context.

        Args:
            query: Current query
            session_id: Session identifier for context tracking
            user_feedback: Optional feedback on previous results

        Returns:
            Enhanced query dict
        """
        # Get or create session
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'query_history': [],
                'user_preferences': {}
            }

        session = self.sessions[session_id]

        # Update session with feedback
        if user_feedback:
            self._update_preferences(session, user_feedback)

        # Build context
        context = {
            'previous_queries': session['query_history'][-self.max_history:],
            'user_preferences': session['user_preferences']
        }

        # Enhance query with context
        enhanced = self.base_enhancer.enhance_query(query, context)

        # Update history
        session['query_history'].append(query)

        return enhanced

    def _update_preferences(self, session: Dict, feedback: Dict):
        """Update user preferences based on feedback."""
        prefs = session['user_preferences']

        # Track liked genres, moods, etc.
        if 'liked_genres' in feedback:
            prefs.setdefault('preferred_genres', set()).update(feedback['liked_genres'])

        if 'disliked_genres' in feedback:
            prefs.setdefault('avoided_genres', set()).update(feedback['disliked_genres'])

        if 'liked_moods' in feedback:
            prefs.setdefault('preferred_moods', set()).update(feedback['liked_moods'])

        # Convert sets to lists for JSON serialization
        for key in prefs:
            if isinstance(prefs[key], set):
                prefs[key] = list(prefs[key])

    def clear_session(self, session_id: str):
        """Clear a session's context."""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get summary of a session."""
        return self.sessions.get(session_id)
