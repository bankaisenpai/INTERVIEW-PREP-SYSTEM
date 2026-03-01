import streamlit as st
import pandas as pd
from datetime import datetime
import json
import requests
import PyPDF2
import io
import os
import random
import time
from dotenv import load_dotenv

st.set_page_config(page_title="AI Interview Prep", page_icon="🎤", layout="wide")

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ═══════════════════════════════════════════════════════════
# GROQ AI - CONVERSATION MEMORY & ADAPTIVE
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
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except Exception as e:
        return None

def generate_personalized_questions(job_role, difficulty, resume_skills, conversation_history, num_questions=5):
    """Generate questions WITH conversation memory and resume context"""
    
    random_seed = random.randint(1, 1000)
    
    # Build conversation context
    conv_context = ""
    if conversation_history:
        conv_context = "Previous conversation:\n"
        for item in conversation_history[-3:]:  # Last 3 exchanges
            conv_context += f"Q: {item['q']}\nA: {item['a'][:200]}...\n"
    
    # Build resume context
    resume_context = ""
    if resume_skills:
        all_skills = []
        for cat, skills in resume_skills.items():
            all_skills.extend(skills)
        resume_context = f"Candidate has these skills: {', '.join(all_skills[:10])}\n"
    
    job_contexts = {
        "Data Scientist": "ML algorithms, statistics, Python/R, data preprocessing, model evaluation, deployment",
        "Frontend Developer": "React/Vue/Angular, JavaScript/TypeScript, CSS, performance, accessibility, state management",
        "Backend Developer": "APIs, databases, architecture, authentication, caching, microservices, Node/Python/Java",
        "DevOps Engineer": "CI/CD, Docker, Kubernetes, AWS/Azure, monitoring, automation, infrastructure as code",
        "ML Engineer": "Model deployment, MLOps, production ML, scalability, model serving, Docker/Kubernetes",
        "Full Stack Developer": "Frontend (React/Vue) + Backend (Node/Python), databases, REST APIs, deployment",
    }
    
    context = job_contexts.get(job_role, "technical skills and problem-solving")
    
    prompt = f"""You are an expert technical interviewer for a {job_role} position.

{resume_context}

{conv_context}

Generate {num_questions} UNIQUE interview questions:

REQUIREMENTS:
1. Questions MUST be specific to {job_role}: {context}
2. Reference previous conversation if available (e.g., "You mentioned X, now tell me about Y")
3. Target skills from resume AND identify gaps
4. Mix question types:
   - Conceptual (explain X)
   - Practical (how would you solve Y)
   - Debugging (find the bug in this code)
   - Tradeoff (why X over Y)
5. Difficulty: {difficulty}

Seed: {random_seed}

Return ONLY JSON array:
[
  {{"question": "...", "category": "...", "keywords": ["...", "...", "...", "...", "..."], "type": "conceptual|practical|debugging|tradeoff"}}
]

Generate now:"""

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
    """AI evaluation with detailed scoring rubric"""
    
    if not GROQ_API_KEY or not answer or len(answer.strip()) < 10:
        return keyword_rubric_evaluate(answer, keywords)
    
    prompt = f"""You are evaluating a technical interview answer using a detailed rubric.

Question: {question}
Type: {question_type}
Expected keywords: {', '.join(keywords)}
Candidate's Answer: {answer}

Evaluate using this rubric (total 100 points):

SCORING RUBRIC:
1. Correctness (0-40): Technical accuracy and understanding
2. Depth (0-25): Detail level, examples, edge cases
3. Clarity (0-15): Well-organized, easy to follow
4. Structure (0-10): Logical flow, introduction-body-conclusion
5. Real-world Application (0-10): Practical examples, production experience

ADDITIONAL FEEDBACK:
- Identify specific strengths (2-3 points)
- Identify areas to improve (2-3 points)
- Provide an IDEAL ANSWER outline (bullet points)
- Rewrite their answer in professional interview style
- Overall constructive feedback

Return JSON:
{{
  "total_score": <0-100>,
  "rubric": {{
    "correctness": <0-40>,
    "depth": <0-25>,
    "clarity": <0-15>,
    "structure": <0-10>,
    "real_world": <0-10>
  }},
  "strengths": ["...", "..."],
  "improvements": ["...", "..."],
  "ideal_answer_outline": ["point 1", "point 2", "point 3"],
  "rewritten_answer": "Professional version of their answer...",
  "feedback": "Overall feedback sentence",
  "needs_followup": true|false,
  "followup_question": "Optional follow-up if answer is shallow"
}}

Be specific and constructive."""

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
            "ideal_answer_outline": ["Address key concepts", "Provide examples", "Discuss tradeoffs"],
            "rewritten_answer": "",
            "feedback": "No answer provided",
            "needs_followup": False
        }
    
    matched = sum(1 for kw in keywords if kw.lower() in answer.lower())
    base_score = int((matched / len(keywords)) * 100)
    
    # Distribute across rubric
    correctness = int(base_score * 0.4)
    depth = int(base_score * 0.25)
    clarity = int(base_score * 0.15)
    structure = int(base_score * 0.1)
    real_world = int(base_score * 0.1)
    
    missing = [k for k in keywords if k.lower() not in answer.lower()]
    
    return {
        "total_score": base_score,
        "rubric": {
            "correctness": correctness,
            "depth": depth,
            "clarity": clarity,
            "structure": structure,
            "real_world": real_world
        },
        "strengths": [f"Mentioned {len(keywords) - len(missing)}/{len(keywords)} key concepts"] if matched > 0 else [],
        "improvements": [f"Consider discussing: {', '.join(missing[:3])}"] if missing else ["Comprehensive!"],
        "ideal_answer_outline": [f"Explain {kw}" for kw in keywords[:3]],
        "rewritten_answer": f"A strong answer would cover: {', '.join(keywords)}",
        "feedback": "👍 Good" if base_score >= 60 else "⚠️ Needs more detail",
        "needs_followup": base_score < 50
    }

