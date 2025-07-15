import streamlit as st
import os
import time
from datetime import datetime
from src.config import APP_TITLE, APP_DESCRIPTION
from src.utils.document_processor import DocumentProcessor
from src.components.question_generator import QuestionGenerator
from src.components.answer_evaluator import AnswerEvaluator

# Configure page
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def get_components():
    return {
        'doc_processor': DocumentProcessor(),
        'question_generator': QuestionGenerator(),
        'answer_evaluator': AnswerEvaluator()
    }

def main():
    components = get_components()
    
    # Header
    st.title(APP_TITLE)
    st.markdown(APP_DESCRIPTION)
    
    # Initialize session state
    if 'test_start_time' not in st.session_state:
        st.session_state['test_start_time'] = None
    
    # Sidebar for navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["📁 Upload & Generate", "⚙️ Configure Test", "✍️ Take Test", "📊 View Results", "📚 Test History"]
    )
    
    if page == "📁 Upload & Generate":
        upload_and_generate_page(components)
    elif page == "⚙️ Configure Test":
        configure_test_page(components)
    elif page == "✍️ Take Test":
        take_test_page(components)
    elif page == "📊 View Results":
        view_results_page(components)
    elif page == "📚 Test History":
        test_history_page(components)

def upload_and_generate_page(components):
    st.header("📁 Upload Book Chapter & Generate Questions")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload your book chapter (PDF, DOCX, or TXT)",
        type=['pdf', 'docx', 'txt'],
        help="Upload a chapter from your book to generate questions"
    )
    
    if uploaded_file is not None:
        # Process uploaded file
        with st.spinner("Processing uploaded file..."):
            text = components['doc_processor'].process_uploaded_file(uploaded_file)
        
        if text:
            st.success("✅ File processed successfully!")
            
            # Show text preview
            with st.expander("📖 Preview extracted text"):
                st.text_area("Extracted text", text[:1000] + "..." if len(text) > 1000 else text, height=200)
            
            # Split into chapters
            chapters = components['doc_processor'].split_into_chapters(text)
            
            if len(chapters) > 1:
                st.subheader("📚 Detected Chapters")
                selected_chapter = st.selectbox("Select a chapter to generate questions for:", list(chapters.keys()))
                chapter_text = chapters[selected_chapter]
            else:
                selected_chapter = uploaded_file.name.replace('.pdf', '').replace('.docx', '').replace('.txt', '')
                chapter_text = text
            
            # Generate questions
            if st.button("🎯 Generate Questions", type="primary"):
                with st.spinner("Generating questions... This may take a few minutes."):
                    questions = components['question_generator'].generate_questions_for_chapter(
                        chapter_text, selected_chapter
                    )
                
                if questions:
                    st.success("✅ Questions generated successfully!")
                    
                    # Display question summary
                    st.subheader("📊 Generated Questions Summary")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("MCQ", len(questions['mcq']))
                    with col2:
                        st.metric("1 Mark", len(questions['1_mark']))
                    with col3:
                        st.metric("2 Mark", len(questions['2_mark']))
                    with col4:
                        st.metric("3 Mark", len(questions['3_mark']))
                    with col5:
                        st.metric("5 Mark", len(questions['5_mark']))
                    
                    # Save questions
                    components['question_generator'].save_questions_to_file(questions, selected_chapter)
                    
                    # PDF Export button
                    components['question_generator'].create_pdf_download_button(questions, selected_chapter)
                    
                    # Store in session state
                    st.session_state['current_questions'] = questions
                    st.session_state['current_chapter'] = selected_chapter
                    
                    st.info("✨ Questions saved! Now go to 'Configure Test' to create your custom test.")

def configure_test_page(components):
    st.header("⚙️ Configure Test")
    
    # Load available question sets
    available_files = components['question_generator'].get_available_question_files()
    
    if not available_files:
        st.warning("⚠️ No question sets available. Please upload a chapter and generate questions first.")
        return
    
    # Select question set
    selected_file = st.selectbox("📚 Select a chapter:", available_files)
    
    if selected_file:
        # Load questions
        questions = components['question_generator'].load_questions_from_file(selected_file)
        
        if not questions:
            st.error("❌ Failed to load questions.")
            return
        
        st.success(f"✅ Selected: {questions['chapter_name']}")
        
        # Display test configuration interface
        config = components['question_generator'].display_test_configuration(questions)
        
        if config and st.button("🚀 Create Custom Test", type="primary"):
            custom_test = components['question_generator'].create_custom_test(questions, config)
            
            st.session_state['custom_test'] = custom_test
            st.session_state['test_config'] = config
            
            st.success("✅ Custom test created!")
            st.info("📝 Go to 'Take Test' to start your custom test.")

