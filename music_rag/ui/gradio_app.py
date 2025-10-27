"""Gradio UI for Music RAG system.

Interactive web interface for music search with text and audio inputs,
query enhancement, result explanations, and user feedback.
"""

import gradio as gr
import pandas as pd
from typing import Optional, List, Tuple, Dict, Any
import logging
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from music_rag.cli import MusicRAGSystem
from music_rag.config import settings
from music_rag.src.models.music_item import RetrievalQuery

# Optional imports (only if available)
try:
    from music_rag.src.llm.query_enhancer import OpenAIQueryEnhancer
    from music_rag.src.llm.result_explainer import ResultExplainer
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logging.warning("OpenAI LLM modules not available. Install 'openai' package to enable query enhancement and explanations.")

try:
    from music_rag.src.retrieval.reranker import MusicCrossEncoderReranker
    HAS_RERANKER = True
except ImportError:
    HAS_RERANKER = False
    logging.warning("Reranker module not available. Install sentence-transformers to enable reranking.")

logger = logging.getLogger(__name__)


class MusicRAGUI:
    """Gradio UI for Music RAG."""

    def __init__(
        self,
        db_path: str = "./data/chromadb",
        openai_api_key: Optional[str] = None,
        enable_reranking: bool = False,
        enable_explanations: bool = False
    ):
        """
        Initialize UI.

        Args:
            db_path: Path to ChromaDB database
            openai_api_key: Optional OpenAI API key for enhancements
            enable_reranking: Enable cross-encoder reranking
            enable_explanations: Enable LLM-based result explanations
        """
        logger.info("Initializing Music RAG UI...")

        # Initialize RAG system
        self.rag_system = MusicRAGSystem(db_path=db_path)

        # Optional components
        self.query_enhancer = None
        self.result_explainer = None
        self.reranker = None

        if openai_api_key and HAS_OPENAI:
            logger.info("Enabling OpenAI enhancements")
            if enable_explanations:
                self.query_enhancer = OpenAIQueryEnhancer(api_key=openai_api_key)
                self.result_explainer = ResultExplainer(api_key=openai_api_key)

        if enable_reranking and HAS_RERANKER:
            logger.info("Enabling cross-encoder reranking")
            self.reranker = MusicCrossEncoderReranker()

        # Session state
        self.search_history = []

        logger.info("Music RAG UI initialized successfully")

    def search(
        self,
        text_query: str,
        audio_file: Optional[str],
        top_k: int,
        genres: List[str],
        moods: List[str],
        tempo_min: Optional[float],
        tempo_max: Optional[float],
        use_broad: bool,
        use_targeted: bool,
        semantic_weight: float,
        enable_query_enhancement: bool,
        enable_rerank: bool
    ) -> Tuple[pd.DataFrame, str, str]:
        """
        Perform music search.

        Returns:
            (results_df, explanation_html, enhanced_query_text)
        """
        try:
            # Validate inputs
            if not text_query and not audio_file:
                return (
                    pd.DataFrame(),
                    "<p style='color: red;'>Please provide either a text query or audio file.</p>",
                    ""
                )

            # Query enhancement
            enhanced_info = ""
            search_query = text_query

            if enable_query_enhancement and text_query and self.query_enhancer:
                try:
                    enhanced = self.query_enhancer.enhance_query(text_query)
                    enhanced_info = self._format_enhanced_query(enhanced)

                    # Use enhanced query
                    search_query = enhanced['enhanced_query']

                    # Update filters with suggestions
                    if enhanced.get('suggested_filters'):
                        suggested = enhanced['suggested_filters']
                        if suggested.get('genre_filter') and not genres:
                            genres = suggested['genre_filter']
                        if suggested.get('mood_filter') and not moods:
                            moods = suggested['mood_filter']

                except Exception as e:
                    logger.exception("Query enhancement failed")

            # Build query
            query = RetrievalQuery(
                text_query=search_query if text_query else None,
                audio_path=audio_file if audio_file else None,
                top_k=top_k * 2 if enable_rerank else top_k,  # Get more for reranking
                genre_filter=genres if genres else None,
                mood_filter=moods if moods else None,
                tempo_range=(tempo_min, tempo_max) if tempo_min and tempo_max else None,
                use_broad_retrieval=use_broad,
                use_targeted_retrieval=use_targeted,
                semantic_weight=semantic_weight
            )

            # Search
            results = self.rag_system.search(query)

            # Rerank if enabled
            if enable_rerank and self.reranker and results:
                try:
                    # Convert results to dicts
                    result_dicts = [self._result_to_dict(r) for r in results]

                    # Rerank
                    reranked = self.reranker.rerank_music_items(
                        query=search_query,
                        music_items=result_dicts,
                        top_k=top_k
                    )

                    # Update results
                    results = reranked[:top_k]

                except Exception as e:
                    logger.exception("Reranking failed")
                    results = results[:top_k]
            else:
                results = results[:top_k]

            # Generate explanations
            explanation_html = ""
            if self.result_explainer and results:
                try:
                    result_dicts = [self._result_to_dict(r) for r in results]
                    explanations = self.result_explainer.explain_results(
                        query=search_query,
                        results=result_dicts,
                        top_n=min(5, len(results))
                    )
                    explanation_html = self._format_explanations(explanations)
                except Exception as e:
                    logger.exception("Explanation generation failed")

            # Convert to DataFrame
            if results:
                df = self._results_to_dataframe(results)

                # Add to history
                self.search_history.append({
                    'query': text_query or 'Audio query',
                    'results_count': len(results)
                })

                return df, explanation_html, enhanced_info
            else:
                return (
                    pd.DataFrame(),
                    "<p>No results found. Try broadening your search.</p>",
                    enhanced_info
                )

        except Exception as e:
            logger.exception("Search error")
            return (
                pd.DataFrame(),
                f"<p style='color: red;'>Error: {str(e)}</p>",
                ""
            )

    def _result_to_dict(self, result) -> Dict[str, Any]:
        """Convert result object to dict."""
        if isinstance(result, dict):
            return result

        # Handle QueryResult object
        item_dict = {
            'id': result.music_item.id,
            'title': result.music_item.title,
            'artist': result.music_item.artist,
            'description': result.music_item.description,
            'metadata': result.music_item.metadata.model_dump() if hasattr(result.music_item.metadata, 'model_dump') else result.music_item.metadata,
            'score': result.score,
            'retrieval_type': result.retrieval_type
        }

        return item_dict

    def _results_to_dataframe(self, results: List) -> pd.DataFrame:
        """Convert results to pandas DataFrame."""
        rows = []

        for result in results:
            if isinstance(result, dict):
                # Already a dict (from reranking)
                metadata = result.get('metadata', {})
                rows.append({
                    'Title': result.get('title', 'Unknown'),
                    'Artist': result.get('artist', 'Unknown'),
                    'Genre': metadata.get('genre', 'N/A'),
                    'Mood': ', '.join(metadata.get('mood', [])) if isinstance(metadata.get('mood'), list) else metadata.get('mood', 'N/A'),
                    'Tempo (BPM)': metadata.get('tempo', 'N/A'),
                    'Era': metadata.get('era', 'N/A'),
                    'Score': f"{result.get('score', 0):.3f}",
                    'Type': result.get('retrieval_type', 'N/A')
                })
            else:
                # QueryResult object
                metadata = result.music_item.metadata
                rows.append({
                    'Title': result.music_item.title,
                    'Artist': result.music_item.artist,
                    'Genre': metadata.genre or 'N/A',
                    'Mood': ', '.join(metadata.mood) if metadata.mood else 'N/A',
                    'Tempo (BPM)': metadata.tempo or 'N/A',
                    'Era': metadata.era or 'N/A',
                    'Score': f"{result.score:.3f}",
                    'Type': result.retrieval_type
                })

        return pd.DataFrame(rows)

    def _format_enhanced_query(self, enhanced: Dict[str, Any]) -> str:
        """Format enhanced query info as HTML."""
        html = f"""
        <div style='background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 10px 0;'>
            <h4 style='margin-top: 0;'>🎵 Query Enhancement</h4>
            <p><strong>Intent:</strong> {enhanced.get('intent', 'N/A')}</p>
            <p><strong>Enhanced Query:</strong> <em>{enhanced.get('enhanced_query', 'N/A')}</em></p>
            <p><strong>Strategy:</strong> {enhanced.get('search_strategy', 'hybrid')}</p>
        </div>
        """
        return html

    def _format_explanations(self, explanations: Dict[str, Any]) -> str:
        """Format explanations as HTML."""
        html = f"""
        <div style='background: #fff5ee; padding: 15px; border-radius: 5px; margin: 10px 0;'>
            <h4 style='margin-top: 0;'>💡 Results Explained</h4>

            <h5>Summary</h5>
            <p>{explanations.get('summary', 'N/A')}</p>

            <h5>Musical Insights</h5>
            <p>{explanations.get('musical_insights', 'N/A')}</p>

            <h5>Listening Recommendations</h5>
            <p>{explanations.get('listening_recommendations', 'N/A')}</p>
        </div>
        """
        return html

    def get_stats(self) -> str:
        """Get database statistics."""
        try:
            stats = self.rag_system.db.get_stats()
            return f"""
            <div style='padding: 10px; background: #e8f5e9; border-radius: 5px;'>
                <h4>📊 Database Statistics</h4>
                <p><strong>Text Embeddings:</strong> {stats.get('text_embeddings_count', 0)}</p>
                <p><strong>Audio Embeddings:</strong> {stats.get('audio_embeddings_count', 0)}</p>
                <p><strong>Searches Today:</strong> {len(self.search_history)}</p>
            </div>
            """
        except Exception:
            logger.exception("Error getting stats")
            return "<p style='color: red;'>Error loading statistics</p>"