def get_default_questions(job_role):
    """Fallback questions"""
    defaults = {
        "Data Scientist": [
            {"question": "Explain bias-variance tradeoff", "category": "ML Theory", "keywords": ["bias", "variance", "overfitting", "underfitting", "generalization"], "type": "conceptual"},
            {"question": "How do you handle imbalanced datasets?", "category": "Data", "keywords": ["imbalanced", "SMOTE", "oversampling", "class weights"], "type": "practical"},
        ],
        "Frontend Developer": [
            {"question": "Explain React hooks lifecycle", "category": "React", "keywords": ["hooks", "useState", "useEffect", "lifecycle", "state"], "type": "conceptual"},
            {"question": "How do you optimize React performance?", "category": "Performance", "keywords": ["memoization", "lazy loading", "code splitting", "optimization"], "type": "practical"},
        ],
    }
    return defaults.get(job_role, defaults["Data Scientist"])

def generate_improvement_plan(scores, job_role):
    """Generate 7-day improvement plan based on performance"""
    
    if not GROQ_API_KEY:
        return ["Day 1-7: Practice technical concepts and review fundamentals"]
    
    prompt = f"""Based on this interview performance for {job_role}, create a 7-day improvement plan.

Scores by category:
{json.dumps(scores, indent=2)}

Generate a practical 7-day plan:
Day 1: Focus area + specific resources/practice
Day 2: ...
...
Day 7: ...

Return as JSON array:
[
  {{"day": 1, "focus": "topic", "tasks": ["task1", "task2"], "resources": ["resource1"]}},
  ...
]"""

    response = call_groq_api(prompt, temperature=0.7, max_tokens=1000)
    
    if response:
        try:
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
    
    return [{"day": i+1, "focus": f"Practice Day {i+1}", "tasks": ["Review concepts", "Practice problems"], "resources": ["Online resources"]} for i in range(7)]