def take_test_page(components):
    st.header("✍️ Take Test")
    
    # Check if custom test exists
    if 'custom_test' in st.session_state:
        display_custom_test(components)
    else:
        st.warning("⚠️ No test configured. Please go to 'Configure Test' first.")

def display_custom_test(components):
    custom_test = st.session_state['custom_test']
    test_config = st.session_state['test_config']
    
    st.subheader(f"📝 {custom_test['test_name']}")
    
    # Test info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📚 Chapter", custom_test['chapter_name'])
    with col2:
        st.metric("📝 Questions", custom_test['total_questions'])
    with col3:
        st.metric("📊 Total Marks", custom_test['total_marks'])
    with col4:
        st.metric("⏰ Time Limit", f"{custom_test['time_limit']} min")
    
    # User information
    if 'user_name' not in st.session_state:
        st.session_state['user_name'] = st.text_input("👤 Enter your name:", value="Anonymous")
    
    # Start test
    if 'test_started' not in st.session_state:
        st.session_state['test_started'] = False
    
    if not st.session_state['test_started']:
        st.markdown("---")
        st.subheader("📋 Test Instructions")
        st.markdown("""
        - **Time Limit**: You have a limited time to complete the test
        - **Audio Support**: Use the 🔊 button to listen to questions
        - **Voice Answers**: Use the 🎤 button to answer with voice
        - **Skip Questions**: Use the ⏭️ button to skip questions
        - **Hints**: Use the ❓ button for hints on difficult questions
        - **Navigation**: Use Previous/Next buttons to navigate between questions
        """)
        
        if st.button("🚀 Start Test", type="primary", use_container_width=True):
            st.session_state['test_started'] = True
            st.session_state['test_start_time'] = time.time()
            st.session_state['current_question_index'] = 0
            st.session_state['user_answers'] = {}
            st.session_state['test_results'] = []
            st.session_state['skipped_questions'] = []
            st.rerun()
    
    else:
        # Display test interface
        display_test_interface(components, custom_test, test_config)

def display_test_interface(components, custom_test, test_config):
    questions = custom_test['questions']
    current_index = st.session_state.get('current_question_index', 0)
    
    # Timer
    if st.session_state['test_start_time']:
        elapsed_time = time.time() - st.session_state['test_start_time']
        remaining_time = (test_config['time_limit'] * 60) - elapsed_time
        
        if remaining_time <= 0:
            st.error("⏰ Time's up! Test completed.")
            complete_test(components, custom_test)
            return
        
        # Display timer
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        
        timer_color = "red" if remaining_time < 300 else "orange" if remaining_time < 600 else "green"
        st.markdown(f"<div style='text-align: center; color: {timer_color}; font-size: 24px; font-weight: bold;'>⏰ Time Remaining: {minutes:02d}:{seconds:02d}</div>", unsafe_allow_html=True)
    
    # Check if test is completed
    if current_index >= len(questions):
        complete_test(components, custom_test)
        return
    
    current_q = questions[current_index]
    question = current_q['question']
    q_type = current_q['type']
    
    # Display question with enhanced features
    voice_answer = components['question_generator'].display_question_with_enhanced_features(
        question, q_type, current_index, len(questions)
    )
    
    # Handle voice answer
    if voice_answer and voice_answer != "SKIP":
        st.session_state['user_answers'][current_index] = voice_answer
        st.success(f"✅ Voice answer recorded: {voice_answer}")
    elif voice_answer == "SKIP":
        st.session_state['skipped_questions'].append(current_index)
        st.info("⏭️ Question skipped")
    
    # Get user answer
    answer_key = f"answer_{current_index}"
    user_answer = st.session_state['user_answers'].get(current_index, "")
    
    if q_type == 'mcq':
        if not voice_answer:
            user_answer = st.radio(
                "Select your answer:",
                options=list(question['options'].keys()),
                key=answer_key,
                index=None if not user_answer else list(question['options'].keys()).index(user_answer)
            )
    else:
        if not voice_answer:
            user_answer = st.text_area(
                "Enter your answer:",
                value=user_answer,
                height=150,
                key=answer_key,
                help="Type your answer here or use voice input"
            )
    
    # Store answer
    if user_answer:
        st.session_state['user_answers'][current_index] = user_answer
    
    # Navigation
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if current_index > 0:
            if st.button("⬅️ Previous", use_container_width=True):
                st.session_state['current_question_index'] = current_index - 1
                st.rerun()
    
    with col2:
        if user_answer and st.button("✅ Submit & Next", type="primary", use_container_width=True):
            # Evaluate answer
            with st.spinner("Evaluating answer..."):
                result = components['answer_evaluator'].evaluate_answer(question, user_answer, q_type)
            
            # Store result
            st.session_state['test_results'].append({
                'question_index': current_index,
                'question': question,
                'question_type': q_type,
                'user_answer': user_answer,
                'evaluation': result
            })
            
            # Show evaluation
            score, max_score = components['answer_evaluator'].display_evaluation_result(result, q_type, current_index)
            
            # Move to next question
            if current_index + 1 < len(questions):
                st.session_state['current_question_index'] = current_index + 1
                time.sleep(2)  # Brief pause to show evaluation
                st.rerun()
            else:
                st.success("🎉 All questions completed!")
                if st.button("🏁 Finish Test", type="primary"):
                    complete_test(components, custom_test)
    
    with col3:
        if current_index + 1 < len(questions):
            if st.button("⏭️ Next", use_container_width=True):
                st.session_state['current_question_index'] = current_index + 1
                st.rerun()
    
    with col4:
        if st.button("🏁 Finish Test", use_container_width=True):
            complete_test(components, custom_test)

