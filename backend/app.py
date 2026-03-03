import streamlit as st
import pandas as pd
from datetime import datetime
import json
import requests
import PyPDF2
import io
import os
import re
import random
import time
import sqlite3
import hashlib
from dotenv import load_dotenv

st.set_page_config(page_title="AI Interview Prep", page_icon="🎤", layout="wide")

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173") 

# ═══════════════════════════════════════════════════════════
# SQLITE DATABASE FOR PERSISTENT MEMORY
# ═══════════════════════════════════════════════════════════
def init_database():
    """Initialize SQLite database for persistent memory"""
    conn = sqlite3.connect('interview_memory.db')
    c = conn.cursor()
    
    # Table for conversation history
    c.execute('''CREATE TABLE IF NOT EXISTS conversations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT,
                  timestamp DATETIME,
                  question TEXT,
                  answer TEXT,
                  category TEXT)''')
    
    # Table for session history
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT UNIQUE,
                  job_role TEXT,
                  difficulty TEXT,
                  mode TEXT,
                  overall_score REAL,
                  completed_at DATETIME)''')
    
    # Table for performance tracking
    c.execute('''CREATE TABLE IF NOT EXISTS performance
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT,
                  question TEXT,
                  answer TEXT,
                  score INTEGER,
                  rubric_scores TEXT,
                  feedback TEXT,
                  time_taken INTEGER)''')
    
    conn.commit()
    conn.close()

# Initialize on startup
init_database()

def save_conversation(session_id, question, answer, category):
    """Save conversation to database"""
    conn = sqlite3.connect('interview_memory.db')
    c = conn.cursor()
    c.execute('''INSERT INTO conversations (session_id, timestamp, question, answer, category)
                 VALUES (?, ?, ?, ?, ?)''',
              (session_id, datetime.now(), question, answer, category))
    conn.commit()
    conn.close()

def save_session(session_id, job_role, difficulty, mode, overall_score):
    """Save completed session"""
    conn = sqlite3.connect('interview_memory.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO sessions 
                 (session_id, job_role, difficulty, mode, overall_score, completed_at)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (session_id, job_role, difficulty, mode, overall_score, datetime.now()))
    conn.commit()
    conn.close()

def save_performance(session_id, question, answer, score, rubric_scores, feedback, time_taken):
    """Save individual question performance"""
    conn = sqlite3.connect('interview_memory.db')
    c = conn.cursor()
    c.execute('''INSERT INTO performance 
                 (session_id, question, answer, score, rubric_scores, feedback, time_taken)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (session_id, question, answer, score, json.dumps(rubric_scores), feedback, time_taken))
    conn.commit()
    conn.close()

def load_session_history():
    """Load all previous sessions"""
    conn = sqlite3.connect('interview_memory.db')
    c = conn.cursor()
    c.execute('''SELECT session_id, job_role, difficulty, overall_score, completed_at 
                 FROM sessions ORDER BY completed_at DESC''')
    sessions = c.fetchall()
    conn.close()
    return sessions

def get_conversation_context(session_id, limit=5):
    """Get recent conversation history"""
    conn = sqlite3.connect('interview_memory.db')
    c = conn.cursor()
    c.execute('''SELECT question, answer FROM conversations 
                 WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?''',
              (session_id, limit))
    history = c.fetchall()
    conn.close()
    return [{"q": h[0], "a": h[1]} for h in reversed(history)]

# ═══════════════════════════════════════════════════════════
# GROQ AI WITH MEMORY
# ═══════════════════════════════════════════════════════════
def call_groq_api(prompt, temperature=0.7, max_tokens=1500):
    if not GROQ_API_KEY:
        return None
    
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        # ✅ BUG 1 FIXED: Was using FRONTEND_URL (Vercel) instead of Groq's actual API endpoint
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except Exception as e:
        return None

