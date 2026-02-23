import streamlit as st
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="AI Interview Prep", page_icon="🎤", layout="wide")

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
</style>
""", unsafe_allow_html=True)

# Questions DB
QUESTIONS_DB = {
    "Data Scientist": {
        "Beginner": [
            {"question": "What is supervised vs unsupervised learning?", "category": "ML", "keywords": ["supervised", "labeled", "unsupervised", "clustering"]},
            {"question": "Explain overfitting.", "category": "Evaluation", "keywords": ["overfitting", "training", "test", "validation"]},
            {"question": "What is a confusion matrix?", "category": "Metrics", "keywords": ["confusion", "matrix", "precision", "recall"]},
        ]
    },
    "ML Engineer": {
        "Beginner": [
            {"question": "Batch vs online learning?", "category": "Systems", "keywords": ["batch", "online", "real-time", "incremental"]},
        ]
    }
}

# Evaluation
def evaluate_answer(answer, q_data):
    matched = sum(1 for kw in q_data["keywords"] if kw.lower() in answer.lower())
    score = int((matched / len(q_data["keywords"])) * 100)
    feedback = "🌟 Excellent!" if score >= 80 else "👍 Good!" if score >= 60 else "⚠️ Partial" if score >= 40 else "❌ Needs work"
    return {"score": score, "feedback": feedback, "missing": [k for k in q_data["keywords"] if k.lower() not in answer.lower()]}

# Sidebar
st.sidebar.title("🎯 Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "📄 Resume", "🎤 Interview", "📊 Results"])
st.sidebar.markdown("---")
job_role = st.sidebar.selectbox("Role:", ["Data Scientist", "ML Engineer"])
difficulty = st.sidebar.select_slider("Difficulty:", ["Beginner", "Intermediate", "Advanced"])

# HOME
if page == "🏠 Home":
    st.markdown("<h1 class='main-header'>🎤 AI Interview Prep</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Ace your next interview!</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='feature-box'><h3>📄 Resume</h3><p>Tailored questions</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='feature-box'><h3>🎙️ Voice</h3><p>Real feedback</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='feature-box'><h3>🤖 3D Avatar</h3><p>Realistic interview</p></div>", unsafe_allow_html=True)
    
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
            st.success("✅ Ready!")

# INTERVIEW
elif page == "🎤 Interview":
    st.title("🎤 AI Interview")
    
    col1, col2 = st.columns([3,1])
    with col1:
        st.markdown(f"### 🎯 {job_role} | {difficulty}")
    with col2:
        elapsed = (datetime.now() - st.session_state.start_time).seconds
        mins, secs = divmod(elapsed, 60)
        st.markdown(f"### ⏱️ {mins:02d}:{secs:02d}")
    
    st.markdown("---")
    st.subheader("🤖 AI Interviewer")
    
    # YOUR VERCEL DEPLOYMENT
    st.components.v1.iframe("https://interview-prep-system.vercel.app/", height=600, scrolling=False)
    
    st.markdown("---")
    
    questions = QUESTIONS_DB.get(job_role, {}).get(difficulty, QUESTIONS_DB["Data Scientist"]["Beginner"])
    
    if st.session_state.question_num > len(questions):
        st.success("🎉 Complete!")
        st.info("View Results →")
    else:
        q_idx = st.session_state.question_num - 1
        q = questions[q_idx]
        
        st.subheader(f"❓ Q{st.session_state.question_num}/{len(questions)}")
        st.markdown(f"<div class='feature-box'><h3>{q['question']}</h3><p>{q['category']}</p></div>", unsafe_allow_html=True)
        
        answer = st.text_area("Your answer:", height=150, key=f"a{st.session_state.question_num}")
        
        if st.button("📤 Submit"):
            if answer:
                result = evaluate_answer(answer, q)
                st.session_state.answers.append({"q": q['question'], "a": answer, "score": result['score']})
                st.session_state.scores.append(result['score'])
                
                st.success(f"Score: {result['score']}/100")
                st.info(result['feedback'])
                if result['missing']:
                    st.warning(f"Try: {', '.join(result['missing'][:2])}")
                
                st.session_state.question_num += 1
                st.balloons()
                st.rerun()
        
        st.progress(st.session_state.question_num / len(questions))

# RESULTS
elif page == "📊 Results":
    st.title("📊 Results")
    
    if not st.session_state.answers:
        st.warning("No interview yet!")
    else:
        avg = sum(st.session_state.scores) / len(st.session_state.scores)
        mins = (datetime.now() - st.session_state.start_time).seconds // 60
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='score-card'><h2>{avg:.0f}%</h2><p>Score</p></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='score-card'><h2>{len(st.session_state.answers)}</h2><p>Questions</p></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='score-card'><h2>{mins}</h2><p>Minutes</p></div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        for i, ans in enumerate(st.session_state.answers, 1):
            with st.expander(f"Q{i}: {ans['q'][:50]}..."):
                st.write(f"**Answer:** {ans['a']}")
                st.write(f"**Score:** {ans['score']}/100")
        
        if st.button("📥 Download JSON"):
            st.download_button("💾 Save", json.dumps({"avg": avg, "answers": st.session_state.answers}, indent=2), "report.json")
        
        if st.button("🔄 New Interview"):
            st.session_state.question_num = 1
            st.session_state.answers = []
            st.session_state.scores = []
            st.session_state.start_time = datetime.now()
            st.rerun()

st.markdown("---")
st.markdown("<div style='text-align:center;color:#757575'><p>Built with ❤️ | BCA Project</p></div>", unsafe_allow_html=True)