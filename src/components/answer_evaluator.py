import streamlit as st
from typing import Dict, List, Optional
import json
import pandas as pd
from datetime import datetime
import time
import os
from src.utils.mistral_api import MistralAPI
from src.config import SCORING

class AnswerEvaluator:
    """Enhanced answer evaluation and scoring with detailed feedback"""
    
    def __init__(self):
        self.mistral_api = MistralAPI()
    
    def evaluate_answer(self, question: Dict, user_answer: str, question_type: str, 
                       is_skipped: bool = False) -> Dict:
        """Evaluate user answer with enhanced scoring and feedback"""
        
        if is_skipped:
            return {
                'score': 0,
                'max_score': SCORING.get(question_type, 1),
                'correct': False,
                'feedback': 'Question was skipped.',
                'suggestions': 'Try to attempt all questions for better score.',
                'evaluation_type': 'skipped'
            }
        
        if not user_answer or user_answer.strip() == '':
            return {
                'score': 0,
                'max_score': SCORING.get(question_type, 1),
                'correct': False,
                'feedback': 'No answer provided.',
                'suggestions': 'Please provide an answer.',
                'evaluation_type': 'no_answer'
            }
        
        if question_type == 'mcq':
            return self._evaluate_mcq_answer(question, user_answer)
        else:
            return self._evaluate_subjective_answer(question, user_answer, question_type)
    
    def _evaluate_mcq_answer(self, question: Dict, user_answer: str) -> Dict:
        """Evaluate MCQ answer with detailed feedback"""
        correct_answer = question['correct_answer'].upper()
        user_answer = user_answer.upper()
        
        is_correct = user_answer == correct_answer
        
        result = {
            'score': 1 if is_correct else 0,
            'max_score': 1,
            'correct': is_correct,
            'evaluation_type': 'mcq',
            'correct_answer': correct_answer,
            'user_answer': user_answer
        }
        
        if is_correct:
            result['feedback'] = f"Correct! {question.get('explanation', 'Good job!')}"
            result['suggestions'] = "Well done! Keep up the good work."
        else:
            result['feedback'] = f"Incorrect. The correct answer is {correct_answer}. {question.get('explanation', '')}"
            result['suggestions'] = "Review the topic and try to understand the concepts better."
        
        return result
    
    def _evaluate_subjective_answer(self, question: Dict, user_answer: str, question_type: str) -> Dict:
        """Evaluate subjective answer using enhanced AI evaluation"""
        
        max_marks = SCORING.get(question_type, 1)
        
        # Enhanced evaluation prompt
        evaluation_prompt = f"""
        You are an expert teacher evaluating a student's answer. Please evaluate the following answer carefully and provide detailed feedback.
        
        Question: {question['question']}
        Maximum Marks: {max_marks}
        Expected Key Points: {question.get('key_points', [])}
        Sample Answer: {question.get('sample_answer', 'Not provided')}
        Expected Length: {question.get('expected_length', 'Not specified')}
        
        Student Answer: {user_answer}
        
        Please evaluate based on:
        1. Accuracy of content
        2. Completeness of answer
        3. Clarity of explanation
        4. Relevance to the question
        5. Use of appropriate examples/details
        
        Provide your evaluation in the following JSON format:
        {{
            "score": [0-{max_marks}],
            "accuracy_score": [0-10],
            "completeness_score": [0-10],
            "clarity_score": [0-10],
            "relevance_score": [0-10],
            "detailed_feedback": "Detailed feedback about what was good and what needs improvement",
            "strengths": ["strength1", "strength2"],
            "improvements": ["improvement1", "improvement2"],
            "suggestions": "Specific suggestions for improvement",
            "grade_justification": "Explanation of why this score was given"
        }}
        
        Be fair but thorough in your evaluation.
        """
        
        response = self.mistral_api.generate_completion(evaluation_prompt, max_tokens=1000)
        
        if response:
            try:
                # Extract JSON from response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                evaluation = json.loads(json_str)
                
                # Ensure score is within bounds
                score = max(0, min(evaluation.get('score', 0), max_marks))
                
                return {
                    'score': score,
                    'max_score': max_marks,
                    'correct': score == max_marks,
                    'evaluation_type': 'subjective',
                    'detailed_evaluation': evaluation,
                    'feedback': evaluation.get('detailed_feedback', 'No feedback available'),
                    'suggestions': evaluation.get('suggestions', 'No suggestions available'),
                    'strengths': evaluation.get('strengths', []),
                    'improvements': evaluation.get('improvements', []),
                    'grade_justification': evaluation.get('grade_justification', '')
                }
                
            except Exception as e:
                st.error(f"Error parsing evaluation: {str(e)}")
                return self._fallback_evaluation(question, user_answer, question_type)
        
        return self._fallback_evaluation(question, user_answer, question_type)
    
    def _fallback_evaluation(self, question: Dict, user_answer: str, question_type: str) -> Dict:
        """Fallback evaluation when AI evaluation fails"""
        max_marks = SCORING.get(question_type, 1)
        
        # Simple heuristic evaluation
        score = min(max_marks, max(0, len(user_answer.split()) // 10))
        
        return {
            'score': score,
            'max_score': max_marks,
            'correct': score == max_marks,
            'evaluation_type': 'fallback',
            'feedback': 'Automatic evaluation failed. Manual review recommended.',
            'suggestions': 'Please review your answer and ensure it addresses all parts of the question.'
        }
    
    def display_evaluation_result(self, result: Dict, question_type: str, question_index: int):
        """Display enhanced evaluation results"""
        
        score = result.get('score', 0)
        max_score = result.get('max_score', 1)
        percentage = (score / max_score * 100) if max_score > 0 else 0
        
        # Header with score
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if result.get('correct', False):
                st.success(f"✅ Correct!")
            else:
                st.error(f"❌ Incorrect")
        
        with col2:
            st.metric("Score", f"{score}/{max_score}")
        
        with col3:
            st.metric("Percentage", f"{percentage:.1f}%")
        
        # Detailed feedback based on evaluation type
        if result.get('evaluation_type') == 'mcq':
            self._display_mcq_feedback(result)
        elif result.get('evaluation_type') == 'subjective':
            self._display_subjective_feedback(result)
        elif result.get('evaluation_type') == 'skipped':
            st.warning("⏭️ Question was skipped")
        
        # General feedback
        if result.get('feedback'):
            st.info(f"**Feedback:** {result['feedback']}")
        
        if result.get('suggestions'):
            st.info(f"**Suggestions:** {result['suggestions']}")
        
        return score, max_score
    
    def _display_mcq_feedback(self, result: Dict):
        """Display MCQ-specific feedback"""
        if not result.get('correct', False):
            st.write(f"**Your answer:** {result.get('user_answer', 'Not provided')}")
            st.write(f"**Correct answer:** {result.get('correct_answer', 'Not provided')}")
    
    def _display_subjective_feedback(self, result: Dict):
        """Display subjective answer feedback"""
        detailed_eval = result.get('detailed_evaluation', {})
        
        if detailed_eval:
            # Show detailed scores
            st.write("**Detailed Evaluation:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'accuracy_score' in detailed_eval:
                    st.metric("Accuracy", f"{detailed_eval['accuracy_score']}/10")
                if 'completeness_score' in detailed_eval:
                    st.metric("Completeness", f"{detailed_eval['completeness_score']}/10")
            
            with col2:
                if 'clarity_score' in detailed_eval:
                    st.metric("Clarity", f"{detailed_eval['clarity_score']}/10")
                if 'relevance_score' in detailed_eval:
                    st.metric("Relevance", f"{detailed_eval['relevance_score']}/10")
            
            # Strengths and improvements
            if detailed_eval.get('strengths'):
                st.write("**Strengths:**")
                for strength in detailed_eval['strengths']:
                    st.write(f"✅ {strength}")
            
            if detailed_eval.get('improvements'):
                st.write("**Areas for Improvement:**")
                for improvement in detailed_eval['improvements']:
                    st.write(f"🔄 {improvement}")
    
    def calculate_test_score(self, results: List[Dict]) -> Dict:
        """Calculate comprehensive test score with analytics"""
        
        total_score = sum(result.get('score', 0) for result in results)
        total_max_score = sum(result.get('max_score', 1) for result in results)
        
        if total_max_score == 0:
            return {
                'total_score': 0,
                'total_max_score': 0,
                'percentage': 0,
                'grade': 'F'
            }
        
        percentage = (total_score / total_max_score * 100)
        
        # Detailed analytics
        analytics = self._calculate_analytics(results)
        
        return {
            'total_score': total_score,
            'total_max_score': total_max_score,
            'percentage': percentage,
            'grade': self._get_grade(percentage),
            'analytics': analytics
        }
    
    def _calculate_analytics(self, results: List[Dict]) -> Dict:
        """Calculate detailed analytics"""
        
        analytics = {
            'total_questions': len(results),
            'attempted': sum(1 for r in results if r.get('evaluation_type') != 'skipped'),
            'skipped': sum(1 for r in results if r.get('evaluation_type') == 'skipped'),
            'correct': sum(1 for r in results if r.get('correct', False)),
            'by_type': {}
        }
        
        # Analytics by question type
        for result in results:
            eval_type = result.get('evaluation_type', 'unknown')
            if eval_type not in analytics['by_type']:
                analytics['by_type'][eval_type] = {
                    'total': 0,
                    'correct': 0,
                    'score': 0,
                    'max_score': 0
                }
            
            analytics['by_type'][eval_type]['total'] += 1
            analytics['by_type'][eval_type]['correct'] += 1 if result.get('correct', False) else 0
            analytics['by_type'][eval_type]['score'] += result.get('score', 0)
            analytics['by_type'][eval_type]['max_score'] += result.get('max_score', 1)
        
        return analytics
    
    def _get_grade(self, percentage: float) -> str:
        """Get letter grade based on percentage"""
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B'
        elif percentage >= 60:
            return 'C'
        elif percentage >= 50:
            return 'D'
        else:
            return 'F'
    
    def save_test_results(self, results: List[Dict], test_config: Dict, 
                         user_name: str = "Anonymous", test_duration: float = 0):
        """Save enhanced test results with detailed analytics"""
        
        try:
            summary = self.calculate_test_score(results)
            
            test_data = {
                'user_name': user_name,
                'test_config': test_config,
                'timestamp': datetime.now().isoformat(),
                'test_duration': test_duration,
                'results': results,
                'summary': summary,
                'version': '2.0'
            }
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{user_name}_{timestamp}.json"
            filepath = f"data/{filename}"
            
            os.makedirs("data", exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, indent=2, ensure_ascii=False)
            
            st.success(f"✅ Test results saved to {filepath}")
            
        except Exception as e:
            st.error(f"❌ Error saving test results: {str(e)}")
    
    def display_test_summary(self, results: List[Dict], test_duration: float = 0):
        """Display comprehensive test summary"""
        
        summary = self.calculate_test_score(results)
        analytics = summary.get('analytics', {})
        
        st.header("📊 Test Summary")
        
        # Time taken
        if test_duration > 0:
            minutes = int(test_duration // 60)
            seconds = int(test_duration % 60)
            st.info(f"⏱️ Time taken: {minutes}:{seconds:02d}")
        
        # Overall performance
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Score", f"{summary['total_score']}/{summary['total_max_score']}")
        
        with col2:
            st.metric("Percentage", f"{summary['percentage']:.1f}%")
        
        with col3:
            st.metric("Grade", summary['grade'])
        
        with col4:
            st.metric("Attempted", f"{analytics.get('attempted', 0)}/{analytics.get('total_questions', 0)}")
        
        # Performance breakdown
        self._display_performance_breakdown(analytics)
        
        # Detailed question analysis
        self._display_detailed_analysis(results)
    
    def _display_performance_breakdown(self, analytics: Dict):
        """Display performance breakdown"""
        
        st.subheader("📈 Performance Breakdown")
        
        # Overall stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Questions Attempted", analytics.get('attempted', 0))
        
        with col2:
            st.metric("Questions Skipped", analytics.get('skipped', 0))
        
        with col3:
            st.metric("Questions Correct", analytics.get('correct', 0))
        
        # Performance by type
        by_type = analytics.get('by_type', {})
        
        if by_type:
            st.write("**Performance by Question Type:**")
            
            type_data = []
            for q_type, stats in by_type.items():
                if q_type not in ['skipped', 'no_answer']:
                    percentage = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    type_data.append({
                        'Type': q_type.replace('_', ' ').title(),
                        'Total': stats['total'],
                        'Correct': stats['correct'],
                        'Score': f"{stats['score']}/{stats['max_score']}",
                        'Percentage': f"{percentage:.1f}%"
                    })
            
            if type_data:
                df = pd.DataFrame(type_data)
                st.dataframe(df, use_container_width=True)
    
    def _display_detailed_analysis(self, results: List[Dict]):
        """Display detailed question-by-question analysis"""
        
        st.subheader("📋 Detailed Analysis")
        
        for i, result in enumerate(results):
            with st.expander(f"Question {i + 1} - {result.get('evaluation_type', 'unknown').title()}"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Score:** {result.get('score', 0)}/{result.get('max_score', 1)}")
                    st.write(f"**Status:** {'✅ Correct' if result.get('correct', False) else '❌ Incorrect'}")
                
                with col2:
                    if result.get('evaluation_type') == 'mcq':
                        st.write(f"**Your Answer:** {result.get('user_answer', 'Not provided')}")
                        st.write(f"**Correct Answer:** {result.get('correct_answer', 'Not provided')}")
                
                if result.get('feedback'):
                    st.write(f"**Feedback:** {result['feedback']}")
                
                if result.get('suggestions'):
                    st.write(f"**Suggestions:** {result['suggestions']}")
    
    def get_test_history(self, user_name: str = "Anonymous") -> List[Dict]:
        """Get enhanced test history for a user"""
        
        try:
            import glob
            
            pattern = f"data/test_results_{user_name}_*.json"
            files = glob.glob(pattern)
            
            history = []
            for file in files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        history.append(data)
                except:
                    continue
            
            # Sort by timestamp
            history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return history
            
        except Exception as e:
            st.error(f"❌ Error getting test history: {str(e)}")
            return []
    
    def display_test_history(self, history: List[Dict]):
        """Display enhanced test history"""
        
        if not history:
            st.info("No test history available.")
            return
        
        st.subheader("📚 Test History")
        
        # Summary statistics
        if len(history) > 1:
            self._display_history_stats(history)
        
        # Individual test results
        history_data = []
        for i, test in enumerate(history):
            summary = test.get('summary', {})
            test_config = test.get('test_config', {})
            
            history_data.append({
                'Test': test_config.get('test_name', f'Test {i+1}'),
                'Date': test.get('timestamp', '').split('T')[0],
                'Score': f"{summary.get('total_score', 0)}/{summary.get('total_max_score', 0)}",
                'Percentage': f"{summary.get('percentage', 0):.1f}%",
                'Grade': summary.get('grade', 'F'),
                'Duration': f"{int(test.get('test_duration', 0) // 60)}:{int(test.get('test_duration', 0) % 60):02d}"
            })
        
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True)
    
    def _display_history_stats(self, history: List[Dict]):
        """Display historical performance statistics"""
        
        st.write("**Performance Trends:**")
        
        scores = [test.get('summary', {}).get('percentage', 0) for test in history]
        
        if scores:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Average Score", f"{sum(scores) / len(scores):.1f}%")
            
            with col2:
                st.metric("Best Score", f"{max(scores):.1f}%")
            
            with col3:
                st.metric("Latest Score", f"{scores[0]:.1f}%")
            
            # Simple trend chart
            chart_data = pd.DataFrame({
                'Test': [f'Test {i+1}' for i in range(len(scores))],
                'Score': scores
            })
            
            st.line_chart(chart_data.set_index('Test'))
