import streamlit as st
import pandas as pd
from datetime import datetime
import json
import requests
import PyPDF2
import io

st.set_page_config(page_title="AI Interview Prep", page_icon="🎤", layout="wide")

# ═══════════════════════════════════════════════════════════
# GROQ AI CONFIGURATION
# ═══════════════════════════════════════════════════════════
GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"  # Get from https://console.groq.com
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def ai_evaluate_answer(question, answer, keywords):
    """Use Groq AI to evaluate interview answers"""
    
    if not GROQ_API_KEY or GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
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
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
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

# ═══════════════════════════════════════════════════════════
# RESUME PARSING & SCORING
# ═══════════════════════════════════════════════════════════
def parse_resume(uploaded_file):
    """Extract text and skills from PDF resume"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        skills = extract_skills(text)
        experience = extract_experience(text)
        
        return text, skills, experience
    except Exception as e:
        st.error(f"Error parsing resume: {str(e)}")
        return "", [], "Unknown"

def extract_skills(text):
    """Find technical skills in resume"""
    skill_keywords = {
        'Programming': ['python', 'javascript', 'java', 'c++', 'sql', 'r', 'typescript', 'go', 'rust', 'swift'],
        'ML/AI': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'nlp', 'computer vision', 'transformers'],
        'Web': ['react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'html', 'css'],
        'Cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform'],
        'Data': ['pandas', 'numpy', 'sql', 'mongodb', 'postgresql', 'mysql', 'spark', 'hadoop'],
        'Tools': ['git', 'github', 'jenkins', 'ci/cd', 'linux', 'bash']
    }
    
    found_skills = {}
    text_lower = text.lower()
    
    for category, skills in skill_keywords.items():
        found = []
        for skill in skills:
            if skill in text_lower:
                found.append(skill.title())
        if found:
            found_skills[category] = found
    
    return found_skills

def extract_experience(text):
    """Estimate years of experience"""
    import re
    
    patterns = [
        r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
        r'experience[:\s]+(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s+(?:working|in)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    
    return 0

def calculate_resume_score(skills, experience, job_role):
    """Calculate resume match score for job role"""
    
    role_requirements = {
        "Data Scientist": {
            "required_categories": ['Programming', 'ML/AI', 'Data'],
            "bonus_categories": ['Cloud', 'Tools'],
            "min_skills": 8,
            "ideal_experience": 2
        },
        "ML Engineer": {
            "required_categories": ['Programming', 'ML/AI', 'Cloud'],
            "bonus_categories": ['Data', 'Tools'],
            "min_skills": 10,
            "ideal_experience": 3
        },
        "Software Engineer": {
            "required_categories": ['Programming', 'Web'],
            "bonus_categories": ['Cloud', 'Tools', 'Data'],
            "min_skills": 6,
            "ideal_experience": 2
        }
    }
    
    req = role_requirements.get(job_role, role_requirements["Data Scientist"])
    
    score = 0
    max_score = 100
    
    # Category coverage (40 points)
    required_found = sum(1 for cat in req['required_categories'] if cat in skills)
    score += (required_found / len(req['required_categories'])) * 40
    
    # Total skills count (30 points)
    total_skills = sum(len(s) for s in skills.values())
    score += min((total_skills / req['min_skills']) * 30, 30)
    
    # Experience (20 points)
    if experience >= req['ideal_experience']:
        score += 20
    else:
        score += (experience / req['ideal_experience']) * 20
    
    # Bonus categories (10 points)
    bonus_found = sum(1 for cat in req['bonus_categories'] if cat in skills)
    score += (bonus_found / len(req['bonus_categories'])) * 10
    
    return int(score)

# ═══════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════
if 'question_num' not in st.session_state:
    st.session_state.question_num = 1
if 'start_time' not in st.session_state:
    st.session_state.start_time = datetime.now()
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'scores' not in st.session_state:
    st.session_state.scores = []
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'resume_skills' not in st.session_state:
    st.session_state.resume_skills = {}
if 'resume_experience' not in st.session_state:
    st.session_state.resume_experience = 0
if 'resume_score' not in st.session_state:
    st.session_state.resume_score = 0
if 'current_question' not in st.session_state:
    st.session_state.current_question = ""

# ═══════════════════════════════════════════════════════════
# FIXED CSS - HIGH CONTRAST, READABLE TEXT
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
/* Main headers */
.main-header { 
    font-size: 3rem; 
    font-weight: bold; 
    text-align: center; 
    color: #1E88E5; 
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}

.sub-header { 
    text-align: center; 
    color: #666; 
    font-size: 1.2rem; 
    margin-bottom: 2rem; 
}

/* Feature boxes - LIGHT BACKGROUND WITH DARK TEXT */
.feature-box { 
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    padding: 24px; 
    border-radius: 12px; 
    margin: 15px 0; 
    border-left: 5px solid #1E88E5;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* FORCE DARK TEXT IN FEATURE BOXES */
.feature-box h3 { 
    color: #1a1a1a !important; 
    font-weight: 700 !important;
    font-size: 1.3rem !important;
    margin-bottom: 8px !important;
}

.feature-box p { 
    color: #444 !important; 
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    margin: 0 !important;
}

.feature-box strong {
    color: #1E88E5 !important;
}

/* Buttons */
.stButton>button { 
    background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
    color: white !important;
    font-size: 1.0rem; 
    border-radius: 8px; 
    padding: 0.6rem 2rem;
    font-weight: 600;
    border: none;
    box-shadow: 0 4px 6px rgba(30, 136, 229, 0.3);
    transition: all 0.3s;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(30, 136, 229, 0.4);
}

/* Score cards */
.score-card { 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 24px; 
    border-radius: 12px; 
    color: white; 
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.score-card h2 {
    font-size: 2.5rem !important;
    margin: 0 !important;
    font-weight: 700 !important;
}

.score-card p {
    font-size: 0.9rem !important;
    opacity: 0.9;
    margin-top: 8px !important;
}

/* Feedback boxes */
.strength-box { 
    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    padding: 12px 16px; 
    border-radius: 8px; 
    margin: 8px 0; 
    border-left: 4px solid #28a745;
    color: #155724 !important;
    font-weight: 500;
}

.improvement-box { 
    background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
    padding: 12px 16px; 
    border-radius: 8px; 
    margin: 8px 0; 
    border-left: 4px solid #ffc107;
    color: #856404 !important;
    font-weight: 500;
}

/* Skill badges */
.skill-badge { 
    display: inline-block; 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white; 
    padding: 8px 16px; 
    border-radius: 20px; 
    margin: 5px; 
    font-size: 0.9rem;
    font-weight: 600;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

/* Category badge */
.category-badge {
    display: inline-block;
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    color: white;
    padding: 6px 12px;
    border-radius: 15px;
    font-size: 0.85rem;
    font-weight: 600;
    margin-left: 10px;
}

/* Resume score display */
.resume-score-box {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    padding: 30px;
    border-radius: 16px;
    text-align: center;
    color: white;
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    margin: 20px 0;
}

.resume-score-box h1 {
    font-size: 4rem !important;
    margin: 0 !important;
    font-weight: 800 !important;
}

.resume-score-box p {
    font-size: 1.2rem !important;
    opacity: 0.95;
    margin-top: 10px !important;
}

/* Skill category boxes */
.skill-category-box {
    background: white;
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    padding: 16px;
    margin: 10px 0;
}

.skill-category-box h4 {
    color: #1E88E5 !important;
    margin-bottom: 10px !important;
    font-size: 1.1rem !important;
}

/* Progress bars */
.progress-bar {
    background: #e0e0e0;
    border-radius: 10px;
    height: 20px;
    overflow: hidden;
    margin: 10px 0;
}

.progress-fill {
    background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
    height: 100%;
    border-radius: 10px;
    transition: width 0.5s ease;
}

/* Make markdown text readable everywhere */
.stMarkdown {
    color: inherit;
}

/* Text areas */
.stTextArea textarea {
    border: 2px solid #e0e0e0 !important;
    border-radius: 8px !important;
    font-size: 1rem !important;
}

.stTextArea textarea:focus {
    border-color: #1E88E5 !important;
    box-shadow: 0 0 0 2px rgba(30, 136, 229, 0.2) !important;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# QUESTIONS DATABASE (25+ QUESTIONS)
# ═══════════════════════════════════════════════════════════
QUESTIONS_DB = {
    "Data Scientist": {
        "Beginner": [
            {"question": "What is the difference between supervised and unsupervised learning?", "category": "ML Fundamentals", "keywords": ["supervised", "labeled", "unsupervised", "clustering", "classification"]},
            {"question": "Explain overfitting and how to prevent it.", "category": "Model Evaluation", "keywords": ["overfitting", "training", "test", "validation", "regularization", "cross-validation"]},
            {"question": "What is a confusion matrix and what does it tell us?", "category": "Metrics", "keywords": ["confusion", "matrix", "precision", "recall", "true positive", "false positive"]},
            {"question": "Explain the difference between precision and recall.", "category": "Metrics", "keywords": ["precision", "recall", "true positive", "false positive", "false negative"]},
            {"question": "What is cross-validation and why is it important?", "category": "Validation", "keywords": ["cross-validation", "k-fold", "training", "validation", "generalization"]},
            {"question": "Describe the difference between bagging and boosting.", "category": "Ensemble Methods", "keywords": ["bagging", "boosting", "ensemble", "weak learners", "random forest"]},
            {"question": "What is feature scaling and why is it important?", "category": "Preprocessing", "keywords": ["scaling", "normalization", "standardization", "feature", "range"]},
        ],
        "Intermediate": [
            {"question": "Explain the bias-variance tradeoff.", "category": "ML Theory", "keywords": ["bias", "variance", "tradeoff", "underfitting", "overfitting", "generalization"]},
            {"question": "How do you handle imbalanced datasets?", "category": "Data Preprocessing", "keywords": ["imbalanced", "sampling", "SMOTE", "class weights", "oversampling", "undersampling"]},
            {"question": "What is gradient descent and its variants?", "category": "Optimization", "keywords": ["gradient", "descent", "learning rate", "SGD", "Adam", "momentum"]},
            {"question": "Explain feature engineering and its importance.", "category": "Feature Engineering", "keywords": ["feature", "engineering", "transformation", "selection", "scaling"]},
            {"question": "What are ensemble methods in machine learning?", "category": "Algorithms", "keywords": ["ensemble", "bagging", "boosting", "random forest", "voting"]},
            {"question": "Describe the ROC curve and AUC metric.", "category": "Evaluation", "keywords": ["ROC", "AUC", "true positive", "false positive", "threshold"]},
            {"question": "What is regularization and why do we use it?", "category": "Regularization", "keywords": ["regularization", "L1", "L2", "overfitting", "penalty"]},
        ],
        "Advanced": [
            {"question": "Explain the architecture of a Transformer model.", "category": "Deep Learning", "keywords": ["transformer", "attention", "encoder", "decoder", "self-attention"]},
            {"question": "How do you optimize hyperparameters in deep learning?", "category": "Optimization", "keywords": ["hyperparameter", "grid search", "random search", "bayesian", "tuning"]},
        ]
    },
    "ML Engineer": {
        "Beginner": [
            {"question": "What is the difference between batch and online learning?", "category": "ML Systems", "keywords": ["batch", "online", "real-time", "incremental", "streaming"]},
            {"question": "How do you deploy a machine learning model?", "category": "MLOps", "keywords": ["deployment", "API", "docker", "serving", "production"]},
            {"question": "What is model monitoring and why is it important?", "category": "MLOps", "keywords": ["monitoring", "drift", "performance", "metrics", "alerts"]},
            {"question": "Explain the concept of A/B testing for ML models.", "category": "Testing", "keywords": ["A/B", "testing", "control", "treatment", "experiment"]},
        ],
        "Intermediate": [
            {"question": "Explain model versioning and experiment tracking.", "category": "MLOps", "keywords": ["versioning", "experiment", "tracking", "mlflow", "wandb"]},
            {"question": "What is data drift and how do you detect it?", "category": "Production ML", "keywords": ["drift", "distribution", "monitoring", "feature", "statistical"]},
            {"question": "How do you handle model retraining in production?", "category": "MLOps", "keywords": ["retraining", "pipeline", "automated", "triggers", "continuous"]},
        ]
    },
    "Software Engineer": {
        "Beginner": [
            {"question": "What is the difference between a list and a tuple in Python?", "category": "Python Basics", "keywords": ["list", "tuple", "mutable", "immutable", "ordered"]},
            {"question": "Explain object-oriented programming concepts.", "category": "OOP", "keywords": ["OOP", "class", "object", "inheritance", "polymorphism", "encapsulation"]},
            {"question": "What is a REST API?", "category": "Web Development", "keywords": ["REST", "API", "HTTP", "GET", "POST", "endpoint"]},
            {"question": "Explain the difference between SQL and NoSQL databases.", "category": "Databases", "keywords": ["SQL", "NoSQL", "relational", "document", "schema"]},
        ],
        "Intermediate": [
            {"question": "What are design patterns and give examples?", "category": "Software Design", "keywords": ["design patterns", "singleton", "factory", "observer", "strategy"]},
            {"question": "Explain asynchronous programming in Python.", "category": "Concurrency", "keywords": ["async", "await", "coroutine", "asyncio", "concurrent"]},
        ]
    }
}

# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
st.sidebar.title("🎯 Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "📄 Resume", "🎤 Interview", "📊 Results"])

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Settings")

job_role = st.sidebar.selectbox("Role:", ["Data Scientist", "ML Engineer", "Software Engineer"])
difficulty = st.sidebar.select_slider("Difficulty:", ["Beginner", "Intermediate", "Advanced"])

st.sidebar.markdown("---")

# Status indicators
if GROQ_API_KEY and GROQ_API_KEY != "YOUR_GROQ_API_KEY_HERE":
    st.sidebar.success("🤖 AI: Enabled")
else:
    st.sidebar.warning("⚠️ AI: Disabled")

if st.session_state.resume_skills:
    total_skills = sum(len(skills) for skills in st.session_state.resume_skills.values())
    st.sidebar.success(f"📄 Resume: {total_skills} skills")
    st.sidebar.metric("Match Score", f"{st.session_state.resume_score}%")
else:
    st.sidebar.info("📄 Resume: Not uploaded")

# ═══════════════════════════════════════════════════════════
# HOME PAGE
# ═══════════════════════════════════════════════════════════
if page == "🏠 Home":
    st.markdown("<h1 class='main-header'>🎤 AI Interview Prep</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Ace your next interview with AI-powered feedback!</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='feature-box'><h3>📄 Resume Parser</h3><p>Extract skills automatically & get match score</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='feature-box'><h3>🤖 AI Evaluation</h3><p>Smart answer analysis with detailed feedback</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='feature-box'><h3>🎨 3D Avatar</h3><p>Realistic interviewer with voice</p></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    avg = sum(st.session_state.scores) / len(st.session_state.scores) if st.session_state.scores else 0
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Interviews", "1" if len(st.session_state.answers) > 0 else "0")
    col2.metric("Avg Score", f"{avg:.0f}%")
    col3.metric("Answered", len(st.session_state.answers))
    col4.metric("Resume Match", f"{st.session_state.resume_score}%")
    
    st.markdown("---")
    
    st.subheader("🚀 Getting Started")
    st.markdown("""
    <div class='feature-box'>
    <h3>Step-by-Step Guide:</h3>
    <p><strong>1. 📄 Upload Resume</strong> - Get your skills analyzed and match score</p>
    <p><strong>2. ⚙️ Select Settings</strong> - Choose job role and difficulty</p>
    <p><strong>3. 🎤 Start Interview</strong> - Answer questions (avatar will speak!)</p>
    <p><strong>4. 📊 View Results</strong> - Get AI-powered detailed feedback</p>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# RESUME PAGE - WITH SCORING