def create_interface(
    db_path: str = "./data/chromadb",
    openai_api_key: Optional[str] = None
) -> gr.Blocks:
    """
    Create Gradio interface.

    Args:
        db_path: Path to ChromaDB
        openai_api_key: Optional OpenAI API key

    Returns:
        Gradio Blocks interface
    """
    # Initialize UI
    ui = MusicRAGUI(
        db_path=db_path,
        openai_api_key=openai_api_key or os.getenv('OPENAI_API_KEY'),
        enable_reranking=True,
        enable_explanations=bool(openai_api_key or os.getenv('OPENAI_API_KEY'))
    )

    # Define interface
    with gr.Blocks(title="Music RAG - AI Music Discovery", theme=gr.themes.Soft()) as app:
        gr.Markdown("""
        # 🎵 Music RAG - AI-Powered Music Discovery

        Search for music using natural language or audio examples. Powered by advanced RAG with multimodal embeddings.
        """)

        with gr.Row():
            with gr.Column(scale=2):
                # Search inputs
                gr.Markdown("### Search")

                text_input = gr.Textbox(
                    label="What music are you looking for?",
                    placeholder="e.g., upbeat electronic dance music with female vocals",
                    lines=2
                )

                audio_input = gr.Audio(
                    label="Or upload a reference track (optional)",
                    type="filepath"
                )

                with gr.Row():
                    top_k_slider = gr.Slider(
                        minimum=1,
                        maximum=50,
                        value=10,
                        step=1,
                        label="Number of Results"
                    )

                    semantic_weight_slider = gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=0.7,
                        step=0.1,
                        label="Text vs Audio Weight"
                    )

                # Filters
                with gr.Accordion("🎚️ Filters (optional)", open=False):
                    genre_check = gr.CheckboxGroup(
                        choices=["Pop", "Rock", "Jazz", "Classical", "Electronic", "Hip Hop", "World Music", "Latin", "R&B", "Country"],
                        label="Genres"
                    )

                    mood_check = gr.CheckboxGroup(
                        choices=["happy", "sad", "energetic", "calm", "dark", "uplifting", "romantic", "aggressive", "meditative", "triumphant"],
                        label="Moods"
                    )

                    with gr.Row():
                        tempo_min = gr.Number(label="Min BPM", value=None, precision=0)
                        tempo_max = gr.Number(label="Max BPM", value=None, precision=0)

                # Advanced options
                with gr.Accordion("⚙️ Advanced Options", open=False):
                    use_broad_check = gr.Checkbox(label="Use Broad Retrieval", value=True)
                    use_targeted_check = gr.Checkbox(label="Use Targeted Retrieval", value=True)
                    enable_enhancement_check = gr.Checkbox(label="Enable Query Enhancement (requires OpenAI)", value=bool(openai_api_key))
                    enable_rerank_check = gr.Checkbox(label="Enable Reranking", value=False)

                # Search button
                search_btn = gr.Button("🔍 Search", variant="primary", size="lg")

            with gr.Column(scale=1):
                # Stats
                gr.Markdown("### System Info")
                stats_html = gr.HTML(ui.get_stats())
                refresh_stats_btn = gr.Button("🔄 Refresh Stats")

        # Results section
        gr.Markdown("### Results")

        with gr.Tabs():
            with gr.Tab("📊 Results Table"):
                results_df = gr.Dataframe(
                    label="Search Results",
                    headers=["Title", "Artist", "Genre", "Mood", "Tempo (BPM)", "Era", "Score", "Type"],
                    interactive=False
                )

            with gr.Tab("💡 Explanations"):
                explanation_html = gr.HTML(label="Why these results?")

            with gr.Tab("🎯 Enhanced Query"):
                enhanced_query_html = gr.HTML(label="Query Analysis")

        # Connect components
        search_btn.click(
            fn=ui.search,
            inputs=[
                text_input,
                audio_input,
                top_k_slider,
                genre_check,
                mood_check,
                tempo_min,
                tempo_max,
                use_broad_check,
                use_targeted_check,
                semantic_weight_slider,
                enable_enhancement_check,
                enable_rerank_check
            ],
            outputs=[results_df, explanation_html, enhanced_query_html]
        )

        refresh_stats_btn.click(
            fn=ui.get_stats,
            inputs=[],
            outputs=[stats_html]
        )

        # Examples
        gr.Examples(
            examples=[
                ["upbeat electronic dance music", None, 10, [], [], None, None, True, True, 0.7, False, False],
                ["meditative spiritual music", None, 10, ["Indian Classical"], ["meditative", "serene"], None, None, True, True, 0.7, False, False],
                ["powerful orchestral symphony", None, 10, ["Classical"], ["triumphant", "powerful"], None, None, True, True, 0.7, False, False],
                ["relaxing jazz for late night listening", None, 10, ["Jazz"], ["calm", "sophisticated"], 60, 100, True, True, 0.7, False, False],
            ],
            inputs=[
                text_input,
                audio_input,
                top_k_slider,
                genre_check,
                mood_check,
                tempo_min,
                tempo_max,
                use_broad_check,
                use_targeted_check,
                semantic_weight_slider,
                enable_enhancement_check,
                enable_rerank_check
            ],
        )

        gr.Markdown("""
        ---
        ### About

        This system uses:
        - **Dual-Track Retrieval**: Combines broad and targeted search strategies
        - **Multimodal Embeddings**: Text and audio understanding
        - **Cross-Encoder Reranking**: Improves precision (optional)
        - **Query Enhancement**: LLM-powered query understanding (requires OpenAI API key)

        Built with ❤️ using Music RAG framework
        """)

    return app


def main():
    """Run Gradio app."""
    import argparse

    parser = argparse.ArgumentParser(description="Music RAG Gradio UI")
    parser.add_argument("--db-path", default="./data/chromadb", help="Path to ChromaDB")
    parser.add_argument("--openai-key", help="OpenAI API key for enhancements")
    parser.add_argument("--share", action="store_true", help="Create shareable link")
    parser.add_argument("--port", type=int, default=7860, help="Port to run on")

    args = parser.parse_args()

    # Create and launch interface
    app = create_interface(
        db_path=args.db_path,
        openai_api_key=args.openai_key
    )

    app.launch(
        server_port=args.port,
        share=args.share
    )


if __name__ == "__main__":
    main()
