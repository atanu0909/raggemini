@echo off
REM Deployment script for Book RAG System (Windows)

echo === Book RAG System Deployment ===

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements_new.txt

REM Set up environment file
echo Setting up environment...
if not exist .env (
    copy .env.example .env
    echo Please edit .env file and add your Mistral API key
)

REM Run the application
echo Starting application...
streamlit run book_rag_app.py

echo === Deployment Complete ===
pause