def generate_personalized_questions(job_role, difficulty, resume_skills, conversation_history, num_questions=5):
    """Generate questions with conversation memory"""
    
    random_seed = random.randint(1, 1000)
    
    # Build conversation context
    conv_context = ""
    if conversation_history:
        conv_context = "Previous conversation:\n"
        for item in conversation_history[-3:]:
            conv_context += f"Q: {item['q']}\nA: {item['a'][:200]}...\n"
    
    # Build resume context
    resume_context = ""
    if resume_skills:
        all_skills = []
        for cat, skills in resume_skills.items():
            all_skills.extend(skills)
        resume_context = f"Candidate has these skills: {', '.join(all_skills[:10])}\n"
    
    job_contexts = {
        "Data Scientist": "ML algorithms, statistics, Python/R, data preprocessing, model evaluation",
        "Frontend Developer": "React/Vue/Angular, JavaScript/TypeScript, CSS, performance, accessibility",
        "Backend Developer": "APIs, databases, architecture, authentication, caching, microservices",
        "DevOps Engineer": "CI/CD, Docker, Kubernetes, AWS/Azure, monitoring, automation",
        "ML Engineer": "Model deployment, MLOps, production ML, scalability, Docker/Kubernetes",
        "Full Stack Developer": "Frontend + Backend, databases, REST APIs, deployment",
        "Mobile Developer (iOS/Android)": "Swift/Kotlin, React Native/Flutter, mobile UI/UX, app deployment",
        "Cloud Engineer (AWS/Azure/GCP)": "Cloud services, EC2, S3, Lambda, cloud architecture",
        "QA Engineer": "Test automation, Selenium, testing frameworks, CI/CD integration",
        "Cybersecurity Analyst": "Security threats, penetration testing, network security, encryption",
        "Database Administrator": "SQL optimization, database design, backup/recovery, performance",
        "UI/UX Designer": "User research, wireframing, prototyping, Figma/Sketch, design systems",
    }
    
    context = job_contexts.get(job_role, "technical skills and problem-solving")
    
    prompt = f"""You are an expert technical interviewer for a {job_role} position.

{resume_context}

{conv_context}

Generate {num_questions} UNIQUE interview questions:

REQUIREMENTS:
1. Questions MUST be specific to {job_role}: {context}
2. Reference previous conversation if available
3. Target skills from resume AND identify gaps
4. Mix question types: conceptual, practical, debugging, tradeoff
5. Difficulty: {difficulty}

Seed: {random_seed}

Return ONLY JSON array:
[
  {{"question": "...", "category": "...", "keywords": ["...", "...", "...", "...", "..."], "type": "conceptual|practical|debugging|tradeoff"}}
]"""

    response = call_groq_api(prompt, temperature=0.85, max_tokens=2000)
    
    if response:
        try:
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                questions = json.loads(json_match.group())
                if len(questions) >= num_questions:
                    return questions[:num_questions]
        except:
            pass
    
    return get_default_questions(job_role)

def evaluate_with_rubric(question, answer, keywords, question_type="conceptual"):
    """AI evaluation with detailed rubric"""
    
    if not GROQ_API_KEY or not answer or len(answer.strip()) < 10:
        return keyword_rubric_evaluate(answer, keywords)
    
    prompt = f"""Evaluate this technical interview answer using a detailed rubric.

Question: {question}
Type: {question_type}
Expected keywords: {', '.join(keywords)}
Candidate's Answer: {answer}

SCORING RUBRIC (total 100):
1. Correctness (0-40): Technical accuracy
2. Depth (0-25): Detail, examples, edge cases
3. Clarity (0-15): Well-organized, easy to follow
4. Structure (0-10): Logical flow
5. Real-world (0-10): Practical examples

Return JSON:
{{
  "total_score": <0-100>,
  "rubric": {{"correctness": <0-40>, "depth": <0-25>, "clarity": <0-15>, "structure": <0-10>, "real_world": <0-10>}},
  "strengths": ["...", "..."],
  "improvements": ["...", "..."],
  "ideal_answer_outline": ["point 1", "point 2", "point 3"],
  "rewritten_answer": "Professional version...",
  "feedback": "Overall feedback",
  "needs_followup": true|false,
  "followup_question": "Optional follow-up"
}}"""

    response = call_groq_api(prompt, temperature=0.3, max_tokens=1500)
    
    if response:
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
    
    return keyword_rubric_evaluate(answer, keywords)

def keyword_rubric_evaluate(answer, keywords):
    """Fallback rubric scoring"""
    if not answer or len(keywords) == 0:
        return {
            "total_score": 0,
            "rubric": {"correctness": 0, "depth": 0, "clarity": 0, "structure": 0, "real_world": 0},
            "strengths": [],
            "improvements": ["Please provide an answer"],
            "ideal_answer_outline": ["Address key concepts", "Provide examples"],
            "rewritten_answer": "",
            "feedback": "No answer provided",
            "needs_followup": False
        }
    
    matched = sum(1 for kw in keywords if kw.lower() in answer.lower())
    base_score = int((matched / len(keywords)) * 100)
    
    return {
        "total_score": base_score,
        "rubric": {
            "correctness": int(base_score * 0.4),
            "depth": int(base_score * 0.25),
            "clarity": int(base_score * 0.15),
            "structure": int(base_score * 0.1),
            "real_world": int(base_score * 0.1)
        },
        "strengths": [f"Mentioned {matched}/{len(keywords)} key concepts"] if matched > 0 else [],
        "improvements": [f"Consider: {', '.join([k for k in keywords if k.lower() not in answer.lower()][:3])}"],
        "ideal_answer_outline": [f"Explain {kw}" for kw in keywords[:3]],
        "rewritten_answer": f"A strong answer would cover: {', '.join(keywords)}",
        "feedback": "👍 Good" if base_score >= 60 else "⚠️ Needs detail",
        "needs_followup": base_score < 50
    }

