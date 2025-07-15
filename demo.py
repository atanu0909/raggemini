#!/usr/bin/env python3
"""
Demo script for the Book RAG Question Generation and Assessment System

This script demonstrates the main features of the system:
1. Processing documents
2. Generating questions
3. Evaluating answers
4. Audio features
"""

import os
import sys
import json
from datetime import datetime

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.document_processor import DocumentProcessor
from utils.mistral_api import MistralAPI
from components.question_generator import QuestionGenerator
from components.answer_evaluator import AnswerEvaluator

def demo_document_processing():
    """Demonstrate document processing capabilities"""
    print("=" * 60)
    print("DOCUMENT PROCESSING DEMO")
    print("=" * 60)
    
    processor = DocumentProcessor()
    
    # Create a sample text file for demonstration
    sample_text = """
    Chapter 1: Introduction to Python Programming
    
    Python is a high-level, interpreted programming language known for its simplicity and readability. 
    It was created by Guido van Rossum and first released in 1991. Python's design philosophy emphasizes 
    code readability with its use of significant whitespace.
    
    Key features of Python include:
    - Simple and easy to learn syntax
    - Interpreted language
    - Object-oriented programming support
    - Large standard library
    - Cross-platform compatibility
    
    Python is widely used in web development, data science, artificial intelligence, automation, 
    and many other fields. Its versatility and extensive ecosystem of libraries make it an excellent 
    choice for beginners and experts alike.
    """
    
    # Save sample text to file
    os.makedirs("demo_data", exist_ok=True)
    with open("demo_data/sample_chapter.txt", "w") as f:
        f.write(sample_text)
    
    # Process the document
    print("Processing sample text...")
    extracted_text = processor.extract_text_from_txt("demo_data/sample_chapter.txt")
    print(f"Extracted text length: {len(extracted_text)} characters")
    
    # Split into chapters
    chapters = processor.split_into_chapters(extracted_text)
    print(f"Number of chapters detected: {len(chapters)}")
    
    for chapter_name, content in chapters.items():
        print(f"\nChapter: {chapter_name}")
        print(f"Content length: {len(content)} characters")
        print(f"Preview: {content[:100]}...")

def demo_question_generation():
    """Demonstrate question generation"""
    print("\n" + "=" * 60)
    print("QUESTION GENERATION DEMO")
    print("=" * 60)
    
    # Sample chapter text
    chapter_text = """
    Python is a high-level, interpreted programming language known for its simplicity and readability. 
    It was created by Guido van Rossum and first released in 1991. Python's design philosophy emphasizes 
    code readability with its use of significant whitespace.
    
    Key features of Python include:
    - Simple and easy to learn syntax
    - Interpreted language
    - Object-oriented programming support
    - Large standard library
    - Cross-platform compatibility
    
    Python is widely used in web development, data science, artificial intelligence, automation, 
    and many other fields.
    """
    
    mistral_api = MistralAPI()
    
    print("Generating MCQ questions...")
    try:
        mcq_questions = mistral_api.generate_mcq_questions(chapter_text, num_questions=2)
        print(f"Generated {len(mcq_questions)} MCQ questions")
        
        if mcq_questions:
            for i, q in enumerate(mcq_questions, 1):
                print(f"\nMCQ {i}:")
                print(f"Question: {q.get('question', 'N/A')}")
                print(f"Options: {q.get('options', {})}")
                print(f"Correct Answer: {q.get('correct_answer', 'N/A')}")
    except Exception as e:
        print(f"Error generating MCQ questions: {e}")
    
    print("\nGenerating subjective questions...")
    try:
        subjective_questions = mistral_api.generate_subjective_questions(
            chapter_text, "2_mark", num_questions=1
        )
        print(f"Generated {len(subjective_questions)} subjective questions")
        
        if subjective_questions:
            for i, q in enumerate(subjective_questions, 1):
                print(f"\nSubjective {i}:")
                print(f"Question: {q.get('question', 'N/A')}")
                print(f"Marks: {q.get('marks', 'N/A')}")
                print(f"Key Points: {q.get('key_points', [])}")
    except Exception as e:
        print(f"Error generating subjective questions: {e}")

