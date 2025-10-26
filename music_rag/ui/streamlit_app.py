"""Streamlit Analytics Dashboard for Music RAG.

Provides system monitoring, analytics, evaluation metrics, and admin interface.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, List, Dict, Any
import logging
import os
import sys
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from music_rag.cli import MusicRAGSystem
from music_rag.config import settings
from music_rag.src.models.music_item import MusicItem, RetrievalQuery

logger = logging.getLogger(__name__)


# Page configuration
st.set_page_config(
    page_title="Music RAG Dashboard",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize session state variables."""
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = None
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    if 'query_log' not in st.session_state:
        st.session_state.query_log = []


def load_rag_system(db_path: str):
    """Load or get RAG system."""
    if st.session_state.rag_system is None or getattr(st.session_state.rag_system, 'db_path', None) != db_path:
        with st.spinner("Loading Music RAG system..."):
            st.session_state.rag_system = MusicRAGSystem(db_path=db_path)
    return st.session_state.rag_system


def home_page():
    """Home page with quick search and overview."""
    st.title("🎵 Music RAG Dashboard")
    st.markdown("AI-Powered Music Discovery & Retrieval System")

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        db_path = st.text_input("Database Path", value="./data/chromadb")

        if st.button("🔄 Reload System"):
            st.session_state.rag_system = None
            load_rag_system(db_path)
            st.success("System reloaded!")

    # Load system
    rag_system = load_rag_system(db_path)

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        try:
            stats = rag_system.get_stats()
            st.metric("Text Embeddings", stats.get('text_embeddings_count', 0))
        except:
            st.metric("Text Embeddings", "N/A")

    with col2:
        try:
            stats = rag_system.get_stats()
            st.metric("Audio Embeddings", stats.get('audio_embeddings_count', 0))
        except:
            st.metric("Audio Embeddings", "N/A")

    with col3:
        st.metric("Searches Today", len(st.session_state.search_history))

    with col4:
        st.metric("Total Queries", len(st.session_state.query_log))

    st.divider()

    # Quick search
    st.header("🔍 Quick Search")

    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_input("Search for music", placeholder="e.g., upbeat dance music")

    with col2:
        top_k = st.number_input("Results", min_value=1, max_value=50, value=10)

    if st.button("Search", type="primary"):
        if query:
            with st.spinner("Searching..."):
                try:
                    retrieval_query = RetrievalQuery(
                        text_query=query,
                        top_k=top_k
                    )
                    results = rag_system.search(retrieval_query)

                    # Log query
                    st.session_state.query_log.append({
                        'timestamp': datetime.now(),
                        'query': query,
                        'results_count': len(results)
                    })
                    st.session_state.search_history.append(query)

                    # Display results
                    if results:
                        st.success(f"Found {len(results)} results")

                        # Convert to DataFrame
                        rows = []
                        for result in results:
                            metadata = result.music_item.metadata
                            rows.append({
                                'Title': result.music_item.title,
                                'Artist': result.music_item.artist,
                                'Genre': metadata.genre or 'N/A',
                                'Mood': ', '.join(metadata.mood) if metadata.mood else 'N/A',
                                'Tempo': metadata.tempo or 'N/A',
                                'Score': f"{result.score:.3f}",
                                'Type': result.retrieval_type
                            })

                        df = pd.DataFrame(rows)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.warning("No results found")

                except Exception as e:
                    st.error(f"Search error: {str(e)}")
        else:
            st.warning("Please enter a search query")


