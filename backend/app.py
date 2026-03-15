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
import sqlite3
import hashlib
from dotenv import load_dotenv

# Import UI components and authentication from design.py
from design import (
    apply_custom_css,
    render_home_page,
    render_resume_page,
    render_interview_page,
    render_results_page,
    render_progress_page,
    render_login_page,
    render_register_page,
    is_logged_in,
    get_current_user,
    logout_user,
    init_users_database
)

# ═══════════════════════════════════════════════════════════
# CONFIG AND INITIALIZATION
# ═══════════════════════════════════════════════════════════

st.set_page_config(page_title="AI-Powered Interview Preparation System", page_icon="🎤", layout="wide")

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Export for design.py
__all__ = ['GROQ_API_KEY', 'FRONTEND_URL', 'SUPPORTED_JOB_ROLES', 'INTERVIEW_MODE_CONFIG']

# ═══════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════

SUPPORTED_JOB_ROLES = [
    "Backend Developer",
    "Frontend Developer",
    "Data Scientist",
    "ML Engineer",
    "Full Stack Developer",
    "DevOps Engineer"
]

INTERVIEW_MODE_CONFIG = {
    "Practice Mode": {
        "intro_count": 2,
        "tech_count": 3,
        "description": "Lighter interview flow with immediate feedback",
        "tone": "friendly",
        "immediate_feedback": True
    },
    "Strict Interview": {
        "intro_count": 3,
        "tech_count": 5,
        "description": "Professional simulation with end-of-interview feedback",
        "tone": "formal",
        "immediate_feedback": False
    }
}

ROLE_REQUIRED_SKILLS = {
    "Backend Developer": {
        "must_have": ["python", "sql", "api", "database"],
        "preferred": ["node.js", "django", "flask", "postgresql", "mongodb"],
        "bonus": ["microservices", "docker", "kubernetes", "redis"],
        "min_experience": 2
    },
    "Frontend Developer": {
        "must_have": ["javascript", "html", "css", "react"],
        "preferred": ["typescript", "vue", "angular", "webpack", "git"],
        "bonus": ["nextjs", "redux", "testing", "accessibility"],
        "min_experience": 1
    },
    "Data Scientist": {
        "must_have": ["python", "statistics", "machine learning", "sql"],
        "preferred": ["pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "r"],
        "bonus": ["spark", "hadoop", "aws", "azure", "docker"],
        "min_experience": 2
    },
    "ML Engineer": {
        "must_have": ["python", "machine learning", "docker"],
        "preferred": ["tensorflow", "pytorch", "mlops", "kubernetes"],
        "bonus": ["aws", "azure", "monitoring", "ci/cd"],
        "min_experience": 2
    },
    "Full Stack Developer": {
        "must_have": ["javascript", "python", "sql", "react"],
        "preferred": ["node.js", "typescript", "mongodb", "postgresql"],
        "bonus": ["aws", "docker", "testing"],
        "min_experience": 2
    },
    "DevOps Engineer": {
        "must_have": ["linux", "docker", "ci/cd"],
        "preferred": ["kubernetes", "aws", "azure", "terraform", "ansible"],
        "bonus": ["monitoring", "prometheus", "grafana"],
        "min_experience": 2
    }
}

SKILL_ALIASES = {
    "machine learning": ["ml", "machine-learning"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "node.js": ["node", "nodejs"],
    "ci/cd": ["cicd", "ci cd", "continuous integration", "continuous delivery"],
    "kubernetes": ["k8s"],
    "postgresql": ["postgres", "postgre"],
    "react native": ["react-native"],
    "tensorflow": ["tf"],
    "pytorch": ["torch"],
}

# Question bank and validation (used by design.py)
from design import ROLE_QUESTION_BANK, ROLE_VALIDATION_KEYWORDS

# ═══════════════════════════════════════════════════════════
# DATABASE OPERATIONS
# ═══════════════════════════════════════════════════════════

def init_database():
    """Initialize SQLite database with proper schema"""
    with sqlite3.connect('interview_memory.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS conversations
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, timestamp DATETIME,
                      question TEXT, answer TEXT, category TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS sessions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT UNIQUE, job_role TEXT,
                      difficulty TEXT, mode TEXT, overall_score REAL, completed_at DATETIME)''')
        c.execute('''CREATE TABLE IF NOT EXISTS performance
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, question TEXT, answer TEXT,
                      score INTEGER, rubric_scores TEXT, feedback TEXT, time_taken INTEGER)''')
        conn.commit()

init_database()
init_users_database()

def save_conversation(session_id, question, answer, category):
    try:
        with sqlite3.connect('interview_memory.db') as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO conversations (session_id, timestamp, question, answer, category)
                         VALUES (?, ?, ?, ?, ?)''', (session_id, datetime.now(), question, answer, category))
            conn.commit()
    except Exception as e:
        st.warning(f"Failed to save conversation: {str(e)}")