# ═══════════════════════════════════════════════════════════
# REALISTIC INTRO WITH MEMORY
# ═══════════════════════════════════════════════════════════
def get_intro_questions(job_role):
    return [
        {
            "question": f"Good morning! Welcome to our {job_role} interview. Could you please introduce yourself and tell me about your background?",
            "category": "Introduction",
            "keywords": ["name", "background", "experience"],
            "is_intro": True
        },
        {
            "question": f"Thank you! What specifically interests you about the {job_role} position, and what relevant experience do you bring?",
            "category": "Motivation",
            "keywords": ["interest", "motivation", "experience", "skills"],
            "is_intro": True
        },
        {
            "question": "That's great! Before we dive into technical questions, could you walk me through a recent project or achievement you're proud of?",
            "category": "Project",
            "keywords": ["project", "achievement", "technical", "implementation"],
            "is_intro": True
        }
    ]

# ═══════════════════════════════════════════════════════════
# ROLES & MODES
# ═══════════════════════════════════════════════════════════
IT_JOB_ROLES = [
    "Data Scientist", "ML Engineer", "AI/ML Researcher",
    "Data Engineer", "Data Analyst", "Frontend Developer",
    "Backend Developer", "Full Stack Developer", "DevOps Engineer",
    "Cloud Engineer (AWS/Azure/GCP)", "Software Engineer",
    "QA Engineer", "Cybersecurity Analyst", "Database Administrator",
    "Mobile Developer (iOS/Android)", "UI/UX Designer",
    "Product Manager (Tech)", "Solutions Architect", "SRE",
    "Blockchain Developer", "NLP Engineer", "Computer Vision Engineer"
]

INTERVIEW_MODES = {
    "Practice Mode": "Hints allowed, ideal answers shown, no time limit",
    "Strict Interview": "No hints, timed, feedback at end only",
    "Company Style": "Customize to specific company patterns"
}

# ═══════════════════════════════════════════════════════════
# RESUME PARSING
# ═══════════════════════════════════════════════════════════
def parse_resume(uploaded_file):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        skills = extract_skills(text)
        experience = extract_experience(text)
        return text, skills, experience
    except Exception as e:
        return "", {}, 0

def extract_skills(text):
    skill_keywords = {
        'Programming': ['python', 'javascript', 'java', 'c++', 'sql', 'r', 'typescript', 'go'],
        'ML/AI': ['machine learning', 'tensorflow', 'pytorch', 'keras', 'nlp', 'computer vision'],
        'Web': ['react', 'angular', 'vue', 'node.js', 'django', 'flask', 'nextjs'],
        'Cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform'],
        'Data': ['pandas', 'numpy', 'sql', 'mongodb', 'spark', 'hadoop'],
        'Tools': ['git', 'jenkins', 'ci/cd', 'linux', 'agile']
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
    patterns = [r'(\d+)\+?\s*years?\s+(?:of\s+)?experience']
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    return 0

def calculate_resume_score(skills, experience, job_role):
    score = min((sum(len(s) for s in skills.values()) / 8) * 50, 50)
    score += 30 if experience >= 2 else (experience / 2) * 30
    score += len(skills) * 4
    return int(min(score, 100))

# ═══════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════
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
if 'session_history' not in st.session_state:
    st.session_state.session_history = []

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
.rubric-box { background: white; border: 2px solid #e0e0e0; border-radius: 10px;
    padding: 16px; margin: 10px 0; }
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
page = st.sidebar.radio("Go to", ["🏠 Home", "📄 Resume", "🎤 Interview", "📊 Results", "📈 Progress"])

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Settings")

job_role = st.sidebar.selectbox("Position:", IT_JOB_ROLES)
difficulty = st.sidebar.select_slider("Level:", ["Beginner", "Intermediate", "Advanced"])
interview_mode = st.sidebar.selectbox("Mode:", list(INTERVIEW_MODES.keys()))
st.sidebar.info(INTERVIEW_MODES[interview_mode])

st.sidebar.markdown("---")

if GROQ_API_KEY:
    st.sidebar.success("🤖 AI: Active")
    st.sidebar.caption("✅ Conversation Memory\n✅ Adaptive Questions\n✅ Detailed Rubric")
else:
    st.sidebar.warning("⚠️ AI: Limited")