def analytics_page():
    """Analytics page with query patterns and performance metrics."""
    st.title("📊 Analytics")

    if not st.session_state.query_log:
        st.info("No queries logged yet. Perform some searches to see analytics.")
        return

    # Convert query log to DataFrame
    df = pd.DataFrame(st.session_state.query_log)

    # Time range selector
    col1, col2 = st.columns(2)
    with col1:
        days_back = st.slider("Days to analyze", 1, 30, 7)

    cutoff_date = datetime.now() - timedelta(days=days_back)
    df_filtered = df[df['timestamp'] >= cutoff_date]

    # Metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Queries", len(df_filtered))

    with col2:
        avg_results = df_filtered['results_count'].mean() if not df_filtered.empty else 0
        st.metric("Avg Results per Query", f"{avg_results:.1f}")

    with col3:
        queries_per_day = len(df_filtered) / days_back
        st.metric("Queries per Day", f"{queries_per_day:.1f}")

    st.divider()

    # Query frequency over time
    st.subheader("Query Activity Over Time")

    if not df_filtered.empty:
        df_filtered['date'] = df_filtered['timestamp'].dt.date
        daily_counts = df_filtered.groupby('date').size().reset_index(name='count')

        fig = px.line(daily_counts, x='date', y='count', title='Queries per Day')
        st.plotly_chart(fig, use_container_width=True)

    # Popular queries
    st.subheader("Most Common Queries")

    if not df_filtered.empty:
        query_counts = df_filtered['query'].value_counts().head(10)
        fig = px.bar(
            x=query_counts.index,
            y=query_counts.values,
            labels={'x': 'Query', 'y': 'Count'},
            title='Top 10 Queries'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # Results distribution
    st.subheader("Results Distribution")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.histogram(
            df_filtered,
            x='results_count',
            title='Distribution of Results Count',
            labels={'results_count': 'Number of Results'}
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Query length distribution
        df_filtered['query_length'] = df_filtered['query'].str.len()
        fig = px.box(
            df_filtered,
            y='query_length',
            title='Query Length Distribution',
            labels={'query_length': 'Characters'}
        )
        st.plotly_chart(fig, use_container_width=True)


def database_page():
    """Database management page."""
    st.title("💾 Database Management")

    db_path = st.text_input("Database Path", value="./data/chromadb")
    rag_system = load_rag_system(db_path)

    # Database stats
    st.subheader("Database Statistics")

    try:
        stats = rag_system.get_stats()

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Text Embeddings", stats.get('text_embeddings_count', 0))

        with col2:
            st.metric("Audio Embeddings", stats.get('audio_embeddings_count', 0))
    except Exception as e:
        st.error(f"Error getting stats: {e}")

    st.divider()

    # Indexing section
    st.subheader("📥 Index New Music")

    with st.form("index_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Title")
            artist = st.text_input("Artist")
            description = st.text_area("Description")

        with col2:
            genre = st.text_input("Genre")
            mood = st.text_input("Mood (comma-separated)")
            tempo = st.number_input("Tempo (BPM)", min_value=0.0, value=120.0)

        submit = st.form_submit_button("Index Music Item")

        if submit and title and artist:
            try:
                # Create music item
                from music_rag.src.models.music_item import MusicMetadata

                metadata = MusicMetadata(
                    genre=genre if genre else None,
                    mood=mood.split(',') if mood else [],
                    tempo=tempo if tempo > 0 else None
                )

                item = MusicItem(
                    id=f"{artist}_{title}".replace(' ', '_').lower(),
                    title=title,
                    artist=artist,
                    description=description,
                    metadata=metadata
                )

                # Index
                rag_system.index_music_items([item])
                st.success(f"✅ Indexed: {title} by {artist}")

            except Exception as e:
                st.error(f"Error indexing: {e}")


def evaluation_page():
    """Evaluation and metrics page."""
    st.title("🎯 Evaluation & Metrics")

    st.markdown("""
    This page provides tools for evaluating the RAG system's performance.
    """)

    # Test queries section
    st.subheader("Run Test Queries")

    test_queries = [
        "upbeat dance music",
        "relaxing classical piano",
        "energetic rock with drums",
        "meditative spiritual music",
        "jazz from the 1970s"
    ]

    if st.button("Run Test Suite"):
        with st.spinner("Running test queries..."):
            results_summary = []

            rag_system = st.session_state.rag_system
            if not rag_system:
                st.error("RAG system not initialized")
                return

            for query in test_queries:
                try:
                    retrieval_query = RetrievalQuery(text_query=query, top_k=5)
                    results = rag_system.search(retrieval_query)

                    results_summary.append({
                        'Query': query,
                        'Results': len(results),
                        'Avg Score': sum(r.score for r in results) / len(results) if results else 0,
                        'Status': '✅ Success'
                    })
                except Exception as e:
                    results_summary.append({
                        'Query': query,
                        'Results': 0,
                        'Avg Score': 0,
                        'Status': f'❌ Error: {str(e)[:30]}'
                    })

            df = pd.DataFrame(results_summary)
            st.dataframe(df, use_container_width=True)

            # Summary metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                success_rate = (df['Results'] > 0).sum() / len(df) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")

            with col2:
                avg_results = df['Results'].mean()
                st.metric("Avg Results", f"{avg_results:.1f}")

            with col3:
                avg_score = df['Avg Score'].mean()
                st.metric("Avg Score", f"{avg_score:.3f}")

    st.divider()

    # Metrics explanation
    st.subheader("📈 Evaluation Metrics")

    st.markdown("""
    ### Key Metrics for RAG Systems:

    - **Precision@K**: % of retrieved items that are relevant
    - **Recall@K**: % of relevant items that were retrieved
    - **MRR (Mean Reciprocal Rank)**: Average of 1/rank of first relevant item
    - **nDCG@K**: Normalized Discounted Cumulative Gain (considers ranking quality)
    - **Context Relevance**: How relevant are retrieved items to the query
    - **Answer Quality**: Overall quality of the retrieval results
    """)


def settings_page():
    """Settings and configuration page."""
    st.title("⚙️ Settings")

    st.subheader("System Configuration")

    # Display current settings
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Embeddings")
        st.info(f"**Text Model**: {settings.text_model}")
        st.info(f"**Audio Sample Rate**: {settings.audio_sample_rate} Hz")
        st.info(f"**Audio MFCCs**: {settings.audio_n_mfcc}")

    with col2:
        st.markdown("### Retrieval")
        st.info(f"**Default Top-K**: {settings.default_top_k}")
        st.info(f"**Semantic Weight**: {settings.default_semantic_weight}")
        st.info(f"**Max Batch Size**: {settings.max_batch_size}")

    st.divider()

    st.subheader("Database Configuration")

    st.info(f"**ChromaDB Path**: {settings.chromadb_path}")
    st.info(f"**Environment**: {settings.environment}")

    st.divider()

    # Export/Import
    st.subheader("📦 Data Export/Import")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Export Query Log"):
            if st.session_state.query_log:
                df = pd.DataFrame(st.session_state.query_log)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"query_log_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No queries to export")

    with col2:
        uploaded_file = st.file_uploader("Import Query Log", type=['csv'])
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                st.session_state.query_log = df.to_dict('records')
                st.success(f"Imported {len(df)} queries")
            except Exception as e:
                st.error(f"Error importing: {e}")


def main():
    """Main app function."""
    # Initialize session state
    init_session_state()

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Home", "Analytics", "Database", "Evaluation", "Settings"]
    )

    # Route to pages
    if page == "Home":
        home_page()
    elif page == "Analytics":
        analytics_page()
    elif page == "Database":
        database_page()
    elif page == "Evaluation":
        evaluation_page()
    elif page == "Settings":
        settings_page()

    # Footer
    st.sidebar.divider()
    st.sidebar.markdown("""
    ---
    ### About
    **Music RAG Dashboard**
    v0.2.0 - Enhanced Edition

    Built with Streamlit + Music RAG
    """)


if __name__ == "__main__":
    main()
