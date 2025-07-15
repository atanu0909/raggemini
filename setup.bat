@echo off
echo ===============================================
echo Book RAG System Setup Script
echo ===============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo Python is installed. Checking version...
python --version

:: Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv

:: Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install requirements
echo.
echo Installing requirements...
pip install streamlit PyPDF2 python-dotenv requests pydub speechrecognition gtts pandas python-docx Pillow mistralai

:: Create necessary directories
echo.
echo Creating directories...
if not exist "uploads" mkdir uploads
if not exist "data" mkdir data
if not exist "demo_data" mkdir demo_data

:: Display success message
echo.
echo ===============================================
echo Setup completed successfully!
echo ===============================================
echo.
echo To run the application:
echo 1. Activate virtual environment: venv\Scripts\activate.bat
echo 2. Run the app: streamlit run app.py
echo 3. Open your browser and go to the provided URL
echo.
echo To run the demo: python demo.py
echo.
pause