def complete_test(components, custom_test):
    st.header("🎉 Test Completed!")
    
    results = st.session_state.get('test_results', [])
    user_name = st.session_state.get('user_name', 'Anonymous')
    
    # Calculate time taken
    if st.session_state['test_start_time']:
        time_taken = time.time() - st.session_state['test_start_time']
        time_taken_minutes = int(time_taken // 60)
        time_taken_seconds = int(time_taken % 60)
        
        st.info(f"⏱️ Time taken: {time_taken_minutes}:{time_taken_seconds:02d}")
    
    # Display summary
    evaluation_results = [r['evaluation'] for r in results]
    components['answer_evaluator'].display_test_summary(evaluation_results)
    
    # Save results
    components['answer_evaluator'].save_test_results(
        evaluation_results, 
        custom_test['chapter_name'], 
        user_name
    )
    
    # Show skipped questions
    if st.session_state.get('skipped_questions'):
        st.subheader("⏭️ Skipped Questions")
        st.write(f"You skipped {len(st.session_state['skipped_questions'])} questions")
    
    # Reset test state
    if st.button("🔄 Take Another Test", type="primary"):
        # Clean up session state
        for key in ['test_started', 'custom_test', 'test_config', 'current_question_index', 
                   'user_answers', 'test_results', 'test_start_time', 'skipped_questions']:
            if key in st.session_state:
                del st.session_state[key]
        
        # Clean up audio files
        components['question_generator'].cleanup_audio_files()
        
        st.rerun()

def view_results_page(components):
    st.header("📊 View Results")
    
    # Show latest test results if available
    if 'test_results' in st.session_state:
        results = st.session_state['test_results']
        if results:
            st.subheader("📋 Latest Test Results")
            
            for i, result in enumerate(results):
                with st.expander(f"Question {i + 1} - {result['question_type'].replace('_', ' ').title()}"):
                    st.write(f"**Question:** {result['question']['question']}")
                    st.write(f"**Your Answer:** {result['user_answer']}")
                    st.write(f"**Score:** {result['evaluation']['score']}/{result['evaluation']['max_score']}")
                    st.write(f"**Feedback:** {result['evaluation']['feedback']}")
                    
                    if 'suggestions' in result['evaluation']:
                        st.write(f"**Suggestions:** {result['evaluation']['suggestions']}")
    else:
        st.info("📝 No recent test results available.")

def test_history_page(components):
    st.header("📚 Test History")
    
    user_name = st.text_input("👤 Enter your name to view history:", value="Anonymous")
    
    if st.button("🔍 Load History"):
        history = components['answer_evaluator'].get_test_history(user_name)
        if history:
            components['answer_evaluator'].display_test_history(history)
        else:
            st.info(f"📝 No test history found for {user_name}")

if __name__ == "__main__":
    main()
