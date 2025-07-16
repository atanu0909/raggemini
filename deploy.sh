#!/bin/bash
# Deployment script for Book RAG System

echo "=== Book RAG System Deployment ==="

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements_new.txt

# Set up environment file
echo "Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please edit .env file and add your Mistral API key"
fi

# Run the application
echo "Starting application..."
streamlit run book_rag_app.py

echo "=== Deployment Complete ==="
