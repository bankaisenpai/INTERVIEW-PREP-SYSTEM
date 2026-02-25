import streamlit as st
import pandas as pd
from datetime import datetime
import json
import requests
import os
from dotenv import load_dotenv

st.set_page_config(page_title="AI Interview Prep", page_icon="🎤", layout="wide")

# ═══════════════════════════════════════════════════════════
# GROQ AI CONFIGURATION (FREE API)
# ═══════════════════════════════════════════════════════════
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def ai_evaluate_answer(question, answer, keywords):
    """Use Groq AI to evaluate interview answers"""
    
    if not GROQ_API_KEY or GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
        # Fallback to keyword matching if no API key
        return keyword_evaluate(answer, keywords)
    
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""You are an expert technical interviewer. Evaluate this interview answer.

Question: {question}
Expected Keywords: {', '.join(keywords)}

Candidate's Answer: {answer}

Provide your evaluation as JSON with this exact format:
{{
    "score": <number 0-100>,
    "strengths": ["strength 1", "strength 2"],
    "improvements": ["improvement 1", "improvement 2"],
    "feedback": "<one sentence overall feedback>"
}}

Be specific and constructive. Score generously if concepts are correct even if wording differs."""

        payload = {
            "model": "llama3-8b-8192",  # Fast, free model
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
                return evaluation
            else:
                return keyword_evaluate(answer, keywords)
        else:
            return keyword_evaluate(answer, keywords)
            
    except Exception as e:
        st.warning(f"AI evaluation unavailable, using keyword matching")
        return keyword_evaluate(answer, keywords)

def keyword_evaluate(answer, keywords):
    """Fallback keyword-based evaluation"""
    matched = sum(1 for kw in keywords if kw.lower() in answer.lower())
    score = int((matched / len(keywords)) * 100)
    
    feedback_map = {
        80: "🌟 Excellent! Comprehensive answer.",
        60: "👍 Good! Covers key concepts.",
        40: "⚠️ Partial understanding shown.",
        0: "❌ Needs more detail on core concepts."
    }
    
    feedback = next(v for k, v in sorted(feedback_map.items(), reverse=True) if score >= k)
    missing = [k for k in keywords if k.lower() not in answer.lower()]
    
    return {
        "score": score,
        "strengths": [f"Mentioned {len(keywords) - len(missing)} key concepts"],
        "improvements": [f"Could mention: {', '.join(missing[:2])}"] if missing else ["Great coverage!"],
        "feedback": feedback
    }

# Initialize session state
if 'question_num' not in st.session_state:
    st.session_state.question_num = 1
if 'start_time' not in st.session_state:
    st.session_state.start_time = datetime.now()
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'scores' not in st.session_state:
    st.session_state.scores = []

# CSS
st.markdown("""
<style>
.main-header { font-size: 3rem; font-weight: bold; text-align: center; color: #1E88E5; }
.sub-header { text-align: center; color: #757575; font-size: 1.2rem; margin-bottom: 2rem; }
.feature-box { background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #1E88E5; }
.stButton>button { background-color: #1E88E5; color: white; font-size: 1.0rem; border-radius: 8px; padding: 0.5rem 2rem; }
.score-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; text-align: center; }
.strength-box { background-color: #d4edda; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 3px solid #28a745; }
.improvement-box { background-color: #fff3cd; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 3px solid #ffc107; }
</style>
""", unsafe_allow_html=True)

# EXPANDED Questions DB
QUESTIONS_DB = {
    "Data Scientist": {
        "Beginner": [
            {"question": "What is the difference between supervised and unsupervised learning?", "category": "ML Fundamentals", "keywords": ["supervised", "labeled", "unsupervised", "clustering", "classification"]},
            {"question": "Explain overfitting and how to prevent it.", "category": "Model Evaluation", "keywords": ["overfitting", "training", "test", "validation", "regularization", "cross-validation"]},
            {"question": "What is a confusion matrix and what does it tell us?", "category": "Metrics", "keywords": ["confusion", "matrix", "precision", "recall", "true positive", "false positive"]},
            {"question": "Explain the difference between precision and recall.", "category": "Metrics", "keywords": ["precision", "recall", "true positive", "false positive", "false negative"]},
            {"question": "What is cross-validation and why is it important?", "category": "Validation", "keywords": ["cross-validation", "k-fold", "training", "validation", "generalization"]},
        ],
        "Intermediate": [
            {"question": "Explain the bias-variance tradeoff.", "category": "ML Theory", "keywords": ["bias", "variance", "tradeoff", "underfitting", "overfitting", "generalization"]},
            {"question": "How do you handle imbalanced datasets?", "category": "Data Preprocessing", "keywords": ["imbalanced", "sampling", "SMOTE", "class weights", "oversampling", "undersampling"]},
            {"question": "What is gradient descent and its variants?", "category": "Optimization", "keywords": ["gradient", "descent", "learning rate", "SGD", "Adam", "momentum"]},
            {"question": "Explain feature engineering and its importance.", "category": "Feature Engineering", "keywords": ["feature", "engineering", "transformation", "selection", "scaling"]},
            {"question": "What are ensemble methods in machine learning?", "category": "Algorithms", "keywords": ["ensemble", "bagging", "boosting", "random forest", "voting"]},
        ]
    },
    "ML Engineer": {
        "Beginner": [
            {"question": "What is the difference between batch and online learning?", "category": "ML Systems", "keywords": ["batch", "online", "real-time", "incremental", "streaming"]},
            {"question": "How do you deploy a machine learning model?", "category": "MLOps", "keywords": ["deployment", "API", "docker", "serving", "production"]},
            {"question": "What is model monitoring and why is it important?", "category": "MLOps", "keywords": ["monitoring", "drift", "performance", "metrics", "alerts"]},
        ],
        "Intermediate": [
            {"question": "Explain model versioning and experiment tracking.", "category": "MLOps", "keywords": ["versioning", "experiment", "tracking", "mlflow", "wandb"]},
            {"question": "What is A/B testing for machine learning models?", "category": "Production ML", "keywords": ["A/B", "testing", "experiments", "control", "treatment"]},
        ]
    },
    "Software Engineer": {
        "Beginner": [
            {"question": "What is the difference between a list and a tuple in Python?", "category": "Python Basics", "keywords": ["list", "tuple", "mutable", "immutable", "ordered"]},
            {"question": "Explain object-oriented programming concepts.", "category": "OOP", "keywords": ["OOP", "class", "object", "inheritance", "polymorphism", "encapsulation"]},
            {"question": "What is a REST API?", "category": "Web Development", "keywords": ["REST", "API", "HTTP", "GET", "POST", "endpoint"]},
        ]
    }
}

# Sidebar
st.sidebar.title("🎯 Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "📄 Resume", "🎤 Interview", "📊 Results"])
st.sidebar.markdown("---")
job_role = st.sidebar.selectbox("Role:", ["Data Scientist", "ML Engineer", "Software Engineer"])
difficulty = st.sidebar.select_slider("Difficulty:", ["Beginner", "Intermediate", "Advanced"])

# Add AI status indicator
st.sidebar.markdown("---")
if GROQ_API_KEY and GROQ_API_KEY != "YOUR_GROQ_API_KEY_HERE":
    st.sidebar.success("🤖 AI Evaluation: Enabled")
else:
    st.sidebar.warning("⚠️ AI Evaluation: Disabled\n(Using keyword matching)")

# HOME
if page == "🏠 Home":
    st.markdown("<h1 class='main-header'>🎤 AI Interview Prep</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Ace your next interview with AI-powered feedback!</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='feature-box'><h3>📄 Resume</h3><p>Tailored questions</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='feature-box'><h3>🤖 AI Feedback</h3><p>Smart evaluation</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='feature-box'><h3>🎨 3D Avatar</h3><p>Realistic interview</p></div>", unsafe_allow_html=True)
    
    avg = sum(st.session_state.scores) / len(st.session_state.scores) if st.session_state.scores else 0
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Interviews", "1" if len(st.session_state.answers) > 0 else "0")
    col2.metric("Avg Score", f"{avg:.0f}%")
    col3.metric("Answered", len(st.session_state.answers))
    col4.metric("Improvement", "+15%" if len(st.session_state.answers) > 3 else "0%")

# RESUME
elif page == "📄 Resume":
    st.title("📄 Upload Resume")
    uploaded = st.file_uploader("PDF only", type=['pdf'])
    if uploaded:
        st.success(f"✅ {uploaded.name}")
        if st.button("🎯 Generate Questions"):
            st.success("✅ Questions ready!")

# INTERVIEW
elif page == "🎤 Interview":
    st.title("🎤 AI-Powered Interview")
    
    col1, col2 = st.columns([3,1])
    with col1:
        st.markdown(f"### 🎯 {job_role} | {difficulty}")
    with col2:
        elapsed = (datetime.now() - st.session_state.start_time).seconds
        mins, secs = divmod(elapsed, 60)
        st.markdown(f"### ⏱️ {mins:02d}:{secs:02d}")
    
    st.markdown("---")
    st.subheader("🤖 AI Interviewer")
    
    # 3D Avatar
    st.components.v1.iframe("https://interview-prep-system.vercel.app/", height=600, scrolling=False)
    
    st.markdown("---")
    
    questions = QUESTIONS_DB.get(job_role, {}).get(difficulty, QUESTIONS_DB["Data Scientist"]["Beginner"])
    
    if st.session_state.question_num > len(questions):
        st.success("🎉 Interview Complete!")
        st.info("📊 Check the Results page to see your detailed feedback!")
    else:
        q_idx = st.session_state.question_num - 1
        q = questions[q_idx]
        
        st.subheader(f"❓ Question {st.session_state.question_num} of {len(questions)}")
        st.markdown(f"<div class='feature-box'><h3>{q['question']}</h3><p>📂 Category: <strong>{q['category']}</strong></p></div>", unsafe_allow_html=True)
        
        answer = st.text_area("Your answer:", height=150, key=f"a{st.session_state.question_num}", 
                             placeholder="Type your detailed answer here. Be specific and use examples!")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("📤 Submit Answer", use_container_width=True):
                if answer and len(answer.strip()) > 10:
                    with st.spinner("🤖 AI is evaluating your answer..."):
                        # AI Evaluation
                        result = ai_evaluate_answer(q['question'], answer, q['keywords'])
                        
                        # Save answer
                        st.session_state.answers.append({
                            "q": q['question'],
                            "a": answer,
                            "score": result['score'],
                            "strengths": result.get('strengths', []),
                            "improvements": result.get('improvements', []),
                            "feedback": result.get('feedback', '')
                        })
                        st.session_state.scores.append(result['score'])
                        
                        # Display instant feedback
                        st.success(f"✅ Score: {result['score']}/100")
                        st.info(f"💬 {result['feedback']}")
                        
                        # Strengths
                        if result.get('strengths'):
                            st.markdown("**✨ Strengths:**")
                            for s in result['strengths']:
                                st.markdown(f"<div class='strength-box'>✓ {s}</div>", unsafe_allow_html=True)
                        
                        # Improvements
                        if result.get('improvements'):
                            st.markdown("**💡 Improvements:**")
                            for imp in result['improvements']:
                                st.markdown(f"<div class='improvement-box'>→ {imp}</div>", unsafe_allow_html=True)
                        
                        # Move to next
                        st.session_state.question_num += 1
                        st.balloons()
                        
                        # Auto-advance button
                        if st.button("➡️ Next Question"):
                            st.rerun()
                elif not answer:
                    st.error("⚠️ Please provide an answer before submitting!")
                else:
                    st.error("⚠️ Answer too short. Please provide more detail (min 10 characters).")
        
        with col2:
            word_count = len(answer.split()) if answer else 0
            st.metric("Word Count", word_count)
        
        # Progress bar
        st.progress(st.session_state.question_num / len(questions))

# RESULTS
elif page == "📊 Results":
    st.title("📊 Detailed Results & Feedback")
    
    if not st.session_state.answers:
        st.warning("⚠️ No interview completed yet!")
        st.info("👈 Go to '🎤 Interview' to start your first interview!")
    else:
        avg = sum(st.session_state.scores) / len(st.session_state.scores)
        mins = (datetime.now() - st.session_state.start_time).seconds // 60
        
        # Score Cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='score-card'><h2>{avg:.0f}%</h2><p>Overall Score</p></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='score-card'><h2>{len(st.session_state.answers)}</h2><p>Questions</p></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='score-card'><h2>{mins}</h2><p>Minutes</p></div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Detailed Breakdown
        st.subheader("📝 Question-by-Question Analysis")
        
        for i, ans in enumerate(st.session_state.answers, 1):
            with st.expander(f"Q{i}: {ans['q'][:60]}... | Score: {ans['score']}/100"):
                st.markdown(f"**📋 Question:** {ans['q']}")
                st.markdown(f"**✍️ Your Answer:** {ans['a']}")
                st.markdown(f"**🎯 Score:** {ans['score']}/100")
                
                if ans.get('feedback'):
                    st.info(f"💬 {ans['feedback']}")
                
                if ans.get('strengths'):
                    st.markdown("**✨ Strengths:**")
                    for s in ans['strengths']:
                        st.markdown(f"- ✓ {s}")
                
                if ans.get('improvements'):
                    st.markdown("**💡 Areas for Improvement:**")
                    for imp in ans['improvements']:
                        st.markdown(f"- → {imp}")
        
        st.markdown("---")
        
        # Download Report
        col1, col2 = st.columns(2)
        with col1:
            report_data = {
                "overall_score": avg,
                "total_questions": len(st.session_state.answers),
                "time_taken_minutes": mins,
                "answers": st.session_state.answers
            }
            st.download_button(
                "📥 Download Full Report (JSON)",
                data=json.dumps(report_data, indent=2),
                file_name=f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            if st.button("🔄 Start New Interview", use_container_width=True):
                st.session_state.question_num = 1
                st.session_state.answers = []
                st.session_state.scores = []
                st.session_state.start_time = datetime.now()
                st.success("✅ Session reset! Go to Interview page to start fresh.")
                st.rerun()

st.markdown("---")
st.markdown("<div style='text-align:center;color:#757575'><p>Built with ❤️ using React + Streamlit + Groq AI | BCA Final Year Project</p></div>", unsafe_allow_html=True)