def get_default_questions(job_role):
    """Fallback questions"""
    defaults = {
        "Data Scientist": [
            {"question": "Explain bias-variance tradeoff in ML", "category": "ML Theory", "keywords": ["bias", "variance", "overfitting", "underfitting"], "type": "conceptual"},
            {"question": "How do you handle imbalanced datasets?", "category": "Data", "keywords": ["imbalanced", "SMOTE", "oversampling"], "type": "practical"},
        ],
        "Frontend Developer": [
            {"question": "Explain React hooks lifecycle", "category": "React", "keywords": ["hooks", "useState", "useEffect", "lifecycle"], "type": "conceptual"},
            {"question": "How do you optimize React performance?", "category": "Performance", "keywords": ["memoization", "lazy loading", "splitting"], "type": "practical"},
        ],
    }
    return defaults.get(job_role, defaults["Data Scientist"])

def generate_improvement_plan(scores, job_role):
    """Generate 7-day plan"""
    if not GROQ_API_KEY:
        return [{"day": i+1, "focus": f"Day {i+1}: Practice", "tasks": ["Review concepts"], "resources": ["Online"]} for i in range(7)]
    
    prompt = f"""Create a 7-day improvement plan for {job_role} based on:
{json.dumps(scores, indent=2)}

Return JSON array:
[{{"day": 1, "focus": "topic", "tasks": ["task1", "task2"], "resources": ["resource1"]}}]"""

    response = call_groq_api(prompt, temperature=0.7, max_tokens=1000)
    
    if response:
        try:
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
    
    return [{"day": i+1, "focus": f"Day {i+1}", "tasks": ["Practice"], "resources": ["Online"]} for i in range(7)]

def get_intro_questions(job_role):
    return [
        {"question": f"Good morning! Welcome to our {job_role} interview. Please introduce yourself and tell me about your background.", "category": "Introduction", "keywords": ["name", "background"], "is_intro": True},
        {"question": f"What specifically interests you about the {job_role} position?", "category": "Motivation", "keywords": ["interest", "motivation"], "is_intro": True},
        {"question": "Walk me through a recent project you're proud of.", "category": "Project", "keywords": ["project", "achievement"], "is_intro": True}
    ]

IT_JOB_ROLES = [
    "Data Scientist", "ML Engineer", "AI/ML Researcher", "Data Engineer", "Data Analyst",
    "Frontend Developer", "Backend Developer", "Full Stack Developer", "DevOps Engineer",
    "Cloud Engineer (AWS/Azure/GCP)", "Software Engineer", "QA Engineer",
    "Cybersecurity Analyst", "Database Administrator", "Mobile Developer (iOS/Android)",
    "UI/UX Designer", "Product Manager (Tech)", "Solutions Architect", "SRE",
    "Blockchain Developer", "NLP Engineer", "Computer Vision Engineer"
]

INTERVIEW_MODES = {
    "Practice Mode": "Hints allowed, ideal answers shown",
    "Strict Interview": "Timed, feedback at end only",
    "Company Style": "Customize to specific patterns"
}

# ═══════════════════════════════════════════════════════════
# RESUME PARSING
# ═══════════════════════════════════════════════════════════
def parse_resume(uploaded_file):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        text = "".join([page.extract_text() for page in pdf_reader.pages])
        return text, extract_skills(text), extract_experience(text)
    except:
        return "", {}, 0

def extract_skills(text):
    skill_keywords = {
        'Programming': ['python', 'javascript', 'java', 'c++', 'sql'],
        'ML/AI': ['machine learning', 'tensorflow', 'pytorch'],
        'Web': ['react', 'angular', 'vue', 'node.js'],
        'Cloud': ['aws', 'azure', 'gcp', 'docker'],
        'Data': ['pandas', 'numpy', 'mongodb'],
        'Tools': ['git', 'jenkins', 'linux']
    }
    
    found_skills = {}
    text_lower = text.lower()
    
    for category, skills in skill_keywords.items():
        found = [skill.title() for skill in skills if skill in text_lower]
        if found:
            found_skills[category] = found
    
    return found_skills

def extract_experience(text):
    import re
    match = re.search(r'(\d+)\+?\s*years?\s+(?:of\s+)?experience', text.lower())
    return int(match.group(1)) if match else 0