# ═══════════════════════════════════════════════════════════
# HOME
# ═══════════════════════════════════════════════════════════
if page == "🏠 Home":
    st.markdown("<h1 class='main-header'>🎤 AI-Powered Interview Preparation System</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='feature-box'><h3>💬 Conversation Memory</h3><p>AI references your previous answers</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='feature-box'><h3>🎯 Adaptive Follow-ups</h3><p>Dynamic questions based on depth</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='feature-box'><h3>📊 Detailed Rubric</h3><p>5-category scoring breakdown</p></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.session_state.session_history:
        avg_scores = [s['avg'] for s in st.session_state.session_history]
        improvement = avg_scores[-1] - avg_scores[0] if len(avg_scores) > 1 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Sessions", len(st.session_state.session_history))
        col2.metric("Latest Score", f"{avg_scores[-1]:.0f}%")
        col3.metric("Improvement", f"{improvement:+.0f}%", delta_color="normal")

# ═══════════════════════════════════════════════════════════
# RESUME PAGE
# ═══════════════════════════════════════════════════════════
elif page == "📄 Resume":
    st.title("📄 Resume Analysis")
    
    uploaded = st.file_uploader("Upload PDF", type=['pdf'])
    
    if uploaded and st.button("🔍 Analyze"):
        with st.spinner("Analyzing..."):
            text, skills, exp = parse_resume(uploaded)
            st.session_state.resume_skills = skills
            st.session_state.resume_experience = exp
            st.session_state.resume_score = calculate_resume_score(skills, exp, job_role)
            st.balloons()
            st.rerun()
    
    if st.session_state.resume_skills:
        st.markdown("---")
        score = st.session_state.resume_score
        st.markdown(f"<div class='score-card'><h2>{score}%</h2><p>Match for {job_role}</p></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# INTERVIEW PAGE - WITH ALL PREMIUM FEATURES
# ═══════════════════════════════════════════════════════════
elif page == "🎤 Interview":
    st.title("🎤 Professional Interview Simulation")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### 🎯 {job_role} | {interview_mode}")
    with col2:
        elapsed = (datetime.now() - st.session_state.start_time).seconds
        mins, secs = divmod(elapsed, 60)
        st.markdown(f"### ⏱️ {mins:02d}:{secs:02d}")
    with col3:
        if st.session_state.question_start_time:
            q_elapsed = (datetime.now() - st.session_state.question_start_time).seconds
            st.markdown(f"### 🕐 {q_elapsed}s")
    
    st.markdown("---")
    
    # 3D AVATAR
    st.subheader("🤖 AI Interviewer")
    st.components.v1.iframe("https://interview-prep-system.vercel.app/", height=600, scrolling=False)
    
    st.markdown("---")
    
    # NOT STARTED
    if st.session_state.interview_stage == 'not_started':
        st.markdown(f"""<div class='feature-box'>
        <h3>Interview Structure:</h3>
        <p><strong>Round 1:</strong> Introduction (3 questions)</p>
        <p><strong>Round 2:</strong> Technical Assessment (5 adaptive questions)</p>
        <p><strong>Features:</strong> Conversation memory, follow-up questions, detailed scoring rubric</p>
        </div>""", unsafe_allow_html=True)
        
        if st.button("🚀 START INTERVIEW", use_container_width=True, type="primary"):
            st.session_state.interview_stage = 'intro'
            st.session_state.question_num = 1
            st.session_state.start_time = datetime.now()
            st.session_state.question_start_time = datetime.now()
            st.session_state.intro_questions = get_intro_questions(job_role)
            st.rerun()
    
    # INTRO STAGE
    elif st.session_state.interview_stage == 'intro':
        intro_qs = st.session_state.intro_questions
        
        if st.session_state.question_num <= len(intro_qs):
            q = intro_qs[st.session_state.question_num - 1]
            
            st.subheader(f"Introduction - Question {st.session_state.question_num} of {len(intro_qs)}")
            st.markdown(f"""<div class='feature-box'><h3>{q['question']}</h3></div>""", unsafe_allow_html=True)
            
            # Timer warning
            if st.session_state.question_start_time:
                elapsed = (datetime.now() - st.session_state.question_start_time).seconds
                if interview_mode == "Strict Interview" and elapsed > 90:
                    st.markdown("<div class='timer-warning'>⚠️ Recommended time: 60-90 seconds</div>", unsafe_allow_html=True)
            
            answer = st.text_area("Your Answer:", height=120, key=f"intro_{st.session_state.question_num}")
            
            if st.button("📤 Submit", use_container_width=True, type="primary"):
                if answer and len(answer.strip()) > 10:
                    answer_time = (datetime.now() - st.session_state.question_start_time).seconds if st.session_state.question_start_time else 0
                    
                    st.session_state.conversation_history.append({"q": q['question'], "a": answer})
                    st.session_state.answers.append({
                        "q": q['question'],
                        "a": answer,
                        "category": q['category'],
                        "is_intro": True,
                        "time_taken": answer_time
                    })
                    
                    st.session_state.question_num += 1
                    st.session_state.question_start_time = datetime.now()
                    
                    if st.session_state.question_num > len(intro_qs):
                        st.session_state.interview_stage = 'technical'
                        st.session_state.question_num = 1
                        
                        with st.spinner(f"Generating personalized {job_role} questions..."):
                            st.session_state.technical_questions = generate_personalized_questions(
                                job_role, difficulty, st.session_state.resume_skills, 
                                st.session_state.conversation_history, 5
                            )
                        st.success("✅ Questions generated with conversation context!")
                    
                    st.rerun()
                else:
                    st.error("⚠️ Please provide an answer")
    
    # TECHNICAL STAGE
    elif st.session_state.interview_stage == 'technical':
        questions = st.session_state.technical_questions
        
        if st.session_state.question_num <= len(questions):
            q = questions[st.session_state.question_num - 1]
            
            st.subheader(f"Technical - Question {st.session_state.question_num} of {len(questions)}")
            st.markdown(f"""<div class='feature-box'><h3>{q['question']}</h3>
            <p><strong>Type:</strong> {q.get('type', 'conceptual').title()} | <strong>Category:</strong> {q['category']}</p>
            </div>""", unsafe_allow_html=True)
            
            # Timer
            if st.session_state.question_start_time:
                elapsed = (datetime.now() - st.session_state.question_start_time).seconds
                if interview_mode == "Strict Interview" and elapsed > 240:
                    st.markdown("<div class='timer-warning'>⚠️ Recommended time: 2-4 minutes for technical questions</div>", unsafe_allow_html=True)
            
            answer = st.text_area("Your Answer:", height=150, key=f"tech_{st.session_state.question_num}",
                                placeholder="Provide detailed answer with examples...")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("📤 Submit Answer", use_container_width=True, type="primary"):
                    if answer and len(answer.strip()) > 15:
                        answer_time = (datetime.now() - st.session_state.question_start_time).seconds if st.session_state.question_start_time else 0
                        
                        with st.spinner("AI Evaluating with detailed rubric..."):
                            result = evaluate_with_rubric(q['question'], answer, q['keywords'], q.get('type', 'conceptual'))
                            
                            st.session_state.conversation_history.append({"q": q['question'], "a": answer})
                            st.session_state.answers.append({
                                "q": q['question'],
                                "a": answer,
                                "category": q['category'],
                                "score": result['total_score'],
                                "rubric": result['rubric'],
                                "strengths": result['strengths'],
                                "improvements": result['improvements'],
                                "ideal_answer": result.get('ideal_answer_outline', []),
                                "rewritten": result.get('rewritten_answer', ''),
                                "feedback": result['feedback'],
                                "time_taken": answer_time,
                                "followup": result.get('followup_question', '')
                            })
                            st.session_state.scores.append(result['total_score'])
                            st.session_state.rubric_scores.append(result['rubric'])
                            
                            # Show detailed feedback
                            st.success(f"✅ Total Score: {result['total_score']}/100")
                            
                            # Rubric breakdown
                            st.markdown("**📊 Scoring Rubric:**")
                            cols = st.columns(5)
                            rubric = result['rubric']
                            cols[0].metric("Correctness", f"{rubric['correctness']}/40")
                            cols[1].metric("Depth", f"{rubric['depth']}/25")
                            cols[2].metric("Clarity", f"{rubric['clarity']}/15")
                            cols[3].metric("Structure", f"{rubric['structure']}/10")
                            cols[4].metric("Real-world", f"{rubric['real_world']}/10")
                            
                            # Ideal answer
                            if result.get('ideal_answer_outline'):
                                st.markdown("**✨ Ideal Answer Outline:**")
                                st.markdown("<div class='ideal-answer'>" + "<br>".join([f"• {point}" for point in result['ideal_answer_outline']]) + "</div>", unsafe_allow_html=True)
                            
                            # Rewritten answer
                            if result.get('rewritten_answer'):
                                st.markdown("**✍️ Professional Interview Version:**")
                                st.markdown(f"<div class='rewritten-answer'>{result['rewritten_answer']}</div>", unsafe_allow_html=True)
                            
                            # Time feedback
                            if answer_time < 60:
                                st.info("💡 Consider taking more time to elaborate")
                            elif answer_time > 300:
                                st.info("💡 Try to be more concise (aim for 2-4 minutes)")
                            
                            # Follow-up
                            if result.get('needs_followup') and result.get('followup_question'):
                                st.warning(f"🔄 Follow-up: {result['followup_question']}")
                            
                            st.session_state.question_num += 1
                            st.session_state.question_start_time = datetime.now()
                            
                            if st.session_state.question_num > len(questions):
                                st.session_state.interview_stage = 'complete'
                            
                            st.balloons()
                            time.sleep(3)
                            st.rerun()
                    else:
                        st.error("⚠️ Please provide detailed answer")
            
            with col2:
                words = len(answer.split()) if answer else 0
                st.metric("Words", words)
            
            progress = (st.session_state.question_num - 1) / len(questions)
            st.progress(min(progress, 1.0))
    
    # COMPLETE
    elif st.session_state.interview_stage == 'complete':
        st.success("🎉 Interview Complete!")
        st.info("📊 Check Results page for detailed feedback and improvement plan")

# ═══════════════════════════════════════════════════════════
# RESULTS PAGE - PREMIUM
# ═══════════════════════════════════════════════════════════
elif page == "📊 Results":
    st.title("📊 Comprehensive Performance Report")
    
    if not st.session_state.answers:
        st.warning("⚠️ No interview completed")
    else:
        tech_answers = [a for a in st.session_state.answers if not a.get('is_intro')]
        tech_scores = [a['score'] for a in tech_answers]
        avg = sum(tech_scores) / len(tech_scores) if tech_scores else 0
        
        # Save to history
        if avg > 0 and not any(s.get('timestamp') == datetime.now().strftime('%Y-%m-%d %H:%M') for s in st.session_state.session_history):
            st.session_state.session_history.append({
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M'),
                "role": job_role,
                "avg": avg,
                "scores": tech_scores
            })
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='score-card'><h2>{avg:.0f}%</h2><p>Overall Score</p></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='score-card'><h2>{len(tech_scores)}</h2><p>Questions</p></div>", unsafe_allow_html=True)
        with col3:
            avg_time = sum([a.get('time_taken', 0) for a in tech_answers]) / len(tech_answers) if tech_answers else 0
            st.markdown(f"<div class='score-card'><h2>{avg_time:.0f}s</h2><p>Avg Time</p></div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Radar chart for rubric
        if st.session_state.rubric_scores:
            st.subheader("📊 Performance Radar")
            avg_rubric = {
                "Correctness": sum([r['correctness'] for r in st.session_state.rubric_scores]) / len(st.session_state.rubric_scores),
                "Depth": sum([r['depth'] for r in st.session_state.rubric_scores]) / len(st.session_state.rubric_scores),
                "Clarity": sum([r['clarity'] for r in st.session_state.rubric_scores]) / len(st.session_state.rubric_scores),
                "Structure": sum([r['structure'] for r in st.session_state.rubric_scores]) / len(st.session_state.rubric_scores),
                "Real-world": sum([r['real_world'] for r in st.session_state.rubric_scores]) / len(st.session_state.rubric_scores)
            }
            
            df = pd.DataFrame(list(avg_rubric.items()), columns=['Category', 'Score'])
            st.bar_chart(df.set_index('Category'))
        
        st.markdown("---")
        
        # Detailed Q&A
        st.subheader("📝 Question-by-Question Analysis")
        for i, ans in enumerate(tech_answers, 1):
            with st.expander(f"Q{i}: {ans['q'][:50]}... | {ans['score']}/100"):
                st.markdown(f"**Question:** {ans['q']}")
                st.markdown(f"**Your Answer:** {ans['a']}")
                st.markdown(f"**Score:** {ans['score']}/100 | **Time:** {ans.get('time_taken', 0)}s")
                
                if ans.get('ideal_answer'):
                    st.markdown("**✨ Ideal Answer:**")
                    for point in ans['ideal_answer']:
                        st.markdown(f"• {point}")
                
                if ans.get('rewritten'):
                    st.markdown(f"**✍️ Professional Version:** {ans['rewritten']}")
        
        st.markdown("---")
        
        # 7-Day Improvement Plan
        st.subheader("📈 Personalized 7-Day Improvement Plan")
        
        if st.button("Generate Improvement Plan", use_container_width=True):
            with st.spinner("Creating personalized plan..."):
                category_scores = {}
                for ans in tech_answers:
                    cat = ans['category']
                    if cat not in category_scores:
                        category_scores[cat] = []
                    category_scores[cat].append(ans['score'])
                
                plan = generate_improvement_plan(category_scores, job_role)
                
                for day in plan:
                    with st.expander(f"Day {day['day']}: {day.get('focus', 'Practice')}"):
                        st.markdown(f"**Focus:** {day.get('focus', '')}")
                        if day.get('tasks'):
                            st.markdown("**Tasks:**")
                            for task in day['tasks']:
                                st.markdown(f"• {task}")
                        if day.get('resources'):
                            st.markdown("**Resources:**")
                            for res in day['resources']:
                                st.markdown(f"• {res}")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            report = {
                "timestamp": datetime.now().isoformat(),
                "role": job_role,
                "mode": interview_mode,
                "overall_score": round(avg, 2),
                "rubric_breakdown": avg_rubric if st.session_state.rubric_scores else {},
                "answers": tech_answers
            }
            st.download_button("📥 Download Full Report", json.dumps(report, indent=2), 
                             f"interview_{job_role.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json", 
                             use_container_width=True)
        
        with col2:
            if st.button("🔄 Start New Interview", use_container_width=True):
                keys_to_reset = ['interview_stage', 'question_num', 'answers', 'scores', 'rubric_scores',
                                'technical_questions', 'intro_questions', 'conversation_history', 
                                'question_start_time']
                for key in keys_to_reset:
                    if key in st.session_state:
                        if key in ['answers', 'scores', 'rubric_scores', 'technical_questions', 
                                   'intro_questions', 'conversation_history']:
                            st.session_state[key] = []
                        elif key == 'interview_stage':
                            st.session_state[key] = 'not_started'
                        else:
                            st.session_state[key] = 0 if 'num' in key else None
                st.rerun()

# ═══════════════════════════════════════════════════════════
# PROGRESS TRACKING
# ═══════════════════════════════════════════════════════════
elif page == "📈 Progress":
    st.title("📈 Progress Tracking")
    
    if st.session_state.session_history:
        df = pd.DataFrame(st.session_state.session_history)
        
        st.subheader("Score Improvement Over Time")
        st.line_chart(df.set_index('timestamp')['avg'])
        
        st.subheader("Session History")
        st.dataframe(df)
        
        if len(df) > 1:
            improvement = df['avg'].iloc[-1] - df['avg'].iloc[0]
            st.metric("Total Improvement", f"{improvement:+.1f}%")
    else:
        st.info("Complete interviews to track your progress!")

st.markdown("---")
st.markdown("<div style='text-align:center;color:#888'><p>AI-Powered Interview Preparation System | Premium Features</p></div>", unsafe_allow_html=True)