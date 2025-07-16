# 🚀 Streamlit Cloud Deployment Guide

## Prerequisites

1. **GitHub Repository**: Your code should be in a GitHub repository
2. **Streamlit Cloud Account**: Create account at [share.streamlit.io](https://share.streamlit.io)
3. **Mistral AI API Key**: Required for question generation and evaluation

## 📋 Deployment Steps

### Step 1: Prepare Your Repository

1. **Ensure all files are committed to GitHub**:
   ```bash
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Required files for deployment**:
   - ✅ `app.py` (main application file)
   - ✅ `requirements.txt` (dependencies)
   - ✅ `.streamlit/config.toml` (Streamlit configuration)
   - ✅ `README.md` (documentation)

### Step 2: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**:
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account

2. **Create New App**:
   - Click "New app"
   - Select your repository: `atanu0909/book_reading_rag`
   - Branch: `main`
   - Main file path: `app.py`
   - App URL: `book-reading-rag` (or your preferred name)

3. **Configure Secrets**:
   - Go to "Advanced settings"
   - Add the following secrets:
   ```toml
   MISTRAL_API_KEY = "your_actual_mistral_api_key_here"
   DEBUG = "false"
   ```

4. **Deploy**:
   - Click "Deploy!"
   - Wait for deployment to complete

### Step 3: Test Your Deployment

1. **Check Status**: Monitor deployment logs for any errors
2. **Test Functionality**: 
   - Upload a document
   - Generate questions
   - Test audio features
   - Verify AI evaluation

## 🔧 Configuration Files

### requirements.txt
```txt
streamlit>=1.28.0
requests>=2.31.0
python-dotenv>=1.0.0
PyPDF2>=3.0.1
pypdf>=5.8.0
python-docx>=1.1.0
gtts>=2.4.0
speechrecognition>=3.10.0
audio-recorder-streamlit>=0.0.10
pydub>=0.25.1
fpdf2>=2.7.0
pandas>=2.0.0
numpy>=1.21.0
```

### .streamlit/config.toml
```toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = false

[theme]
primaryColor = "#ff6b6b"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

## 🛠️ Troubleshooting

### Common Issues:

1. **Module Not Found Error**:
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version compatibility

2. **API Key Issues**:
   - Verify `MISTRAL_API_KEY` is correctly set in secrets
   - Check API key validity

3. **Audio Features Not Working**:
   - Audio recording may have limitations in cloud environment
   - File upload for audio should work normally

4. **Memory Issues**:
   - Large PDF files may cause memory problems
   - Consider file size limits

### Resource Limits:
- **Memory**: 1GB RAM limit
- **CPU**: Limited processing power
- **Storage**: Temporary files only
- **Network**: External API calls allowed

## 📱 Expected App URL

Your app will be available at:
`https://book-reading-rag.streamlit.app`

## 🔄 Updates

To update your deployed app:
1. Push changes to your GitHub repository
2. Streamlit Cloud will automatically redeploy
3. Monitor deployment logs for issues

## 📧 Support

- **Streamlit Community**: [discuss.streamlit.io](https://discuss.streamlit.io)
- **Documentation**: [docs.streamlit.io](https://docs.streamlit.io)
- **GitHub Issues**: Create issues in your repository

---

🎉 **Happy Deploying!** Your Book RAG system will be live and accessible to users worldwide.
