# 🚀 Streamlit Cloud Deployment Guide

## Book Question Generator & Assessment System

### Quick Deployment Steps

1. **Repository Setup** ✅
   - Repository: `https://github.com/atanu0909/book_reading_rag`
   - Branch: `main`
   - Main file: `app.py`

2. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select repository: `atanu0909/book_reading_rag`
   - Main file path: `app.py`
   - App URL: Choose your preferred URL

3. **Add Secrets in Streamlit Cloud**
   - In your app dashboard, click "⚙️ Settings"
   - Go to "Secrets" tab
   - Add the following:
   ```toml
   [general]
   MISTRAL_API_KEY = "ELvBe6YSxK0LgKpwnz2qG4nDE0tVhO6r"
   ```

4. **App Features**
   - ✅ PDF/DOCX/TXT file upload
   - ✅ AI-powered question generation (MCQ, 1-5 marks)
   - ✅ Interactive test interface with timer
   - ✅ Audio features (Text-to-Speech, Voice input)
   - ✅ PDF export functionality
   - ✅ Real-time answer evaluation
   - ✅ Comprehensive results dashboard

### Architecture
- **Single-file application** for easy deployment
- **Session state management** for cloud compatibility
- **Graceful fallbacks** for optional features
- **Optimized dependencies** for faster deployment

### Requirements
- Python 3.8+
- Streamlit 1.28.0+
- All dependencies listed in `requirements.txt`

### Local Testing
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Deployment Status
- ✅ Code optimized for cloud deployment
- ✅ Dependencies cleaned and tested
- ✅ Secrets configured
- ✅ Ready for Streamlit Cloud

---

**Deploy URL**: After deployment, your app will be available at:
`https://[your-app-name].streamlit.app`
