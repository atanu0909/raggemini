import streamlit as st
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    st.title("📚 Book RAG System - Simple Demo")
    st.write("This is a simplified version to test basic functionality")
    
    # Test with sample text
    sample_text = """
    Chapter 1: Introduction to Data Science
    Data science is an interdisciplinary field that uses scientific methods, processes, algorithms, and systems to extract knowledge and insights from structured and unstructured data.
    
    Chapter 2: Statistics and Probability
    Statistics is the discipline that concerns the collection, organization, analysis, interpretation, and presentation of data.
    
    Chapter 3: Machine Learning
    Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence.
    """
    
    st.subheader("Sample Text")
    st.text_area("Book Content", sample_text, height=200)
    
    # Question generation options
    st.subheader("Question Generation Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        mcq_count = st.number_input("MCQ Questions", min_value=0, max_value=10, value=2)
        one_mark = st.number_input("1 Mark Questions", min_value=0, max_value=10, value=2)
        
    with col2:
        two_mark = st.number_input("2 Mark Questions", min_value=0, max_value=10, value=2)
        five_mark = st.number_input("5 Mark Questions", min_value=0, max_value=10, value=1)
    
    if st.button("Generate Questions"):
        try:
            from components.question_generator import QuestionGenerator
            from utils.mistral_api import MistralAPI
            
            # Initialize components
            mistral_api = MistralAPI()
            question_generator = QuestionGenerator(mistral_api)
            
            # Generate questions
            with st.spinner("Generating questions..."):
                questions = question_generator.generate_questions(
                    text=sample_text,
                    chapter_title="Sample Chapter",
                    mcq_count=mcq_count,
                    one_mark_count=one_mark,
                    two_mark_count=two_mark,
                    five_mark_count=five_mark
                )
            
            if questions:
                st.success("Questions generated successfully!")
                st.json(questions)
            else:
                st.error("Failed to generate questions")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.write("Falling back to sample questions...")
            
            # Sample fallback questions
            sample_questions = {
                "mcq": [
                    {
                        "question": "What is data science?",
                        "options": ["A) Art", "B) Science", "C) Interdisciplinary field", "D) None"],
                        "answer": "C"
                    }
                ],
                "one_mark": [
                    {"question": "Define statistics.", "answer": "Statistics is the discipline that concerns data collection and analysis."}
                ],
                "two_mark": [
                    {"question": "Explain machine learning.", "answer": "Machine learning is a method of data analysis that automates analytical model building using AI."}
                ],
                "five_mark": [
                    {"question": "Discuss the importance of data science.", "answer": "Data science is important because it helps extract insights from data using scientific methods."}
                ]
            }
            
            st.json(sample_questions)
    
    st.subheader("System Status")
    st.write("✅ Basic Streamlit functionality working")
    
    # Test imports
    try:
        import PyPDF2
        st.write("✅ PyPDF2 imported successfully")
    except ImportError:
        st.write("❌ PyPDF2 not available")
    
    try:
        import pypdf
        st.write("✅ pypdf imported successfully")
    except ImportError:
        st.write("❌ pypdf not available")
    
    try:
        import docx
        st.write("✅ python-docx imported successfully")
    except ImportError:
        st.write("❌ python-docx not available")
    
    try:
        from components.question_generator import QuestionGenerator
        st.write("✅ Question generator imported successfully")
    except ImportError as e:
        st.write(f"❌ Question generator import failed: {str(e)}")

if __name__ == "__main__":
    main()
