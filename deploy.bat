@echo off
REM 🚀 Streamlit Cloud Deployment Script for Windows
REM This script helps prepare your Book RAG system for Streamlit Cloud deployment

echo 📚 Book RAG - Streamlit Cloud Deployment Script
echo ==============================================

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ Error: app.py not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

echo ✅ Found app.py - proceeding with deployment preparation...

REM Check if git is initialized
if not exist ".git" (
    echo ❌ Error: Git repository not initialized. Please initialize git first:
    echo    git init
    echo    git remote add origin https://github.com/atanu0909/book_reading_rag.git
    pause
    exit /b 1
)

echo ✅ Git repository detected...

REM Check for required files
echo 🔍 Checking required files...

set missing_files=0

if not exist "requirements.txt" (
    echo ❌ Missing: requirements.txt
    set missing_files=1
)

if not exist ".streamlit\config.toml" (
    echo ❌ Missing: .streamlit\config.toml
    set missing_files=1
)

if not exist "README.md" (
    echo ❌ Missing: README.md
    set missing_files=1
)

if %missing_files%==1 (
    echo ❌ Some required files are missing. Please ensure all files are present.
    pause
    exit /b 1
)

echo ✅ All required files present...

REM Check if secrets template exists
if not exist "secrets.toml" (
    echo ⚠️  Warning: secrets.toml not found. You'll need to configure secrets manually in Streamlit Cloud.
) else (
    echo ✅ Secrets template found...
)

REM Add all files to git
echo 📝 Adding files to git...
git add .

REM Check if there are changes to commit
git diff --cached --quiet >nul 2>&1
if %errorlevel%==0 (
    echo ℹ️  No changes to commit...
) else (
    echo 💾 Committing changes...
    git commit -m "Prepare for Streamlit Cloud deployment - %date% %time%"
)

REM Push to GitHub
echo 🚀 Pushing to GitHub...
git push origin main

if %errorlevel%==0 (
    echo ✅ Successfully pushed to GitHub!
    echo.
    echo 🎉 Deployment preparation complete!
    echo.
    echo 📋 Next steps:
    echo 1. Go to https://share.streamlit.io
    echo 2. Sign in with your GitHub account
    echo 3. Click 'New app'
    echo 4. Select repository: atanu0909/book_reading_rag
    echo 5. Branch: main
    echo 6. Main file path: app.py
    echo 7. Add your MISTRAL_API_KEY to secrets
    echo 8. Deploy!
    echo.
    echo 📖 For detailed instructions, see: STREAMLIT_CLOUD_DEPLOYMENT.md
) else (
    echo ❌ Error pushing to GitHub. Please check your git configuration and try again.
    pause
    exit /b 1
)

echo.
echo Press any key to continue...
pause >nul
