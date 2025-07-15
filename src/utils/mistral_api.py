import requests
import json
from typing import Dict, List, Optional
import streamlit as st
from src.config import MISTRAL_API_KEY, MISTRAL_BASE_URL, QUESTION_TYPES, SCORING
from src.utils.fallback_generator import FallbackQuestionGenerator

class MistralAPI:
    """Handles integration with Mistral AI API for question generation and answer evaluation"""
    
    def __init__(self):
        self.api_key = MISTRAL_API_KEY
        self.base_url = MISTRAL_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.fallback_generator = FallbackQuestionGenerator()
    
    def generate_completion(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Generate completion using Mistral API"""
        try:
            # Updated model name for Mistral API
            data = {
                "model": "mistral-small-latest",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                # Better error handling
                error_msg = f"API Error: {response.status_code}"
                if response.status_code == 401:
                    error_msg += " - Invalid API key. Please check your Mistral API key."
                elif response.status_code == 429:
                    error_msg += " - Rate limit exceeded. Please wait and try again."
                else:
                    error_msg += f" - {response.text}"
                
                st.error(error_msg)
                return None
                
        except requests.exceptions.Timeout:
            st.error("Request timed out. Please try again.")
            return None
        except Exception as e:
            st.error(f"Error calling Mistral API: {str(e)}")
            return None
    
    def generate_mcq_questions(self, chapter_text: str, num_questions: int = 5) -> List[Dict]:
        """Generate multiple choice questions from chapter text"""
        prompt = f"""
        Based on the following chapter text, generate {num_questions} multiple choice questions (MCQs).
        Each question should have 4 options (A, B, C, D) with only one correct answer.
        
        Format your response as a JSON array with the following structure:
        [
            {{
                "question": "Question text here?",
                "options": {{
                    "A": "Option A text",
                    "B": "Option B text", 
                    "C": "Option C text",
                    "D": "Option D text"
                }},
                "correct_answer": "A",
                "explanation": "Brief explanation of why this is correct"
            }}
        ]
        
        Chapter text:
        {chapter_text[:2000]}...
        """
        
        response = self.generate_completion(prompt, max_tokens=1500)
        if response:
            try:
                # Extract JSON from response
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            except:
                st.warning("API response parsing failed. Using fallback questions.")
                return self.fallback_generator.generate_sample_mcq_questions(chapter_text, num_questions)
        else:
            st.warning("API request failed. Using fallback questions.")
            return self.fallback_generator.generate_sample_mcq_questions(chapter_text, num_questions)
    
    def generate_subjective_questions(self, chapter_text: str, question_type: str, num_questions: int = 3) -> List[Dict]:
        """Generate subjective questions of specified mark value"""
        marks = SCORING.get(question_type, 1)
        
        prompt = f"""
        Based on the following chapter text, generate {num_questions} subjective questions worth {marks} marks each.
        
        For {marks} mark questions:
        - Questions should be appropriate for the mark value
        - Include expected answer length and key points
        - Provide sample answers for evaluation reference
        
        Format your response as a JSON array:
        [
            {{
                "question": "Question text here?",
                "marks": {marks},
                "expected_length": "Brief description of expected answer length",
                "key_points": ["Key point 1", "Key point 2", "Key point 3"],
                "sample_answer": "Sample answer for reference"
            }}
        ]
        
        Chapter text:
        {chapter_text[:2000]}...
        """
        
        response = self.generate_completion(prompt, max_tokens=1500)
        if response:
            try:
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            except:
                st.warning("API response parsing failed. Using fallback questions.")
                return self.fallback_generator.generate_sample_subjective_questions(chapter_text, question_type, num_questions)
        else:
            st.warning("API request failed. Using fallback questions.")
            return self.fallback_generator.generate_sample_subjective_questions(chapter_text, question_type, num_questions)
    
    def evaluate_mcq_answer(self, question: Dict, user_answer: str) -> Dict:
        """Evaluate MCQ answer"""
        correct = user_answer.upper() == question['correct_answer'].upper()
        return {
            'correct': correct,
            'score': 1 if correct else 0,
            'max_score': 1,
            'feedback': question.get('explanation', 'No explanation available')
        }
    
    def evaluate_subjective_answer(self, question: Dict, user_answer: str) -> Dict:
        """Evaluate subjective answer using AI"""
        prompt = f"""
        Evaluate the following student answer against the question and expected key points.
        
        Question: {question['question']}
        Expected Key Points: {question['key_points']}
        Sample Answer: {question['sample_answer']}
        Maximum Marks: {question['marks']}
        
        Student Answer: {user_answer}
        
        Please evaluate and provide:
        1. Score out of {question['marks']} marks
        2. Detailed feedback on what was correct/incorrect
        3. Suggestions for improvement
        
        Format response as JSON:
        {{
            "score": 0-{question['marks']},
            "feedback": "Detailed feedback here",
            "suggestions": "Suggestions for improvement"
        }}
        """
        
        response = self.generate_completion(prompt, max_tokens=800)
        if response:
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                result['max_score'] = question['marks']
                result['correct'] = result['score'] == question['marks']
                return result
            except:
                return {
                    'score': 0,
                    'max_score': question['marks'],
                    'correct': False,
                    'feedback': 'Unable to evaluate answer automatically',
                    'suggestions': 'Please review your answer'
                }
        
        return {
            'score': 0,
            'max_score': question['marks'],
            'correct': False,
            'feedback': 'Evaluation failed',
            'suggestions': 'Please try again'
        }