# ═══════════════════════════════════════════════════════════
elif page == "📄 Resume":
    st.title("📄 Resume Analysis & Scoring")
    
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=['pdf'])
    
    if uploaded_file:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.success(f"✅ Uploaded: {uploaded_file.name}")
            
            if st.button("🔍 Analyze Resume", use_container_width=True):
                with st.spinner("🤖 Analyzing your resume..."):
                    text, skills, experience = parse_resume(uploaded_file)
                    st.session_state.resume_text = text
                    st.session_state.resume_skills = skills
                    st.session_state.resume_experience = experience
                    st.session_state.resume_score = calculate_resume_score(skills, experience, job_role)
                    
                    st.success("✅ Analysis complete!")
                    st.balloons()
                    st.rerun()
        
        with col2:
            if st.button("🗑️ Clear Resume", use_container_width=True):
                st.session_state.resume_text = ""
                st.session_state.resume_skills = {}
                st.session_state.resume_experience = 0
                st.session_state.resume_score = 0
                st.rerun()
    
    # Show results
    if st.session_state.resume_skills:
        st.markdown("---")
        
        # BIG SCORE DISPLAY
        score = st.session_state.resume_score
        score_color = "#4caf50" if score >= 70 else "#ff9800" if score >= 50 else "#f44336"
        
        st.markdown(f"""
        <div class='resume-score-box' style='background: linear-gradient(135deg, {score_color}aa 0%, {score_color} 100%);'>
            <h1>{score}%</h1>
            <p>Resume Match for {job_role}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Recommendation
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Experience", f"{st.session_state.resume_experience}+ years")
        with col2:
            total_skills = sum(len(skills) for skills in st.session_state.resume_skills.values())
            st.metric("Total Skills", total_skills)
        with col3:
            categories = len(st.session_state.resume_skills)
            st.metric("Skill Categories", categories)
        
        st.markdown("---")
        
        # Skills by category
        st.subheader("🏷️ Detected Skills by Category")
        
        for category, skills_list in st.session_state.resume_skills.items():
            with st.expander(f"**{category}** ({len(skills_list)} skills)", expanded=True):
                skills_html = ""
                for skill in skills_list:
                    skills_html += f'<span class="skill-badge">{skill}</span>'
                st.markdown(skills_html, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Recommendations
        st.subheader("💡 Recommendations")
        
        if score >= 80:
            st.markdown("<div class='strength-box'>🌟 <strong>Excellent Match!</strong> Your resume is well-suited for this role. You're ready to interview!</div>", unsafe_allow_html=True)
        elif score >= 60:
            st.markdown("<div class='strength-box'>👍 <strong>Good Match!</strong> Your resume shows relevant experience. Consider highlighting more specific projects.</div>", unsafe_allow_html=True)
        elif score >= 40:
            st.markdown("<div class='improvement-box'>⚠️ <strong>Moderate Match.</strong> Consider adding more relevant skills and projects for this role.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='improvement-box'>❌ <strong>Limited Match.</strong> Focus on building more relevant skills for this role.</div>", unsafe_allow_html=True)
        
        st.success("🎯 Ready for interview! Go to Interview page to start.")

# ═══════════════════════════════════════════════════════════
# INTERVIEW PAGE
# ═══════════════════════════════════════════════════════════
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
    
    # 3D Avatar iframe
    st.subheader("🤖 AI Interviewer")
    st.components.v1.iframe("https://interview-prep-system.vercel.app/", height=600, scrolling=False)
    
    st.markdown("---")
    
    questions = QUESTIONS_DB.get(job_role, {}).get(difficulty, QUESTIONS_DB["Data Scientist"]["Beginner"])
    
    if st.session_state.question_num > len(questions):
        st.success("🎉 Interview Complete!")
        st.info("📊 Check Results page for feedback!")
    else:
        q_idx = st.session_state.question_num - 1
        q = questions[q_idx]
        
        # Store current question for voice trigger
        st.session_state.current_question = q['question']
        
        st.subheader(f"❓ Question {st.session_state.question_num} of {len(questions)}")
        
        # READABLE QUESTION BOX
        st.markdown(f"""
        <div class='feature-box'>
            <h3>{q['question']}</h3>
            <p><strong>Category:</strong> {q['category']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # TTS Button to trigger avatar speech
        if st.button("🔊 Hear Question (Avatar will speak)", use_container_width=True):
            st.info("🎙️ Listen to the avatar in the iframe above!")
            # The frontend will handle the actual TTS
        
        # Answer input
        answer = st.text_area(
            "Your answer:", 
            height=150, 
            key=f"a{st.session_state.question_num}",
            placeholder="Type your detailed answer here. Be specific and use examples!\n\nTip: Aim for at least 50 words for better evaluation."
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("📤 Submit Answer", use_container_width=True, type="primary"):
                if answer and len(answer.strip()) > 10:
                    with st.spinner("🤖 AI is evaluating..."):
                        result = ai_evaluate_answer(q['question'], answer, q['keywords'])
                        
                        st.session_state.answers.append({
                            "q": q['question'],
                            "a": answer,
                            "category": q['category'],
                            "score": result['score'],
                            "strengths": result.get('strengths', []),
                            "improvements": result.get('improvements', []),
                            "feedback": result.get('feedback', '')
                        })
                        st.session_state.scores.append(result['score'])
                        
                        st.success(f"✅ Score: {result['score']}/100")
                        st.info(f"💬 {result['feedback']}")
                        
                        if result.get('strengths'):
                            st.markdown("**✨ Strengths:**")
                            for s in result['strengths']:
                                st.markdown(f"<div class='strength-box'>✓ {s}</div>", unsafe_allow_html=True)
                        
                        if result.get('improvements'):
                            st.markdown("**💡 Improvements:**")
                            for imp in result['improvements']:
                                st.markdown(f"<div class='improvement-box'>→ {imp}</div>", unsafe_allow_html=True)
                        
                        st.session_state.question_num += 1
                        st.balloons()
                        
                        if st.button("➡️ Next Question"):
                            st.rerun()
                else:
                    st.error("⚠️ Please provide a detailed answer (min 10 characters)")
        
        with col2:
            word_count = len(answer.split()) if answer else 0
            st.metric("Words", word_count)
        
        with col3:
            char_count = len(answer) if answer else 0
            st.metric("Characters", char_count)
        
        st.progress(st.session_state.question_num / len(questions))

# ═══════════════════════════════════════════════════════════
# RESULTS PAGE
# ═══════════════════════════════════════════════════════════
elif page == "📊 Results":
    st.title("📊 Interview Performance Report")
    
    if not st.session_state.answers:
        st.warning("⚠️ No interview completed yet!")
        st.info("👈 Start from Interview page!")
    else:
        avg = sum(st.session_state.scores) / len(st.session_state.scores)
        mins = (datetime.now() - st.session_state.start_time).seconds // 60
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='score-card'><h2>{avg:.0f}%</h2><p>Overall Score</p></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='score-card'><h2>{len(st.session_state.answers)}</h2><p>Questions</p></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='score-card'><h2>{mins}</h2><p>Minutes</p></div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.subheader("📈 Performance by Category")
        category_scores = {}
        for ans in st.session_state.answers:
            cat = ans.get('category', 'General')
            if cat not in category_scores:
                category_scores[cat] = []
            category_scores[cat].append(ans['score'])
        
        category_avg = {cat: sum(scores)/len(scores) for cat, scores in category_scores.items()}
        df = pd.DataFrame(list(category_avg.items()), columns=['Category', 'Average Score'])
        st.bar_chart(df.set_index('Category'))
        
        st.markdown("---")
        
        st.subheader("📝 Question-by-Question Analysis")
        
        for i, ans in enumerate(st.session_state.answers, 1):
            with st.expander(f"Q{i}: {ans['q'][:60]}... | Score: {ans['score']}/100"):
                st.markdown(f"**📋 Question:** {ans['q']}")
                st.markdown(f"**📂 Category:** {ans.get('category', 'General')}")
                st.markdown(f"**✍️ Your Answer:** {ans['a']}")
                st.markdown(f"**🎯 Score:** {ans['score']}/100")
                
                if ans.get('feedback'):
                    st.info(f"💬 {ans['feedback']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if ans.get('strengths'):
                        st.markdown("**✨ Strengths:**")
                        for s in ans['strengths']:
                            st.markdown(f"- ✓ {s}")
                
                with col2:
                    if ans.get('improvements'):
                        st.markdown("**💡 Improvements:**")
                        for imp in ans['improvements']:
                            st.markdown(f"- → {imp}")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_data = {
                "interview_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "job_role": job_role,
                "difficulty": difficulty,
                "overall_score": round(avg, 2),
                "total_questions": len(st.session_state.answers),
                "time_taken_minutes": mins,
                "resume_match_score": st.session_state.resume_score,
                "answers": st.session_state.answers
            }
            
            st.download_button(
                "📥 Download Report (JSON)",
                data=json.dumps(report_data, indent=2),
                file_name=f"interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            if st.button("🔄 Start New Interview", use_container_width=True):
                st.session_state.question_num = 1
                st.session_state.answers = []
                st.session_state.scores = []
                st.session_state.start_time = datetime.now()
                st.success("✅ Reset complete!")
                st.rerun()

st.markdown("---")
st.markdown("<div style='text-align:center;color:#888'><p>Built with ❤️ | React + Streamlit + Groq AI | BCA Final Year Project 2025</p></div>", unsafe_allow_html=True)