def demo_answer_evaluation():
    """Demonstrate answer evaluation"""
    print("\n" + "=" * 60)
    print("ANSWER EVALUATION DEMO")
    print("=" * 60)
    
    mistral_api = MistralAPI()
    
    # Sample MCQ evaluation
    mcq_question = {
        "question": "What year was Python first released?",
        "options": {
            "A": "1989",
            "B": "1991",
            "C": "1993",
            "D": "1995"
        },
        "correct_answer": "B",
        "explanation": "Python was first released in 1991 by Guido van Rossum."
    }
    
    print("Evaluating MCQ answer...")
    mcq_result = mistral_api.evaluate_mcq_answer(mcq_question, "B")
    print(f"User answer: B")
    print(f"Correct: {mcq_result['correct']}")
    print(f"Score: {mcq_result['score']}/{mcq_result['max_score']}")
    print(f"Feedback: {mcq_result['feedback']}")
    
    # Sample subjective evaluation
    subjective_question = {
        "question": "Explain the key features of Python programming language.",
        "marks": 3,
        "key_points": [
            "Simple and easy to learn syntax",
            "Interpreted language",
            "Object-oriented programming support",
            "Large standard library",
            "Cross-platform compatibility"
        ],
        "sample_answer": "Python has simple syntax, is interpreted, supports OOP, has a large standard library, and is cross-platform."
    }
    
    user_answer = "Python has simple syntax that makes it easy to learn. It is an interpreted language which means code is executed line by line. It supports object-oriented programming and has a large standard library."
    
    print("\nEvaluating subjective answer...")
    print(f"Question: {subjective_question['question']}")
    print(f"User answer: {user_answer}")
    
    try:
        subjective_result = mistral_api.evaluate_subjective_answer(subjective_question, user_answer)
        print(f"Score: {subjective_result['score']}/{subjective_result['max_score']}")
        print(f"Feedback: {subjective_result['feedback']}")
    except Exception as e:
        print(f"Error evaluating subjective answer: {e}")

def demo_system_features():
    """Demonstrate key system features"""
    print("\n" + "=" * 60)
    print("SYSTEM FEATURES DEMONSTRATION")
    print("=" * 60)
    
    features = [
        "✅ Document Processing (PDF, DOCX, TXT)",
        "✅ Automatic Chapter Detection",
        "✅ MCQ Question Generation",
        "✅ Subjective Question Generation (1, 2, 3, 5 marks)",
        "✅ AI-Powered Answer Evaluation",
        "✅ Detailed Feedback and Scoring",
        "✅ Audio Support (Text-to-Speech)",
        "✅ Voice Answer Input",
        "✅ Test Customization",
        "✅ Question Skipping",
        "✅ Time Tracking",
        "✅ Test History and Analytics",
        "✅ Performance Tracking",
        "✅ Grade Calculation",
        "✅ Detailed Results Export"
    ]
    
    print("Key Features of the Book RAG System:")
    for feature in features:
        print(f"  {feature}")
    
    print("\n" + "=" * 60)
    print("USAGE INSTRUCTIONS")
    print("=" * 60)
    
    instructions = [
        "1. Run the application: streamlit run app.py",
        "2. Navigate to 'Upload & Generate' to upload book chapters",
        "3. Configure question generation settings",
        "4. Generate questions using AI",
        "5. Go to 'Custom Test Setup' to create personalized tests",
        "6. Take tests in 'Take Test' section",
        "7. Use audio features for accessibility",
        "8. Skip questions if needed",
        "9. Get detailed AI feedback on answers",
        "10. View results and track progress",
        "11. Access test history for performance analysis"
    ]
    
    for instruction in instructions:
        print(f"  {instruction}")

def main():
    """Main demo function"""
    print("🚀 BOOK RAG SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    print("\nThis demo showcases the capabilities of the Book RAG system.")
    print("The system helps create and evaluate questions from book chapters.")
    
    # Run demonstrations
    demo_document_processing()
    demo_question_generation()
    demo_answer_evaluation()
    demo_system_features()
    
    print("\n" + "=" * 80)
    print("🎉 DEMO COMPLETED!")
    print("=" * 80)
    
    print("\nTo use the full system, run:")
    print("  streamlit run app.py")
    print("\nThen open your browser and navigate to the provided URL.")
    print("The system will be available at: http://localhost:8501")

if __name__ == "__main__":
    main()