ROLE_REQUIRED_SKILLS = {
    "Data Scientist": {
        "must_have": ["python", "statistics", "machine learning", "sql"],
        "preferred": ["pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "r"],
        "bonus": ["spark", "hadoop", "aws", "azure", "docker"],
        "min_experience": 2
    },
    "Frontend Developer": {
        "must_have": ["javascript", "html", "css", "react"],
        "preferred": ["typescript", "vue", "angular", "webpack", "git"],
        "bonus": ["nextjs", "redux", "testing", "accessibility"],
        "min_experience": 1
    },
    "Backend Developer": {
        "must_have": ["python", "sql", "api", "database"],
        "preferred": ["node.js", "django", "flask", "postgresql", "mongodb"],
        "bonus": ["microservices", "docker", "kubernetes", "redis"],
        "min_experience": 2
    },
    "ML Engineer": {
        "must_have": ["python", "machine learning", "docker"],
        "preferred": ["tensorflow", "pytorch", "mlops", "kubernetes"],
        "bonus": ["aws", "azure", "monitoring", "ci/cd"],
        "min_experience": 2
    },
    "DevOps Engineer": {
        "must_have": ["linux", "docker", "ci/cd"],
        "preferred": ["kubernetes", "aws", "azure", "terraform", "ansible"],
        "bonus": ["monitoring", "prometheus", "grafana"],
        "min_experience": 2
    },
    "Full Stack Developer": {
        "must_have": ["javascript", "python", "sql", "react"],
        "preferred": ["node.js", "typescript", "mongodb", "postgresql"],
        "bonus": ["aws", "docker", "testing"],
        "min_experience": 2
    },
    "Mobile Developer (iOS/Android)": {
        "must_have": ["swift", "kotlin", "mobile"],
        "preferred": ["react native", "flutter", "ios", "android"],
        "bonus": ["firebase", "app store", "play store"],
        "min_experience": 1
    },
    "Cloud Engineer (AWS/Azure/GCP)": {
        "must_have": ["aws", "cloud", "linux"],
        "preferred": ["azure", "gcp", "terraform", "kubernetes"],
        "bonus": ["lambda", "s3", "ec2", "monitoring"],
        "min_experience": 2
    },
}

# Common skill synonyms/aliases (helps realism)
_SKILL_ALIASES = {
    "machine learning": ["ml", "machine-learning"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "node.js": ["node", "nodejs"],
    "ci/cd": ["cicd", "ci cd", "continuous integration", "continuous delivery"],
    "kubernetes": ["k8s"],
    "amazon web services": ["aws"],
    "postgresql": ["postgres", "postgre"],
    "react native": ["react-native"],
    "tensorflow": ["tf"],
    "pytorch": ["torch"],
}

def _normalize_text(s: str) -> str:
    s = (s or "").lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9\.\+\-\s/]", " ", s)  # keep . + - / for things like node.js, ci/cd
    s = re.sub(r"\s+", " ", s).strip()
    return f" {s} "  # pad for safer "in" checks

def _skill_present(text: str, skill: str) -> bool:
    """Checks if a skill or any of its aliases appear in normalized text."""
    skill_n = _normalize_text(skill).strip()
    if f" {skill_n} " in text:
        return True
    for alias in _SKILL_ALIASES.get(skill_n, []):
        alias_n = _normalize_text(alias).strip()
        if f" {alias_n} " in text:
            return True
    return False

def calculate_resume_score(resume_text: str, skills: dict, experience: int, job_role: str) -> int:
    """
    Role-aware resume scoring.
    Uses extracted skills + experience.
    Output range: 18-92 (more realistic than 0-100).
    Deterministic for same (skills, exp, role).
    """

    requirements = ROLE_REQUIRED_SKILLS.get(job_role, {
        "must_have": ["programming"],
        "preferred": [],
        "bonus": [],
        "min_experience": 1
    })

    # Flatten extracted skills safely
    all_resume_skills = []
    if isinstance(skills, dict):
        for _, skill_list in skills.items():
            if isinstance(skill_list, list):
                all_resume_skills.extend([str(s) for s in skill_list if s])

    # Build normalized search text from extracted skill list
    resume_text = _normalize_text(resume_text)

    # If resume had almost no detected skills, keep it low but not zero
    detected_skill_count = len(all_resume_skills)

    # -----------------------------
    # Scoring components (0..100-ish internal, then clamp)
    # -----------------------------
    score = 0

    # A) Must-have skills (max 44)
    # Strong penalty for missing must-haves
    must_have = requirements["must_have"]
    must_found = 0
    for sk in must_have:
        if _skill_present(resume_text, sk):
            must_found += 1

    if len(must_have) > 0:
        must_ratio = must_found / len(must_have)
    else:
        must_ratio = 0.0

    # Base must score
    must_score = int(44 * must_ratio)

    # Extra penalty if many missing
    missing = len(must_have) - must_found
    must_score -= missing * 6  # -6 per missing must-have
    must_score = max(0, must_score)
    score += must_score

    # B) Preferred skills (max 28)
    preferred = requirements["preferred"]
    pref_found = 0
    for sk in preferred:
        if _skill_present(resume_text, sk):
            pref_found += 1
    # up to 28 points
    pref_score = min(28, pref_found * 4)
    score += pref_score

    # C) Bonus skills (max 10)
    bonus = requirements["bonus"]
    bonus_found = 0
    for sk in bonus:
        if _skill_present(resume_text, sk):
            bonus_found += 1
    bonus_score = min(10, bonus_found * 2)
    score += bonus_score

    # D) Experience (max 18)
    exp = max(0, int(experience or 0))
    min_exp = int(requirements.get("min_experience", 1))

    if exp >= min_exp + 4:
        exp_score = 18
    elif exp >= min_exp + 2:
        exp_score = 15
    elif exp >= min_exp:
        exp_score = 12
    elif exp == max(min_exp - 1, 0):
        exp_score = 9
    else:
        exp_score = 6
    score += exp_score

    # E) “Completeness” nudge (0..6)
    # Prevents all roles always getting 55% when resume has many skills
    if detected_skill_count >= 12:
        score += 6
    elif detected_skill_count >= 8:
        score += 4
    elif detected_skill_count >= 4:
        score += 2
    else:
        score += 0

    # F) Small deterministic jitter (-2..+2) so scores don't look "robotic"
    # but still deterministic per resume+role+exp.
    seed_str = f"{job_role}|{exp}|{'|'.join(sorted([s.lower() for s in all_resume_skills]))}"
    h = hashlib.md5(seed_str.encode("utf-8")).hexdigest()
    jitter = (int(h[:2], 16) % 5) - 2  # -2..+2
    score += jitter

    # -----------------------------
    # Final clamp (realistic range)
    # -----------------------------
    final_score = max(18, min(92, score))
    return int(final_score)
# ═══════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
if 'interview_stage' not in st.session_state:
    st.session_state.interview_stage = 'not_started'
if 'question_num' not in st.session_state:
    st.session_state.question_num = 0
if 'start_time' not in st.session_state:
    st.session_state.start_time = datetime.now()
if 'question_start_time' not in st.session_state:
    st.session_state.question_start_time = None
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'scores' not in st.session_state:
    st.session_state.scores = []
if 'rubric_scores' not in st.session_state:
    st.session_state.rubric_scores = []
if 'resume_skills' not in st.session_state:
    st.session_state.resume_skills = {}
if 'resume_experience' not in st.session_state:
    st.session_state.resume_experience = 0
if 'resume_score' not in st.session_state:
    st.session_state.resume_score = 0
if 'technical_questions' not in st.session_state:
    st.session_state.technical_questions = []
if 'intro_questions' not in st.session_state:
    st.session_state.intro_questions = []
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'interview_mode' not in st.session_state:
    st.session_state.interview_mode = "Practice Mode"

# ═══════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
.main-header { font-size: 3rem; font-weight: bold; text-align: center; color: #1E88E5; }
.feature-box { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    padding: 24px; border-radius: 12px; margin: 15px 0; border-left: 5px solid #1E88E5; }
.feature-box h3 { color: #1a1a1a !important; font-weight: 700 !important; }
.stButton>button { background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
    color: white !important; border-radius: 8px; padding: 0.6rem 2rem; font-weight: 600; }
.score-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 24px; border-radius: 12px; color: white; text-align: center; }
.ideal-answer { background: #e8f5e9; border-left: 4px solid #4caf50;
    padding: 16px; border-radius: 8px; margin: 10px 0; }
.rewritten-answer { background: #e3f2fd; border-left: 4px solid #2196f3;
    padding: 16px; border-radius: 8px; margin: 10px 0; }
.timer-warning { background: #fff3cd; color: #856404; padding: 12px;
    border-radius: 8px; margin: 10px 0; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
st.sidebar.title("🎯 Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "📄 Resume", "🎤 Interview","🎙️ Voice Interview", "📊 Results", "📈 Progress"])

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Settings")

job_role = st.sidebar.selectbox("Position:", IT_JOB_ROLES)
difficulty = st.sidebar.select_slider("Level:", ["Beginner", "Intermediate", "Advanced"])
interview_mode = st.sidebar.selectbox("Mode:", list(INTERVIEW_MODES.keys()))
st.sidebar.caption(INTERVIEW_MODES[interview_mode])

st.sidebar.markdown("---")

if GROQ_API_KEY:
    st.sidebar.success("🤖 AI: Active")
    st.sidebar.caption("✅ SQLite Memory\n✅ Adaptive Q's\n✅ Rubric Scoring")
else:
    st.sidebar.warning("⚠️ AI: Limited")

# ═══════════════════════════════════════════════════════════
# PAGES
# ═══════════════════════════════════════════════════════════
if page == "🏠 Home":
    st.markdown("<h1 class='main-header'>🎤 AI-Powered Interview Preparation System</h1>", unsafe_allow_html=True)
    
    # ✅ IMPROVED FEATURE CARDS (GOAL 1)
    st.markdown("""
    <style>
    .feature-card {
        background: linear-gradient(145deg, #1e293b 0%, #334155 100%);
        border-radius: 16px;
        padding: 32px 24px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(148, 163, 184, 0.1);
        transition: all 0.3s ease;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        cursor: default;
        pointer-events: none;
    }
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(96, 165, 250, 0.2);
    }
    .feature-card h3 {
        color: #60a5fa !important;
        font-size: 1.5rem !important;
        margin-bottom: 12px !important;
        font-weight: 600 !important;
    }
    .feature-card p {
        color: #cbd5e1;
        font-size: 1rem;
        line-height: 1.6;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="large")
    
    with col1:
        st.markdown("""
        <div class='feature-card'>
            <h3>💾 SQLite Memory</h3>
            <p>Persistent conversation history across all sessions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='feature-card'>
            <h3>🎯 Adaptive AI</h3>
            <p>Questions personalized to your background</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='feature-card'>
            <h3>📊 5-Factor Rubric</h3>
            <p>Detailed scoring across multiple dimensions</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show stats from database (keep existing code)
    sessions = load_session_history()
    if sessions:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sessions", len(sessions))
        if len(sessions) > 0:
            col2.metric("Latest Score", f"{sessions[0][3]:.0f}%")
        if len(sessions) > 1:
            improvement = sessions[0][3] - sessions[-1][3]
            col3.metric("Improvement", f"{improvement:+.0f}%")

elif page == "📄 Resume":
    st.title("📄 Resume Analysis")
    
    uploaded = st.file_uploader("Upload PDF", type=['pdf'])
    
    if uploaded and st.button("🔍 Analyze"):
        with st.spinner("Analyzing..."):
            text, skills, exp = parse_resume(uploaded)
            st.session_state.resume_skills = skills
            st.session_state.resume_experience = exp
            st.session_state.resume_score = calculate_resume_score(text,skills, exp, job_role)
            st.balloons()
            st.rerun()
    
    if st.session_state.resume_skills:
        score = st.session_state.resume_score
        st.markdown(f"<div class='score-card'><h2>{score}%</h2><p>{job_role} Match</p></div>", unsafe_allow_html=True)

elif page == "🎤 Interview":
    st.title("🎤 Professional Interview")
    
    # ✅ ADD RESTART BUTTON (GOAL 3)
    if st.session_state.interview_stage != 'not_started':
        col_restart, col_spacer = st.columns([1, 5])
        with col_restart:
            if st.button("🔄 Restart", width=True):
                st.session_state.interview_stage = 'not_started'
                st.session_state.question_num = 0
                st.session_state.answers = []
                st.session_state.scores = []
                st.session_state.rubric_scores = []
                st.session_state.technical_questions = []
                st.session_state.intro_questions = []
                st.session_state.conversation_history = []
                st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                st.rerun()
    
    # ✅ IMPROVED QUESTION CARD CSS (GOAL 3)
    st.markdown("""
    <style>
    .question-card {
        background: linear-gradient(145deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 28px;
        margin: 20px 0;
        border-left: 5px solid #3b82f6;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
    .question-card h3 {
        color: #f1f5f9 !important;
        font-size: 1.3rem !important;
        line-height: 1.6 !important;
        margin-bottom: 16px !important;
        font-weight: 500 !important;
    }
    .question-card p {
        color: #94a3b8;
        font-size: 0.95rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### 🎯 {job_role}")
    with col2:
        # ✅ FIXED TIMER (GOAL 3)
        if st.session_state.interview_stage != 'not_started':
            elapsed = (datetime.now() - st.session_state.start_time).seconds
            st.markdown(f"### ⏱️ {elapsed//60:02d}:{elapsed%60:02d}")
        else:
            st.markdown(f"### ⏱️ --:--")
    with col3:
        if st.session_state.question_start_time and st.session_state.interview_stage != 'not_started':
            st.markdown(f"### 🕐 {(datetime.now() - st.session_state.question_start_time).seconds}s")
    
    st.markdown("---")
    
    # 3D AVATAR (keep existing iframe)
    st.subheader("🤖 AI Interviewer")
    st.components.v1.iframe(FRONTEND_URL, height=600, scrolling=False)
    
    st.markdown("---")
    
    if st.session_state.interview_stage == 'not_started':
        st.markdown(f"""<div class='feature-box'><h3>Interview Structure:</h3>
        <p><strong>Round 1:</strong> Introduction (3 questions)</p>
        <p><strong>Round 2:</strong> Technical (5 adaptive questions)</p>
        <p><strong>Memory:</strong> Stored in SQLite for learning</p></div>""", unsafe_allow_html=True)
        
        if st.button("🚀 START", width=True, type="primary"):
            st.session_state.interview_stage = 'intro'
            st.session_state.question_num = 1
            st.session_state.start_time = datetime.now()
            st.session_state.question_start_time = datetime.now()
            st.session_state.intro_questions = get_intro_questions(job_role)
            st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.rerun()
    
    elif st.session_state.interview_stage == 'intro':
        intro_qs = st.session_state.intro_questions
        
        if st.session_state.question_num <= len(intro_qs):
            q = intro_qs[st.session_state.question_num - 1]
            
            st.subheader(f"Introduction - Q{st.session_state.question_num}/{len(intro_qs)}")
            st.markdown(f"""
    <div class='question-card'>
        <h3>{q['question']}</h3>
    </div>
    """, unsafe_allow_html=True)
            
            answer = st.text_area("Your Answer:", height=120, key=f"intro_{st.session_state.question_num}")
            
            if st.button("📤 Submit", width=True, type="primary"):
                if answer and len(answer.strip()) > 10:
                    answer_time = (datetime.now() - st.session_state.question_start_time).seconds if st.session_state.question_start_time else 0
                    
                    # Save to SQLite
                    save_conversation(st.session_state.session_id, q['question'], answer, q['category'])
                    
                    st.session_state.conversation_history.append({"q": q['question'], "a": answer})
                    st.session_state.answers.append({
                        "q": q['question'], "a": answer, "category": q['category'],
                        "is_intro": True, "time_taken": answer_time
                    })
                    
                    st.session_state.question_num += 1
                    st.session_state.question_start_time = datetime.now()
                    
                    if st.session_state.question_num > len(intro_qs):
                        st.session_state.interview_stage = 'technical'
                        st.session_state.question_num = 1
                        
                        with st.spinner("Generating questions..."):
                            # Get conversation from database
                            context = get_conversation_context(st.session_state.session_id)
                            st.session_state.technical_questions = generate_personalized_questions(
                                job_role, difficulty, st.session_state.resume_skills, context, 5
                            )
                        st.success("✅ Generated with memory!")
                    
                    st.rerun()
    
    elif st.session_state.interview_stage == 'technical':
        questions = st.session_state.technical_questions
        
        if st.session_state.question_num <= len(questions):
            q = questions[st.session_state.question_num - 1]
            
            st.subheader(f"Technical - Q{st.session_state.question_num}/{len(questions)}")
            st.markdown(f"""
    <div class='question-card'>
        <h3>{q['question']}</h3>
        <p><strong>Type:</strong> {q.get('type', 'conceptual').title()}</p>
    </div>
    """, unsafe_allow_html=True)
            
            answer = st.text_area("Your Answer:", height=150, key=f"tech_{st.session_state.question_num}")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("📤 Submit", width=True, type="primary"):
                    if answer and len(answer.strip()) > 15:
                        answer_time = (datetime.now() - st.session_state.question_start_time).seconds if st.session_state.question_start_time else 0
                        
                        with st.spinner("Evaluating..."):
                            result = evaluate_with_rubric(q['question'], answer, q['keywords'], q.get('type'))
                            
                            # Save to SQLite
                            save_conversation(st.session_state.session_id, q['question'], answer, q['category'])
                            save_performance(st.session_state.session_id, q['question'], answer, 
                                           result['total_score'], result['rubric'], 
                                           result['feedback'], answer_time)
                            
                            st.session_state.answers.append({
                                "q": q['question'], "a": answer, "category": q['category'],
                                "score": result['total_score'], "rubric": result['rubric'],
                                "strengths": result['strengths'], "improvements": result['improvements'],
                                "ideal_answer": result.get('ideal_answer_outline', []),
                                "rewritten": result.get('rewritten_answer', ''),
                                "feedback": result['feedback'], "time_taken": answer_time
                            })
                            st.session_state.scores.append(result['total_score'])
                            st.session_state.rubric_scores.append(result['rubric'])
                            
                            # Show feedback
                            st.success(f"✅ Score: {result['total_score']}/100")
                            
                            cols = st.columns(5)
                            r = result['rubric']
                            cols[0].metric("Correct", f"{r['correctness']}/40")
                            cols[1].metric("Depth", f"{r['depth']}/25")
                            cols[2].metric("Clarity", f"{r['clarity']}/15")
                            cols[3].metric("Structure", f"{r['structure']}/10")
                            cols[4].metric("Real", f"{r['real_world']}/10")
                            
                            if result.get('ideal_answer_outline'):
                                st.markdown("<div class='ideal-answer'>" + "<br>".join([f"• {p}" for p in result['ideal_answer_outline']]) + "</div>", unsafe_allow_html=True)
                            
                            if result.get('rewritten_answer'):
                                st.markdown(f"<div class='rewritten-answer'>{result['rewritten_answer']}</div>", unsafe_allow_html=True)
                            
                            st.session_state.question_num += 1
                            st.session_state.question_start_time = datetime.now()
                            
                            if st.session_state.question_num > len(questions):
                                st.session_state.interview_stage = 'complete'
                                # Save session
                                avg = sum(st.session_state.scores) / len(st.session_state.scores)
                                save_session(st.session_state.session_id, job_role, difficulty, interview_mode, avg)
                            
                            time.sleep(2)
                            st.rerun()
            
            with col2:
                st.metric("Words", len(answer.split()) if answer else 0)
            
            st.progress(min((st.session_state.question_num - 1) / len(questions), 1.0))
    
    elif st.session_state.interview_stage == 'complete':
        st.success("🎉 Interview Complete!")
        st.info("📊 Check Results for detailed feedback")


elif page == "🎙️ Voice Interview":
    st.title("🎙️ Voice-Based Interview Mode")
    st.info("💡 This feature uses the FastAPI voice server. Make sure it's running on port 8000!")

    voice_url = f"{FRONTEND_URL}/voice"
    st.components.v1.html(f"""
    <iframe 
        src="{voice_url}" 
        width="100%" 
        height="900" 
        frameborder="0"
        allow="microphone"
        style="border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.2);"
    ></iframe>
    """, height=900)

elif page == "📊 Results":
    st.title("📊 Performance Report")
    
    if not st.session_state.answers:
        st.warning("⚠️ No interview completed")
    else:
        tech = [a for a in st.session_state.answers if not a.get('is_intro')]
        avg = sum([a['score'] for a in tech]) / len(tech) if tech else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='score-card'><h2>{avg:.0f}%</h2><p>Score</p></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='score-card'><h2>{len(tech)}</h2><p>Questions</p></div>", unsafe_allow_html=True)
        with col3:
            avg_time = sum([a.get('time_taken', 0) for a in tech]) / len(tech) if tech else 0
            st.markdown(f"<div class='score-card'><h2>{avg_time:.0f}s</h2><p>Avg Time</p></div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        for i, ans in enumerate(tech, 1):
            with st.expander(f"Q{i}: {ans['q'][:50]}... | {ans['score']}/100"):
                st.markdown(f"**Q:** {ans['q']}")
                st.markdown(f"**A:** {ans['a']}")
                if ans.get('ideal_answer'):
                    st.markdown("**Ideal:**")
                    for p in ans['ideal_answer']:
                        st.markdown(f"• {p}")
        
        if st.button("📈 Generate 7-Day Plan"):
            with st.spinner("Creating plan..."):
                cat_scores = {}
                for ans in tech:
                    if ans['category'] not in cat_scores:
                        cat_scores[ans['category']] = []
                    cat_scores[ans['category']].append(ans['score'])
                
                plan = generate_improvement_plan(cat_scores, job_role)
                for day in plan:
                    st.markdown(f"**Day {day['day']}: {day.get('focus')}**")
                    for task in day.get('tasks', []):
                        st.markdown(f"• {task}")

elif page == "📈 Progress":
    st.title("📈 Performance Dashboard")
    
    sessions = load_session_history()
    
    if not sessions:
        st.info("💡 Complete interviews to track your progress!")
    else:
        # Prepare data
        df = pd.DataFrame(sessions, columns=['ID', 'Role', 'Difficulty', 'Score', 'Date'])
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # ═══ KPI CARDS ═══
        st.subheader("📊 Key Performance Indicators")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Sessions", len(sessions))
        
        with col2:
            last_score = df['Score'].iloc[-1]
            st.metric("Latest Score", f"{last_score:.0f}%")
        
        with col3:
            avg_score = df['Score'].mean()
            st.metric("Average Score", f"{avg_score:.0f}%")
        
        with col4:
            best_score = df['Score'].max()
            st.metric("Best Score", f"{best_score:.0f}%")
        
        with col5:
            if len(df) > 1:
                improvement = df['Score'].iloc[-1] - df['Score'].iloc[0]
                st.metric("Improvement", f"{improvement:+.0f}%", delta=f"{improvement:+.0f}%")
            else:
                st.metric("Improvement", "N/A")
        
        st.markdown("---")
        
        # ═══ SCORE TREND ═══
        st.subheader("📈 Score Trend Over Time")
        chart_df = df[['Date', 'Score']].copy()
        chart_df = chart_df.set_index('Date')
        st.line_chart(chart_df, width=True, height=300)
        
        st.markdown("---")
        
        # ═══ CATEGORY PERFORMANCE ═══
        st.subheader("📊 Performance by Category")
        
        conn = sqlite3.connect('interview_memory.db')
        c = conn.cursor()
        c.execute('''SELECT rubric_scores FROM performance''')
        all_rubrics = c.fetchall()
        conn.close()
        
        if all_rubrics:
            category_totals = {"Correctness": 0, "Depth": 0, "Clarity": 0, "Structure": 0, "Real-world": 0}
            count = 0
            
            for rubric_json, in all_rubrics:
                try:
                    rubric = json.loads(rubric_json)
                    category_totals["Correctness"] += rubric.get("correctness", 0)
                    category_totals["Depth"] += rubric.get("depth", 0)
                    category_totals["Clarity"] += rubric.get("clarity", 0)
                    category_totals["Structure"] += rubric.get("structure", 0)
                    category_totals["Real-world"] += rubric.get("real_world", 0)
                    count += 1
                except:
                    pass
            
            if count > 0:
                category_avgs = {k: v / count for k, v in category_totals.items()}
                category_df = pd.DataFrame(list(category_avgs.items()), columns=['Category', 'Score'])
                st.bar_chart(category_df.set_index('Category'), width=True, height=300)
        
        st.markdown("---")
        
        # ═══ SESSION HISTORY TABLE ═══
        st.subheader("📋 Session History")
        
        display_df = df[['Date', 'Role', 'Difficulty', 'Score']].copy()
        display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d %H:%M')
        display_df['Score'] = display_df['Score'].apply(lambda x: f"{x:.0f}%")
        
        st.dataframe(display_df, width=True, hide_index=True)


st.markdown("<div style='text-align:center;color:#888'><p>AI Interview Prep | SQLite Memory | Premium Features</p></div>", unsafe_allow_html=True)