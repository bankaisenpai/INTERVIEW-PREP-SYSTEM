import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ========================================
# PAGE CONFIGURATION
# ========================================
st.set_page_config(
    page_title="AI Interview Prep System",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# CUSTOM CSS
# ========================================
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1E88E5;
        margin-bottom: 0;
    }
    .sub-header {
        text-align: center;
        color: #757575;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .feature-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #1E88E5;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        font-size: 1.0rem;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #1565C0;
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

# ========================================
# SIDEBAR NAVIGATION
# ========================================
st.sidebar.title("🎯 Navigation")
page = st.sidebar.radio(
    "Go to",
    ["🏠 Home", "📄 Upload Resume", "🎤 Start Interview", "📊 View Results"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Interview Settings")

job_role = st.sidebar.selectbox(
    "🎯 Target Role:",
    ["Data Scientist", "ML Engineer", "Data Analyst", "AI Researcher",
     "Backend Developer", "Frontend Developer", "Cyber Security",
     "Full Stack Developer", "DevOps Engineer", "Cloud Engineer", "Software Engineer"]
)

difficulty = st.sidebar.select_slider(
    "📊 Difficulty Level:",
    options=["Beginner", "Intermediate", "Advanced", "FAANG"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip**: Upload your resume first to get personalized questions!")

# ========================================
# PAGE 1: HOME
# ========================================
if page == "🏠 Home":
    st.markdown("<h1 class='main-header'>🎤 AI Interview Preparation System</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Ace your next tech interview with AI-powered practice</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("### 📄 Resume Analysis")
        st.write("Upload your resume and get tailored questions based on your skills and experience.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("### 🎙️ Voice Analysis")
        st.write("Answer questions using your voice. Get real-time feedback on clarity and content.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("### 🤖 3D AI Interviewer")
        st.write("Interact with a realistic 3D avatar with sitting and talking animations.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("📈 Your Progress")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Interviews Completed", "0", "0")
    col2.metric("Average Score", "0%", "0%")
    col3.metric("Questions Answered", "0", "0")
    col4.metric("Improvement Rate", "0%", "0%")

    st.markdown("---")
    st.success("👉 **Ready to start?** Navigate to 'Upload Resume' to begin!")

    if st.button("🚀 Get Started Now", use_container_width=True):
        st.balloons()
        st.info("Navigate to '📄 Upload Resume' from the sidebar to begin!")

# ========================================
# PAGE 2: UPLOAD RESUME
# ========================================
elif page == "📄 Upload Resume":
    st.title("📄 Upload Your Resume")
    st.markdown("Upload your resume (PDF format) to generate personalized interview questions.")

    uploaded_file = st.file_uploader(
        "Choose your resume (PDF only)",
        type=['pdf'],
        help="Upload your latest resume in PDF format"
    )

    if uploaded_file is not None:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.success(f"✅ File uploaded: **{uploaded_file.name}**")
            st.info(f"📦 File size: {uploaded_file.size / 1024:.2f} KB")

            st.markdown("### 📋 Resume Preview")
            st.warning("🚧 Resume parsing will be implemented in the next step!")

            with st.expander("🔍 Extracted Information (Coming Soon)"):
                st.write("- **Skills**: Python, Machine Learning, SQL, Azure")
                st.write("- **Experience**: 1 year")
                st.write("- **Projects**: 3 detected")

        with col2:
            st.markdown("### ⚙️ Options")

            if st.button("🎯 Generate Questions", use_container_width=True):
                with st.spinner("Analyzing your resume..."):
                    import time
                    time.sleep(2)
                    st.success("✅ 8 questions generated!")
                    st.info("Navigate to '🎤 Start Interview' to begin!")

            if st.button("🗑️ Clear Resume", use_container_width=True):
                st.rerun()
    else:
        st.info("👆 Please upload your resume to continue")

        with st.expander("📝 Resume Format Tips"):
            st.markdown("""
            **For best results, ensure your resume includes:**
            - Clear section headings (Skills, Experience, Projects)
            - Bullet points for achievements
            - Technical skills section
            - Project descriptions with technologies used
            """)

# ========================================
# PAGE 3: START INTERVIEW
# ========================================
elif page == "🎤 Start Interview":
    st.title("🎤 AI Interview Simulation")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 🎯 Role: **{job_role}** | Difficulty: **{difficulty}**")
    with col2:
        st.markdown("### ⏱️ Time")
        if 'start_time' not in st.session_state:
            st.session_state.start_time = datetime.now()
        elapsed = (datetime.now() - st.session_state.start_time).seconds
        mins, secs = divmod(elapsed, 60)
        st.markdown(f"**{mins:02d}:{secs:02d}**")

    st.markdown("---")

    # ═══ 3D AVATAR SECTION ═══
    # ═══ 3D AVATAR SECTION ═══
    st.subheader("🤖 Your AI Interviewer")

# Load 3D avatar from local Vite dev server
    st.components.v1.iframe(
    "http://localhost:5173",
    height=600,
    scrolling=False
    )

    st.markdown("---")

    # ═══ QUESTION SECTION ═══
    if 'question_num' not in st.session_state:
        st.session_state.question_num = 1

    # Sample questions database
    questions_db = {
        "Data Scientist": [
            ("Explain the difference between supervised and unsupervised learning.", "ML Fundamentals"),
            ("What is overfitting and how do you prevent it?", "Model Evaluation"),
            ("Describe the bias-variance tradeoff.", "Statistics"),
            ("What feature engineering techniques do you use?", "Data Preprocessing"),
            ("How do you handle imbalanced datasets?", "Data Science"),
            ("Explain how Random Forest works.", "Algorithms"),
            ("What is cross-validation?", "Model Evaluation"),
            ("Describe a data science project you've worked on.", "Experience"),
        ],
        "ML Engineer": [
            ("How do you deploy ML models to production?", "MLOps"),
            ("Explain batch vs online learning.", "ML Systems"),
            ("What is model drift?", "Production ML"),
            ("Describe CI/CD for ML projects.", "MLOps"),
            ("How do you optimize inference speed?", "Performance"),
            ("What experiment tracking tools do you use?", "Tools"),
            ("Explain containerization for ML.", "DevOps"),
            ("How do you monitor production models?", "Monitoring"),
        ],
    }

    role_questions = questions_db.get(job_role, questions_db["Data Scientist"])
    q_idx = min(st.session_state.question_num - 1, len(role_questions) - 1)
    current_q, current_cat = role_questions[q_idx]

    st.subheader(f"❓ Question {st.session_state.question_num} of {len(role_questions)}")

    st.markdown(f"""
    <div class='feature-box'>
        <h3>{current_q}</h3>
        <p style='color: #757575; margin-top: 8px;'>📂 Category: <strong>{current_cat}</strong></p>
    </div>
    """, unsafe_allow_html=True)

    # ═══ ANSWER INPUT ═══
    st.markdown("### 🎙️ Your Answer")

    tab1, tab2 = st.tabs(["🎤 Voice Input", "⌨️ Text Input"])

    with tab1:
        st.info("🚧 Voice recording will be implemented using Whisper!")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔴 Start Recording", use_container_width=True):
                st.warning("Recording feature coming soon!")
        with col2:
            st.button("⏸️ Pause", use_container_width=True, disabled=True)
        with col3:
            st.button("⏹️ Stop", use_container_width=True, disabled=True)

    with tab2:
        answer = st.text_area(
            "Type your answer here:",
            height=150,
            placeholder="Start typing your answer... Be specific and use examples!"
        )

        if st.button("📤 Submit Answer", use_container_width=True):
            if answer:
                st.success("✅ Answer submitted! Moving to next question...")
                st.session_state.question_num = min(
                    st.session_state.question_num + 1, len(role_questions)
                )
                st.balloons()
                st.rerun()
            else:
                st.error("⚠️ Please provide an answer before submitting!")

    st.markdown("---")

    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⏮️ Previous Question",
                     use_container_width=True,
                     disabled=st.session_state.question_num <= 1):
            st.session_state.question_num -= 1
            st.rerun()
    with col2:
        progress = st.session_state.question_num / len(role_questions)
        st.progress(progress, text=f"Progress: {st.session_state.question_num}/{len(role_questions)}")
    with col3:
        if st.button("Next Question ⏭️",
                     use_container_width=True,
                     disabled=st.session_state.question_num >= len(role_questions)):
            st.session_state.question_num += 1
            st.rerun()

# ========================================
# PAGE 4: VIEW RESULTS
# ========================================
elif page == "📊 View Results":
    st.title("📊 Interview Results & Feedback")

    st.markdown("### 🎯 Overall Performance")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Score", "0%", "0%", delta_color="normal")
    with col2:
        st.metric("Questions Answered", "0/8", "0")
    with col3:
        st.metric("Average Time/Question", "0 min", "0")

    st.markdown("---")

    st.subheader("📝 Detailed Feedback")
    st.info("🚧 Complete an interview to see detailed feedback here!")

    with st.expander("👀 Preview: Feedback Format"):
        st.markdown("""
        **Question 1**: Explain supervised learning
        - **Your Score**: 85/100
        - **Strengths**: Clear explanation, good examples
        - **Improvements**: Could mention more algorithms
        - **Suggested Answer**: Supervised learning uses labeled data to train models...
        """)

    st.markdown("---")

    if st.button("📥 Download Full Report (PDF)", use_container_width=True):
        st.warning("Report generation coming soon!")

    if st.button("🔄 Start New Interview", use_container_width=True):
        st.session_state.question_num = 1
        st.session_state.start_time = datetime.now()
        st.success("✅ Session reset! Navigate to 'Start Interview' to begin.")

# ========================================
# FOOTER
# ========================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #757575;'>
    <p>Built with ❤️ | BCA 3rd Year Project |
    <a href='https://github.com/yourusername' target='_blank'>GitHub</a> |
    <a href='https://linkedin.com/in/yourprofile' target='_blank'>LinkedIn</a>
    </p>
</div>
""", unsafe_allow_html=True)
