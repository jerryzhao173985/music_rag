# Music RAG Web Interface

This directory contains the static web interface for Music RAG, deployable to GitHub Pages.

## Features

- Modern, responsive UI built with vanilla HTML/CSS/JavaScript
- Real-time search with the Music RAG API
- Advanced filters (genres, moods, tempo)
- Dual-track retrieval configuration
- Database statistics dashboard
- Dark theme optimized for music discovery

## Quick Start

### Local Development

1. Start the Music RAG API:
   ```bash
   cd ..
   python -m uvicorn music_rag.api:app --reload
   ```

2. Serve the static files:
   ```bash
   cd docs
   python -m http.server 8080
   ```

3. Open http://localhost:8080 in your browser

### GitHub Pages Deployment

This directory is configured to be automatically deployed to GitHub Pages via GitHub Actions.

**Setup:**

1. Enable GitHub Pages in repository settings:
   - Go to **Settings** → **Pages**
   - Set **Source** to **GitHub Actions**

2. The workflow `.github/workflows/deploy-github-pages.yml` will automatically deploy on push to main/master

3. Access your app at: `https://USERNAME.github.io/REPO_NAME/`

## Configuration

### API URL

The app uses `localStorage` to remember your API URL. On first visit, you'll be prompted to enter it.

**To change the default API URL**, edit `index.html` line 298:

```javascript
const API_URL = localStorage.getItem('apiUrl') || 'YOUR_DEFAULT_URL_HERE';
```

### Customization

The app is fully customizable:

- **Colors**: Edit CSS variables in `:root` (lines 10-22)
- **Filters**: Modify `genres` and `moods` arrays in JavaScript (lines 300-301)
- **Features**: Add/remove search options in the HTML

## Architecture

### Files

- `index.html` - Complete single-page application
  - HTML structure
  - CSS styles (embedded)
  - JavaScript application logic

### API Integration

The app communicates with the Music RAG FastAPI backend via REST:

```javascript
// Search endpoint
POST /search
{
  "text_query": "upbeat dance music",
  "top_k": 10,
  "genre_filter": ["Electronic"],
  "mood_filter": ["energetic"],
  "semantic_weight": 0.7
}

// Stats endpoint
GET /stats
```

### State Management

- **API URL**: Stored in `localStorage`
- **Search history**: In-memory (resets on page reload)
- **Filter selections**: DOM state

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Any modern browser with ES6+ support

## CORS Configuration

If your API is on a different domain, ensure CORS is enabled in `music_rag/api.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourusername.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Security

- API keys are supported via `X-API-Key` header (if configured in backend)
- All communication should use HTTPS in production
- No sensitive data is stored client-side

## Performance

- Zero dependencies (no npm, no build step)
- Lightweight (~15KB HTML)
- Fast load times
- Progressive enhancement

## Troubleshooting

### API Connection Failed

**Symptoms:**
- "Search failed: Failed to fetch"
- CORS errors in console

**Solutions:**
1. Verify API is running: `curl http://localhost:8000/health`
2. Check CORS configuration in API
3. Ensure API URL is correct in app

### No Results Found

**Symptoms:**
- Empty results with no errors

**Solutions:**
1. Check database has data: `curl http://localhost:8000/stats`
2. Try broader search terms
3. Remove all filters

### GitHub Pages 404

**Symptoms:**
- Page not found after deployment

**Solutions:**
1. Verify GitHub Pages is enabled in settings
2. Check Actions tab for deployment status
3. Ensure source is set to "GitHub Actions"

## Development

### Adding New Features

1. **New Filter:**
   ```javascript
   // Add to filter arrays
   const instruments = ["Guitar", "Piano", "Drums"];

   // Add HTML in filters section
   // Add to search request body
   ```

2. **New Visualization:**
   ```javascript
   // Add result card styling in CSS
   // Modify displayResults() function
   ```

3. **Analytics:**
   ```javascript
   // Track events in localStorage or send to analytics service
   ```

## License

Same as parent Music RAG project.

## Links

- [Full Documentation](../DEPLOYMENT.md)
- [API Documentation](../README.md)
- [GitHub Repository](https://github.com/YOUR_USERNAME/music_rag)
