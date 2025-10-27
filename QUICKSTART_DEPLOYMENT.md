# Quick Deployment Guide

Get your Music RAG web app live in 5 minutes!

## Option 1: GitHub Pages + Render (Recommended)

### Step 1: Enable GitHub Pages (30 seconds)

1. Go to your repo → **Settings** → **Pages**
2. Set **Source** to **GitHub Actions**
3. Done! Your frontend will deploy automatically

Your site will be at: `https://YOUR_USERNAME.github.io/music_rag/`

### Step 2: Deploy API to Render (3 minutes)

1. Sign up at [render.com](https://render.com) (free)

2. Click **New** → **Web Service**

3. Connect your GitHub repo

4. Render auto-detects `render.yaml` - click **Apply**

5. Add these environment variables in Render:
   ```
   CHROMADB_PATH=/opt/render/project/data/chromadb
   LOG_LEVEL=INFO
   ENVIRONMENT=production
   ```

6. Wait for deployment (2-3 minutes)

Your API will be at: `https://YOUR-APP-NAME.onrender.com`

### Step 3: Connect Frontend to API (10 seconds)

1. Visit your GitHub Pages site
2. When prompted, enter your Render URL
3. Done!

---

## Option 2: Hugging Face Spaces (Even Easier!)

### Deploy Gradio App (2 minutes)

1. Create a Space at [huggingface.co/new-space](https://huggingface.co/new-space)
   - Choose **Gradio** SDK
   - Name it `music-rag`

2. Add GitHub secrets (Settings → Secrets → Actions):
   ```
   HF_TOKEN=<your-hf-token>
   HF_USERNAME=<your-username>
   HF_SPACE_NAME=music-rag
   ```

3. Push to GitHub - auto-deploys!

Your app will be at: `https://huggingface.co/spaces/YOUR_USERNAME/music-rag`

---

## Automated Deployment via GitHub Actions

All three workflows are already set up in `.github/workflows/`:

### Set Up Secrets

Go to repo **Settings** → **Secrets and variables** → **Actions**

Add these secrets:

| Secret | For | Get it from |
|--------|-----|-------------|
| `RENDER_DEPLOY_HOOK_URL` | Auto-deploy API | Render → Settings → Deploy Hook |
| `HF_TOKEN` | Auto-deploy Gradio | HuggingFace → Settings → Tokens |
| `HF_USERNAME` | Auto-deploy Gradio | Your HF username |
| `HF_SPACE_NAME` | Auto-deploy Gradio | Your Space name |

### Trigger Deployment

**Automatic:** Push to `main` or `master` branch

**Manual:**
1. Go to **Actions** tab
2. Select workflow
3. Click **Run workflow**

---

## Verify Deployment

### Check GitHub Pages
```bash
curl https://YOUR_USERNAME.github.io/music_rag/
```

### Check Render API
```bash
curl https://your-app.onrender.com/health
```

Should return:
```json
{"status": "healthy", "version": "0.2.0"}
```

### Check Hugging Face Space
Visit the URL and try a search!

---

## Next Steps

1. **Initialize data:**
   ```bash
   curl -X POST "https://your-app.onrender.com/init-data"
   ```

2. **Test search:**
   Visit your GitHub Pages site and search for "upbeat dance music"

3. **Optional:** Set `OPENAI_API_KEY` in Render/HF Spaces for advanced features

---

## Troubleshooting

**GitHub Pages not loading?**
- Check Actions tab for errors
- Wait 2-3 minutes for first deployment

**API not responding?**
- Render free tier sleeps after inactivity (wakes in ~30 seconds)
- Check Render logs for errors

**CORS errors?**
- Update `music_rag/api.py` with your GitHub Pages URL
- Redeploy API

---

## Need Help?

- [Full Deployment Guide](./DEPLOYMENT.md)
- [API Documentation](./README.md)
- [Create an Issue](https://github.com/YOUR_USERNAME/music_rag/issues)

---

**Happy Deploying! 🚀**
