# 📚 Book RAG - AI-Powered Question Generation & Assessment System

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![Mistral AI](https://img.shields.io/badge/Mistral_AI-FF6B6B?style=for-the-badge&logo=ai&logoColor=white)](https://mistral.ai/)

A comprehensive AI-powered educational assessment system that generates intelligent questions from book chapters and provides automated answer evaluation with voice support.

## 🚀 Live Demo

[**Try the Live Application**](https://book-reading-rag.streamlit.app/) *(Coming soon after deployment)*

## ✨ Features

### � **Document Processing**
- **Multi-format Support**: Upload PDF, DOCX, and TXT files
- **Automatic Chapter Detection**: Intelligently splits content into chapters
- **Text Extraction**: Clean and accurate text processing

### 🎯 **Smart Question Generation**
- **Multiple Question Types**: MCQ, 1-mark, 2-mark, 3-mark, and 5-mark questions
- **AI-Powered Creation**: Uses Mistral AI for contextually relevant questions
- **Customizable Tests**: Choose question types and quantities
- **Batch Generation**: Generate multiple questions efficiently

### 🎤 **Advanced Audio Features**
- **Voice Input**: Record answers using your microphone
- **Text-to-Speech**: Listen to questions being read aloud
- **Speech Recognition**: Automatic conversion of voice to text
- **Audio Controls**: Easy-to-use recording interface

### 🧠 **Intelligent Evaluation**
- **AI-Powered Scoring**: Mistral AI evaluates subjective answers
- **Detailed Feedback**: Comprehensive explanations and suggestions
- **Instant Results**: Real-time answer evaluation
- **Performance Analytics**: Track progress and identify improvement areas

### ⚡ **Enhanced Test Experience**
- **Flexible Navigation**: Skip, revisit, and navigate between questions
- **Time Management**: Configurable test duration with live countdown
- **Progress Tracking**: Visual progress indicators
- **Hint System**: Get hints for challenging questions

### 📊 **Comprehensive Analytics**
- **Performance Metrics**: Detailed scoring and grade calculation
- **Test History**: Track performance over time
- **Result Visualization**: Charts and graphs for better insights
- **Export Options**: Save results for future reference

## 🛠️ Installation

### Option 1: Quick Setup

```bash
# Clone the repository
git clone https://github.com/atanu0909/book_reading_rag.git
cd book_reading_rag

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your Mistral API key

# Run the application
streamlit run app.py
```

### Option 2: Docker Setup *(Coming Soon)*

```bash
# Build and run with Docker
docker build -t book-rag .
docker run -p 8501:8501 book-rag
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
MISTRAL_API_KEY=your_mistral_api_key_here
```

### Streamlit Cloud Deployment

For Streamlit Cloud deployment, add your secrets in the Streamlit Cloud dashboard:

```toml
[general]
MISTRAL_API_KEY = "your_mistral_api_key_here"
```

## 🎮 Usage Guide

### 1. **Upload & Generate Questions**
1. Navigate to "📁 Upload & Generate"
2. Upload your book chapter (PDF/DOCX/TXT)
3. Select chapter if multiple chapters detected
4. Click "Generate Questions" to create question sets

### 2. **Configure Custom Tests**
1. Go to "⚙️ Configure Test"
2. Select your generated question set
3. Choose question types and quantities
4. Set time limits and test parameters
5. Create your custom test

### 3. **Take Interactive Tests**
1. Navigate to "✍️ Take Test"
2. Enter your name and start the test
3. Use audio features:
   - 🔊 Click to listen to questions
   - 🎤 Click to record voice answers
   - ⏭️ Skip difficult questions
   - ❓ Get hints when needed

### 4. **View Results & Analytics**
1. Check "📊 View Results" for detailed feedback
2. Review "📚 Test History" for progress tracking
3. Analyze performance metrics and improvement areas

## 📋 Requirements

### Core Dependencies
- **Python 3.8+**
- **Streamlit 1.28+**
- **Mistral AI API Key**

### Key Libraries
- `streamlit` - Web interface
- `mistralai` - AI question generation and evaluation
- `PyPDF2` - PDF processing
- `python-docx` - Word document handling
- `speechrecognition` - Voice-to-text conversion
- `gtts` - Text-to-speech functionality
- `audio-recorder-streamlit` - Audio recording
- `pandas` - Data processing
- `pydub` - Audio manipulation

## 🏗️ Architecture

```
book_rag/
├── app.py                      # Main Streamlit application
├── src/
│   ├── config.py              # Configuration settings
│   ├── components/
│   │   ├── question_generator.py   # Question generation logic
│   │   └── answer_evaluator.py     # Answer evaluation system
│   └── utils/
│       ├── document_processor.py   # Document handling
│       ├── mistral_api.py          # AI API integration
│       └── audio_processor.py      # Audio processing
├── data/                      # Generated questions and results
├── uploads/                   # Temporary file storage
└── .streamlit/               # Streamlit configuration
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include error handling for robustness
- Test thoroughly before submitting

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Mistral AI** for providing powerful language models
- **Streamlit** for the excellent web framework
- **Google** for speech recognition and text-to-speech services
- **Open Source Community** for various libraries and tools

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/atanu0909/book_reading_rag/issues)
- **Discussions**: [GitHub Discussions](https://github.com/atanu0909/book_reading_rag/discussions)
- **Email**: atanu0909@gmail.com

## 🔮 Roadmap

- [ ] **Multi-language Support**: Support for multiple languages
- [ ] **Advanced Analytics**: ML-powered learning insights
- [ ] **Collaborative Features**: Team-based assessments
- [ ] **Mobile App**: React Native mobile application
- [ ] **API Integration**: RESTful API for external integrations
- [ ] **Offline Mode**: Offline question generation and evaluation

## 📊 Stats

![GitHub stars](https://img.shields.io/github/stars/atanu0909/book_reading_rag?style=social)
![GitHub forks](https://img.shields.io/github/forks/atanu0909/book_reading_rag?style=social)
![GitHub issues](https://img.shields.io/github/issues/atanu0909/book_reading_rag)
![GitHub license](https://img.shields.io/github/license/atanu0909/book_reading_rag)

---

**Made with ❤️ by [Atanu](https://github.com/atanu0909)**

*Transform your learning experience with AI-powered question generation and assessment!*