def save_session(session_id, job_role, difficulty, mode, overall_score):
    try:
        with sqlite3.connect('interview_memory.db') as conn:
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO sessions 
                         (session_id, job_role, difficulty, mode, overall_score, completed_at)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (session_id, job_role, difficulty, mode, overall_score, datetime.now()))
            conn.commit()
    except Exception as e:
        st.warning(f"Failed to save session: {str(e)}")

def save_performance(session_id, question, answer, score, rubric_scores, feedback, time_taken):
    try:
        with sqlite3.connect('interview_memory.db') as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO performance 
                         (session_id, question, answer, score, rubric_scores, feedback, time_taken)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (session_id, question, answer, score, json.dumps(rubric_scores), feedback, time_taken))
            conn.commit()
    except Exception as e:
        st.warning(f"Failed to save performance: {str(e)}")

def load_session_history():
    try:
        with sqlite3.connect('interview_memory.db') as conn:
            c = conn.cursor()
            c.execute('''SELECT session_id, job_role, difficulty, overall_score, completed_at 
                         FROM sessions ORDER BY completed_at DESC''')
            return c.fetchall()
    except Exception as e:
        st.warning(f"Failed to load session history: {str(e)}")
        return []

def get_conversation_context(session_id, limit=5):
    try:
        with sqlite3.connect('interview_memory.db') as conn:
            c = conn.cursor()
            c.execute('''SELECT question, answer FROM conversations 
                         WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?''', (session_id, limit))
            history = c.fetchall()
            return [{"q": h[0], "a": h[1]} for h in reversed(history)]
    except Exception:
        return []

# ═══════════════════════════════════════════════════════════
# AI & EVALUATION
# ═══════════════════════════════════════════════════════════

