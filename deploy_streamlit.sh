#!/bin/bash

# 🚀 Streamlit Cloud Deployment Script
# This script helps prepare your Book RAG system for Streamlit Cloud deployment

echo "📚 Book RAG - Streamlit Cloud Deployment Script"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the project root directory."
    exit 1
fi

echo "✅ Found app.py - proceeding with deployment preparation..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Error: Git repository not initialized. Please initialize git first:"
    echo "   git init"
    echo "   git remote add origin https://github.com/atanu0909/book_reading_rag.git"
    exit 1
fi

echo "✅ Git repository detected..."

# Check for required files
echo "🔍 Checking required files..."

required_files=("requirements.txt" ".streamlit/config.toml" "README.md")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ Missing required files:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    exit 1
fi

echo "✅ All required files present..."

# Check if secrets template exists
if [ ! -f "secrets.toml" ]; then
    echo "⚠️  Warning: secrets.toml not found. You'll need to configure secrets manually in Streamlit Cloud."
else
    echo "✅ Secrets template found..."
fi

# Add all files to git
echo "📝 Adding files to git..."
git add .

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "ℹ️  No changes to commit..."
else
    echo "💾 Committing changes..."
    git commit -m "Prepare for Streamlit Cloud deployment - $(date '+%Y-%m-%d %H:%M:%S')"
fi

# Push to GitHub
echo "🚀 Pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "🎉 Deployment preparation complete!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Go to https://share.streamlit.io"
    echo "2. Sign in with your GitHub account"
    echo "3. Click 'New app'"
    echo "4. Select repository: atanu0909/book_reading_rag"
    echo "5. Branch: main"
    echo "6. Main file path: app.py"
    echo "7. Add your MISTRAL_API_KEY to secrets"
    echo "8. Deploy!"
    echo ""
    echo "📖 For detailed instructions, see: STREAMLIT_CLOUD_DEPLOYMENT.md"
else
    echo "❌ Error pushing to GitHub. Please check your git configuration and try again."
    exit 1
fi
