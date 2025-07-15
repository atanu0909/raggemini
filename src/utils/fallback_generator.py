import streamlit as st
from typing import Dict, List, Optional
import json
import os
from datetime import datetime
import random

class FallbackQuestionGenerator:
    """Fallback question generator that creates sample questions when API is unavailable"""
    
    def generate_sample_mcq_questions(self, chapter_text: str, num_questions: int = 5) -> List[Dict]:
        """Generate sample MCQ questions"""
        sample_questions = []
        
        # Extract some keywords from the text for context
        words = chapter_text.lower().split()
        keywords = [word for word in words if len(word) > 4][:20]
        
        for i in range(min(num_questions, 5)):
            question = {
                "question": f"Sample MCQ Question {i+1} based on the chapter content about {keywords[i] if i < len(keywords) else 'the topic'}?",
                "options": {
                    "A": f"Option A related to {keywords[i] if i < len(keywords) else 'topic'}",
                    "B": f"Option B about {keywords[i+1] if i+1 < len(keywords) else 'concepts'}",
                    "C": f"Option C regarding {keywords[i+2] if i+2 < len(keywords) else 'principles'}",
                    "D": f"Option D concerning {keywords[i+3] if i+3 < len(keywords) else 'methods'}"
                },
                "correct_answer": random.choice(["A", "B", "C", "D"]),
                "explanation": f"This is a sample explanation for question {i+1}."
            }
            sample_questions.append(question)
        
        return sample_questions
    
    def generate_sample_subjective_questions(self, chapter_text: str, question_type: str, num_questions: int = 3) -> List[Dict]:
        """Generate sample subjective questions"""
        sample_questions = []
        
        # Extract some keywords from the text for context
        words = chapter_text.lower().split()
        keywords = [word for word in words if len(word) > 4][:20]
        
        marks = {"1_mark": 1, "2_mark": 2, "3_mark": 3, "5_mark": 5}.get(question_type, 1)
        
        for i in range(min(num_questions, 3)):
            question = {
                "question": f"Sample {marks}-mark question {i+1}: Explain the concept of {keywords[i] if i < len(keywords) else 'the main topic'} discussed in the chapter.",
                "marks": marks,
                "expected_length": f"Expected answer length for {marks} marks: {'Brief' if marks <= 2 else 'Detailed' if marks <= 3 else 'Comprehensive'} explanation",
                "key_points": [
                    f"Key point 1 about {keywords[i] if i < len(keywords) else 'topic'}",
                    f"Key point 2 regarding {keywords[i+1] if i+1 < len(keywords) else 'concepts'}",
                    f"Key point 3 concerning {keywords[i+2] if i+2 < len(keywords) else 'principles'}"
                ],
                "sample_answer": f"Sample answer for {marks}-mark question about {keywords[i] if i < len(keywords) else 'the topic'}. This should cover the key points mentioned above."
            }
            sample_questions.append(question)
        
        return sample_questions