def call_groq_api(prompt, temperature=0.7, max_tokens=1500):
    """Call Groq API with error handling"""
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
        response = requests.post("https://api.groq.com/openai/v1/chat/completions",
                                headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except Exception:
        return None

def evaluate_with_rubric(question, answer, keywords, question_type="conceptual"):
    """Evaluate answer using rubric-based scoring"""
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
{{"total_score": <0-100>, "rubric": {{"correctness": <0-40>, "depth": <0-25>, "clarity": <0-15>, "structure": <0-10>, "real_world": <0-10>}},
"strengths": ["...", "..."], "improvements": ["...", "..."], "ideal_answer_outline": ["point 1", "point 2", "point 3"],
"rewritten_answer": "Professional version...", "feedback": "Overall feedback"}}"""

    response = call_groq_api(prompt, temperature=0.3, max_tokens=1500)
    if response:
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
    return keyword_rubric_evaluate(answer, keywords)

def keyword_rubric_evaluate(answer, keywords):
    """Fallback evaluation using keyword matching"""
    if not answer or len(keywords) == 0:
        return {
            "total_score": 0,
            "rubric": {"correctness": 0, "depth": 0, "clarity": 0, "structure": 0, "real_world": 0},
            "strengths": [],
            "improvements": ["Please provide an answer"],
            "ideal_answer_outline": ["Address key concepts", "Provide examples"],
            "rewritten_answer": "",
            "feedback": "No answer provided"
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
        "feedback": "👍 Good" if base_score >= 60 else "⚠️ Needs detail"
    }

# ═══════════════════════════════════════════════════════════
# RESUME PROCESSING
# ═══════════════════════════════════════════════════════════

def normalize_resume_text(text):
    """Normalize resume text to deterministic lowercase and collapsed spacing."""
    if not text:
        return ""
    normalized = text.replace("\r", "\n").lower()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9\s\+\-\.#/\\]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized

def extract_experience(text):
    normalized = normalize_resume_text(text)
    match = re.search(r"(\d+)\+?\s*years?\s+(?:of\s+)?experience", normalized)
    if match:
        return int(match.group(1))
    match = re.search(r"experience:\s*(\d+)", normalized)
    return int(match.group(1)) if match else 0

# Enhanced deterministic skill database with categories and aliases
SKILL_CATEGORIES = {
    'Programming': [
        'python', 'java', 'c', 'c++', 'c#', 'javascript', 'typescript', 'go', 'ruby'
    ],
    'Frontend': [
        'html', 'css', 'react', 'vue', 'angular', 'svelte', 'next.js', 'tailwind'
    ],
    'Backend': [
        'flask', 'fastapi', 'django', 'node.js', 'express', 'rest api', 'restful api',
        'jwt', 'authentication', 'authorization', 'mvc', 'microservices', 'api development'
    ],
    'Database': [
        'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'sqlite', 'redis', 'oracle', 'sqlalchemy', 'sqlmodel', 'orm'
    ],
    'Tools': [
        'git', 'github', 'vs code', 'vscode', 'postman', 'intellij', 'jira', 'docker', 'linux'
    ],
    'Cloud': [
        'aws', 'gcp', 'azure', 'cloud', 'kubernetes', 'ecs', 'eks', 'gke', 'docker'
    ],
    'DevOps': [
        'ci/cd', 'cicd', 'continuous integration', 'continuous delivery', 'github actions', 'jenkins', 'terraform', 'ansible', 'docker compose'
    ],
    'Testing': [
        'unit testing', 'integration testing', 'api testing', 'pytest', 'unittest', 'junit', 'mocha', 'jest', 'cypress'
    ],
    'Concepts': [
        'data structures', 'algorithms', 'oop', 'design patterns', 'rest api', 'microservices', 'api design'
    ]
}

SKILL_CANONICAL = {
    'js': 'javascript',
    'node': 'node.js',
    'nodejs': 'node.js',
    'restful api': 'rest api',
    'restapi': 'rest api',
    'jwt authentication': 'jwt',
    'jwt auth': 'jwt',
    'github actions': 'ci/cd',
    'continuous integration': 'ci/cd',
    'continuous delivery': 'ci/cd',
    'cicd': 'ci/cd',
    'mysql': 'mysql',
    'postgres': 'postgresql',
    'postgre': 'postgresql',
    'tf': 'tensorflow',
    'sklearn': 'scikit-learn',
    'fast api': 'fastapi',
    'restful': 'rest api'
}

ROLE_SKILL_PRIORITIES = {
    'Backend Developer': {
        'must': ['python', 'sql', 'api', 'database'],
        'preferred': ['flask', 'fastapi', 'django', 'node.js', 'express', 'postgresql', 'mongodb', 'rest api', 'jwt', 'authentication'],
        'tools': ['git', 'github', 'docker', 'postman', 'ci/cd', 'kubernetes'],
        'min_experience': 2
    },
    'Frontend Developer': {
        'must': ['javascript', 'html', 'css', 'react'],
        'preferred': ['typescript', 'vue', 'angular'],
        'tools': ['git', 'github', 'webpack'],
        'min_experience': 1
    },
    'Data Scientist': {
        'must': ['python', 'machine learning', 'statistics', 'sql'],
        'preferred': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch'],
        'tools': ['git', 'cloud'],
        'min_experience': 2
    },
    'ML Engineer': {
        'must': ['python', 'machine learning', 'docker'],
        'preferred': ['tensorflow', 'pytorch', 'mlops', 'kubernetes'],
        'tools': ['git', 'ci/cd'],
        'min_experience': 2
    },
    'Full Stack Developer': {
        'must': ['javascript', 'python', 'sql', 'react'],
        'preferred': ['node.js', 'django', 'postgresql'],
        'tools': ['git', 'docker', 'ci/cd'],
        'min_experience': 2
    },
    'DevOps Engineer': {
        'must': ['linux', 'docker', 'ci/cd'],
        'preferred': ['kubernetes', 'aws', 'azure', 'terraform', 'ansible'],
        'tools': ['git', 'monitoring'],
        'min_experience': 2
    }
}

def _normalize_skill_keyword(keyword):
    if not keyword:
        return ""
    normalized = keyword.lower().strip()
    normalized = normalized.replace("-", " ")
    normalized = normalized.replace("/", " ")
    normalized = normalized.replace(".", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = SKILL_CANONICAL.get(normalized, normalized)
    return normalized

def _has_keyword(normalized_text, keyword):
    k = _normalize_skill_keyword(keyword)
    pattern = r"\b" + re.escape(k) + r"\b"
    return bool(re.search(pattern, normalized_text))

def extract_skills_deterministic(text):
    normalized = normalize_resume_text(text)
    found = {}
    canonical_found = set()

    # find every keyword from category lists and aliases
    for category, keywords in SKILL_CATEGORIES.items():
        found[category] = []
        for keyword in keywords:
            normalized_keyword = _normalize_skill_keyword(keyword)
            if normalized_keyword in canonical_found:
                continue
            if _has_keyword(normalized, normalized_keyword):
                canonical_found.add(normalized_keyword)
                found[category].append(keyword.title() if keyword.islower() else keyword)

    # also detect alias keywords not in category lists
    for alias, canonical in SKILL_CANONICAL.items():
        normalized_canonical = _normalize_skill_keyword(canonical)
        if normalized_canonical in canonical_found:
            continue
        if _has_keyword(normalized, alias):
            canonical_found.add(normalized_canonical)
            # map canonical to category
            for category, keywords in SKILL_CATEGORIES.items():
                if canonical in keywords or normalized_canonical in [_normalize_skill_keyword(k) for k in keywords]:
                    found.setdefault(category, []).append(canonical.title())
                    break

    # remove duplicates and sort stable
    for category in found.keys():
        found[category] = sorted(set(found[category]), key=lambda x: x.lower())
    # drop empty categories
    return {cat: skills for cat, skills in found.items() if skills}

def _extract_section_match(text, section_keywords):
    normalized = normalize_resume_text(text)
    for kw in section_keywords:
        if _has_keyword(normalized, kw):
            return True
    return False

def _extract_score_components(resume_text, detected_skills, job_role):
    norm = normalize_resume_text(resume_text)
    role_profile = ROLE_SKILL_PRIORITIES.get(job_role, ROLE_SKILL_PRIORITIES['Backend Developer'])

    # Technical presence
    must = role_profile.get('must', [])
    preferred = role_profile.get('preferred', [])
    bonus = role_profile.get('tools', [])

    must_matches = sum(1 for s in must if _has_keyword(norm, s))
    pref_matches = sum(1 for s in preferred if _has_keyword(norm, s))
    bonus_matches = sum(1 for s in bonus if _has_keyword(norm, s))

    technical_ratio = (
        (must_matches / max(1, len(must))) * 0.7
        + (pref_matches / max(1, len(preferred))) * 0.2
        + (bonus_matches / max(1, len(bonus))) * 0.1
    )
    technical_score = round(40 * min(1.0, technical_ratio), 2)

    project_section = _extract_section_match(resume_text, ['project', 'projects'])
    project_keywords = [k for k in preferred + must if _has_keyword(norm, k)]
    project_relevance = 0.0
    if project_section:
        project_relevance = min(1.0, len(project_keywords) / max(1, len(must + preferred)))
    project_score = round(20 * project_relevance, 2)

    internship_section = _extract_section_match(resume_text, ['intern', 'internship'])
    exp_score = 0
    if internship_section:
        exp_score = 12
    exp_score += 3 if _extract_section_match(resume_text, ['experience']) else 0
    exp_score = min(15, exp_score)

    backend_project_mentions = sum(1 for k in [ 'flask', 'fastapi', 'django', 'node.js', 'express', 'rest api', 'jwt', 'mysql', 'postgresql', 'mongodb', 'docker', 'ci/cd' ] if _has_keyword(norm, k))
    backend_project_score = min(10, backend_project_mentions * 2)

    tool_devops_matches = sum(1 for k in ['docker', 'ci/cd', 'github actions', 'kubernetes', 'terraform', 'ansible', 'postman'] if _has_keyword(norm, k))
    tool_devops_score = min(10, tool_devops_matches * 2)

    completeness = 0
    if _extract_section_match(resume_text, ['summary', 'profile']):
        completeness += 2
    if _extract_section_match(resume_text, ['skills']):
        completeness += 1
    if _extract_section_match(resume_text, ['projects']):
        completeness += 1
    if _extract_section_match(resume_text, ['education']):
        completeness += 1
    completeness_score = min(5, completeness)

    return {
        'technical_score': technical_score,
        'project_score': project_score,
        'experience_score': exp_score,
        'backend_project_score': backend_project_score,
        'tool_devops_score': tool_devops_score,
        'completeness_score': completeness_score,
        'detailed': {
            'must_matches': must_matches,
            'preferred_matches': pref_matches,
            'bonus_matches': bonus_matches,
            'project_section': project_section,
            'internship_section': internship_section,
        }
    }


def generate_backend_recommendations(resume_text, detected_skills, job_role):
    normalized = normalize_resume_text(resume_text)
    role_profile = ROLE_SKILL_PRIORITIES.get(job_role, ROLE_SKILL_PRIORITIES['Backend Developer'])
    must = role_profile.get('must', [])
    preferred = role_profile.get('preferred', [])
    recommendations = []

    missing = [s for s in must if not _has_keyword(normalized, s)]
    missing += [s for s in preferred if not _has_keyword(normalized, s)]

    if 'docker' in missing:
        recommendations.append('Add Docker/containerization and a deployment bullet in your project section.')
    if any(k in missing for k in ['ci/cd', 'github actions', 'continuous integration']):
        recommendations.append('Include CI/CD workflow (GitHub Actions, Jenkins, or Terraform pipeline) in your projects or experience.')
    if any(k in missing for k in ['unit testing', 'api testing', 'integration testing']):
        recommendations.append('Mention unit/API/integration tests and test suites for your backend work.')
    if 'rest api' in missing or 'jwt' in missing:
        recommendations.append('Describe API design and authentication (JWT/OAuth) in a backend project bullet.')
    if not _extract_section_match(resume_text, ['summary', 'profile']):
        recommendations.append('Add a concise backend-focused summary highlighting Python, APIs, and databases.')
    if not _extract_section_match(resume_text, ['projects']):
        recommendations.append('Add a dedicated Backend Projects section with tech stack and outcomes.')

    if not recommendations:
        recommendations.append('Your resume looks strong. Add more quantifiable impact statements to improve further.')

    return recommendations


def validate_score_stability(resume_text, job_role, repeats=3):
    scores = [calculate_resume_score(resume_text, extract_skills_deterministic(resume_text), extract_experience(resume_text), job_role) for _ in range(repeats)]
    if len(set(scores)) > 1:
        return False, scores
    return True, scores[0]


def format_skills_for_ui(skills_dict):
    formatted = []
    for cat in sorted(skills_dict):
        skills = sorted(skills_dict[cat], key=lambda s: s.lower())
        formatted.extend(skills)
    return formatted


def parse_resume(uploaded_file):
    try:
        raw_bytes = uploaded_file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
        text = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
        normalized_text = normalize_resume_text(text)
        detected_skills = extract_skills_deterministic(normalized_text)
        experience = extract_experience(normalized_text)
        return text, detected_skills, experience
    except Exception as e:
        st.error(f"Failed to parse resume: {str(e)}")
        return "", {}, 0


def calculate_resume_score(resume_text, skills, experience, job_role, debug=False):
    normalized = normalize_resume_text(resume_text)
    if not job_role:
        job_role = 'Backend Developer'
    detected_skills = skills if isinstance(skills, dict) and skills else extract_skills_deterministic(resume_text)

    # Stable, weighted formula
    components = _extract_score_components(resume_text, detected_skills, job_role)
    total_score = (
        components['technical_score'] +
        components['project_score'] +
        components['experience_score'] +
        components['backend_project_score'] +
        components['tool_devops_score'] +
        components['completeness_score']
    )
    final_score = int(max(0, min(100, round(total_score))))

    if debug:
        return {
            'score': final_score,
            'components': components,
            'skills': detected_skills,
            'missing': sorted(set([
                s for s in ROLE_SKILL_PRIORITIES.get(job_role, {}).get('must', [])
                if not _has_keyword(normalized, s)
            ])),
        }
    return final_score

# ═══════════════════════════════════════════════════════════
# QUESTION GENERATION
# ═══════════════════════════════════════════════════════════

def validate_question_relevance(question_text, job_role):
    keywords = ROLE_VALIDATION_KEYWORDS.get(job_role, [])
    question_lower = question_text.lower()
    return any(keyword in question_lower for keyword in keywords)

def get_role_questions_by_category(job_role, num_questions=5):
    role_bank = ROLE_QUESTION_BANK.get(job_role, {})
    if not role_bank:
        return []
    all_questions = []
    for category_questions in role_bank.values():
        all_questions.extend(category_questions)
    random.shuffle(all_questions)
    return all_questions[:num_questions * 2]

def generate_personalized_questions(job_role, difficulty, resume_skills, conversation_history, num_questions=5):
    base_questions = get_role_questions_by_category(job_role, num_questions)
    if not base_questions:
        return get_default_questions(job_role)
    
    # Validate and filter
    validated_questions = [q for q in base_questions if validate_question_relevance(q['question'], job_role)][:num_questions]
    if len(validated_questions) < num_questions:
        for q in base_questions:
            if q not in validated_questions:
                validated_questions.append(q)
                if len(validated_questions) >= num_questions:
                    break
    
    # Ensure diversity by type
    by_type = {}
    for q in validated_questions[:num_questions]:
        q_type = q.get('type', 'conceptual')
        by_type.setdefault(q_type, []).append(q)
    
    final_questions = []
    while len(final_questions) < num_questions and by_type:
        for q_type in list(by_type.keys()):
            if by_type[q_type]:
                final_questions.append(by_type[q_type].pop(0))
                if not by_type[q_type]:
                    del by_type[q_type]
                if len(final_questions) >= num_questions:
                    break
    
    return final_questions[:num_questions]

def get_default_questions(job_role):
    # Imported from design.py
    from design import DEFAULT_QUESTIONS
    return DEFAULT_QUESTIONS.get(job_role, DEFAULT_QUESTIONS["Backend Developer"])

def get_intro_questions(job_role, mode):
    mode_config = INTERVIEW_MODE_CONFIG[mode]
    tone = mode_config["tone"]
    if tone == "friendly":
        return [
            {"question": f"Hi! Welcome to this practice interview for the {job_role} position. Let's start easy - tell me a bit about yourself and your background.", "category": "Introduction", "keywords": ["name", "background"], "is_intro": True},
            {"question": f"What interests you about working as a {job_role}?", "category": "Motivation", "keywords": ["interest", "passion"], "is_intro": True}
        ]
    else:
        return [
            {"question": f"Good morning. Thank you for joining us today. Please introduce yourself and walk me through your professional background relevant to this {job_role} position.", "category": "Introduction", "keywords": ["name", "background", "experience"], "is_intro": True},
            {"question": f"What specifically attracted you to apply for this {job_role} role at our company?", "category": "Motivation", "keywords": ["interest", "motivation", "company"], "is_intro": True},
            {"question": "Can you walk me through a challenging project you've worked on recently? What was your role, and what was the outcome?", "category": "Project Experience", "keywords": ["project", "challenge", "outcome"], "is_intro": True}
        ]

def generate_improvement_plan(session_id, job_role):
    try:
        with sqlite3.connect('interview_memory.db') as conn:
            c = conn.cursor()
            c.execute('''SELECT rubric_scores FROM performance WHERE session_id = ?''', (session_id,))
            rubric_data = c.fetchall()
    except Exception:
        return None
    
    if not rubric_data:
        return None
    
    rubric_totals = {"correctness": 0, "depth": 0, "clarity": 0, "structure": 0, "real_world": 0}
    count = len(rubric_data)
    for rubric_json, in rubric_data:
        try:
            rubric = json.loads(rubric_json)
            for key in rubric_totals.keys():
                rubric_totals[key] += rubric.get(key, 0)
        except Exception:
            pass
    
    rubric_avgs = {
        "correctness": rubric_totals["correctness"] / (count * 40),
        "depth": rubric_totals["depth"] / (count * 25),
        "clarity": rubric_totals["clarity"] / (count * 15),
        "structure": rubric_totals["structure"] / (count * 10),
        "real_world": rubric_totals["real_world"] / (count * 10)
    }
    
    weakest = sorted(rubric_avgs.items(), key=lambda x: x[1])[0][0]
    
    # Import from design.py
    from design import get_improvement_plan_data
    plans = get_improvement_plan_data()
    default_plan = plans.get(weakest, {}).get(job_role, None)
    
    if not default_plan:
        return [
            {"day": i+1, "focus": f"Improve {weakest.replace('_', ' ').title()}", 
             "tasks": [f"Study {weakest} techniques", "Practice daily", "Review examples"], 
             "resources": ["Online courses", "Technical blogs"]} 
            for i in range(7)
        ]
    return default_plan

# ═══════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════

def init_session_state():
    defaults = {
        'session_id': f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'interview_stage': 'not_started', 'question_num': 0, 'start_time': datetime.now(),
        'question_start_time': None, 'answers': [], 'scores': [], 'rubric_scores': [],
        'resume_text': '', 'resume_skills': {}, 'resume_experience': 0, 'resume_score': 0,
        'technical_questions': [], 'intro_questions': [], 'conversation_history': [],
        'character_fullscreen': False, 'current_question_text': '',
        'last_spoken_question_id': None, 'active_job_role': None,
        'active_difficulty': None, 'active_interview_mode': None,
        'logged_in': False, 'user': None, 'page': 'login',
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_interview_state():
    st.session_state.interview_stage = 'not_started'
    st.session_state.question_num = 0
    st.session_state.answers = []
    st.session_state.scores = []
    st.session_state.rubric_scores = []
    st.session_state.technical_questions = []
    st.session_state.intro_questions = []
    st.session_state.conversation_history = []
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.current_question_text = ""
    st.session_state.last_spoken_question_id = None
    st.session_state.start_time = datetime.now()
    st.session_state.question_start_time = None
    st.session_state.active_job_role = None
    st.session_state.active_difficulty = None
    st.session_state.active_interview_mode = None

def get_active_interview_config():
    return {
        'job_role': st.session_state.active_job_role,
        'difficulty': st.session_state.active_difficulty,
        'mode': st.session_state.active_interview_mode
    }

def speak_question(question_text, unique_key):
    if st.session_state.get('last_spoken_question_id') == unique_key:
        return
    escaped_text = question_text.replace('"', '\\"').replace("'", "\\'")
    st.components.v1.html(f"""
    <script>
    (function() {{
        const text = "{escaped_text}";
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        if (window.speechSynthesis) {{
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(utterance);
        }}
    }})();
    </script>
    """, height=0)
    st.session_state.last_spoken_question_id = unique_key

# ═══════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════

def main():
    init_session_state()
    apply_custom_css()

    # Authentication gate
    if not is_logged_in():
        if st.session_state.page == "register":
            render_register_page()
        else:
            render_login_page()
        return

    # Logged-in app
    st.sidebar.title("🎯 Navigation")

    user = get_current_user() or {}
    user_name = user.get('full_name') or user.get('username') or user.get('email') or "User"
    st.sidebar.write(f"👤 Logged in as: **{user_name}**")
    if st.sidebar.button("Logout"):
        logout_user()
        st.experimental_rerun()

    page = st.sidebar.radio("Go to", ["🏠 Home", "📄 Resume", "🎤 Interview", "📊 Results", "📈 Progress"])
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Settings")
    
    job_role = st.sidebar.selectbox("Position:", SUPPORTED_JOB_ROLES)
    difficulty = st.sidebar.select_slider("Level:", ["Beginner", "Intermediate", "Advanced"])
    interview_mode = st.sidebar.selectbox("Mode:", list(INTERVIEW_MODE_CONFIG.keys()))
    st.sidebar.caption(INTERVIEW_MODE_CONFIG[interview_mode]["description"])
    
    if st.session_state.interview_stage != 'not_started':
        st.sidebar.info("🔒 Interview settings locked during active session")
    
    st.sidebar.markdown("---")
    
    if GROQ_API_KEY:
        st.sidebar.success("🤖 AI: Active")
        st.sidebar.caption("✅ SQLite Memory\n✅ Role-Based Questions\n✅ Rubric Scoring")
    else:
        st.sidebar.warning("⚠️ AI: Limited (No API Key)")
    
    # Route to pages (protected)
    if page == "🏠 Home":
        render_home_page()
    elif page == "📄 Resume":
        render_resume_page(job_role)
    elif page == "🎤 Interview":
        render_interview_page(job_role, difficulty, interview_mode)
    elif page == "📊 Results":
        render_results_page()
    elif page == "📈 Progress":
        render_progress_page()
    
    st.markdown("<div style='text-align:center;color:#888;margin-top:50px'><p>AI-Powered Interview Preparation System | SQLite Memory | Premium Features</p></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()