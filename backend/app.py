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
    
    c.execute('''CREATE TABLE IF NOT EXISTS conversations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT,
                  timestamp DATETIME,
                  question TEXT,
                  answer TEXT,
                  category TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT UNIQUE,
                  job_role TEXT,
                  difficulty TEXT,
                  mode TEXT,
                  overall_score REAL,
                  completed_at DATETIME)''')
    
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

init_database()

def save_conversation(session_id, question, answer, category):
    conn = sqlite3.connect('interview_memory.db')
    c = conn.cursor()
    c.execute('''INSERT INTO conversations (session_id, timestamp, question, answer, category)
                 VALUES (?, ?, ?, ?, ?)''',
              (session_id, datetime.now(), question, answer, category))
    conn.commit()
    conn.close()

def save_session(session_id, job_role, difficulty, mode, overall_score):
    conn = sqlite3.connect('interview_memory.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO sessions 
                 (session_id, job_role, difficulty, mode, overall_score, completed_at)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (session_id, job_role, difficulty, mode, overall_score, datetime.now()))
    conn.commit()
    conn.close()

def save_performance(session_id, question, answer, score, rubric_scores, feedback, time_taken):
    conn = sqlite3.connect('interview_memory.db')
    c = conn.cursor()
    c.execute('''INSERT INTO performance 
                 (session_id, question, answer, score, rubric_scores, feedback, time_taken)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (session_id, question, answer, score, json.dumps(rubric_scores), feedback, time_taken))
    conn.commit()
    conn.close()

def load_session_history():
    conn = sqlite3.connect('interview_memory.db')
    c = conn.cursor()
    c.execute('''SELECT session_id, job_role, difficulty, overall_score, completed_at 
                 FROM sessions ORDER BY completed_at DESC''')
    sessions = c.fetchall()
    conn.close()
    return sessions

def get_conversation_context(session_id, limit=5):
    conn = sqlite3.connect('interview_memory.db')
    c = conn.cursor()
    c.execute('''SELECT question, answer FROM conversations 
                 WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?''',
              (session_id, limit))
    history = c.fetchall()
    conn.close()
    return [{"q": h[0], "a": h[1]} for h in reversed(history)]

# ═══════════════════════════════════════════════════════════
# ROLE-BASED QUESTION BANK
# ═══════════════════════════════════════════════════════════
ROLE_QUESTION_BANK = {
    "Backend Developer": {
        "conceptual": [
            {"question": "What is a REST API and how does it differ from GraphQL?", "category": "APIs", "keywords": ["REST", "API", "GraphQL", "endpoints"], "type": "conceptual"},
            {"question": "Explain the difference between SQL and NoSQL databases. When would you use each?", "category": "Databases", "keywords": ["SQL", "NoSQL", "database", "schema"], "type": "conceptual"},
            {"question": "What is JWT authentication and how does it work?", "category": "Authentication", "keywords": ["JWT", "token", "authentication", "security"], "type": "conceptual"},
            {"question": "Explain database indexing and its impact on query performance.", "category": "Databases", "keywords": ["indexing", "performance", "query", "optimization"], "type": "conceptual"},
            {"question": "What are microservices and how do they differ from monolithic architecture?", "category": "Architecture", "keywords": ["microservices", "architecture", "monolithic", "scalability"], "type": "conceptual"},
        ],
        "practical": [
            {"question": "How would you design a caching strategy for a high-traffic API?", "category": "Performance", "keywords": ["caching", "API", "performance", "redis"], "type": "practical"},
            {"question": "Walk me through how you would implement rate limiting for an API endpoint.", "category": "APIs", "keywords": ["rate limiting", "API", "throttling", "security"], "type": "practical"},
            {"question": "How would you handle database migrations in a production environment?", "category": "Databases", "keywords": ["migration", "database", "production", "versioning"], "type": "practical"},
            {"question": "Describe how you would implement user authentication and authorization in a web application.", "category": "Authentication", "keywords": ["authentication", "authorization", "security", "session"], "type": "practical"},
            {"question": "How would you optimize a slow database query?", "category": "Databases", "keywords": ["optimization", "query", "performance", "indexing"], "type": "practical"},
        ],
        "debugging": [
            {"question": "Your API is returning 500 errors intermittently. How would you debug this?", "category": "Debugging", "keywords": ["debugging", "error", "API", "logs"], "type": "debugging"},
            {"question": "Database queries are suddenly very slow. What steps would you take to identify the issue?", "category": "Databases", "keywords": ["debugging", "performance", "database", "monitoring"], "type": "debugging"},
            {"question": "Memory usage is spiking on your backend server. How do you investigate?", "category": "Performance", "keywords": ["memory", "debugging", "server", "profiling"], "type": "debugging"},
        ],
        "system_design": [
            {"question": "Design a URL shortening service backend. What API endpoints and database schema would you use?", "category": "System Design", "keywords": ["system design", "scalability", "database", "API", "backend"], "type": "tradeoff"},
            {"question": "How would you design a notification system backend that handles millions of users?", "category": "System Design", "keywords": ["system design", "scalability", "queue", "architecture", "backend"], "type": "tradeoff"},
            {"question": "Explain the trade-offs between consistency and availability in distributed backend systems.", "category": "Architecture", "keywords": ["CAP theorem", "distributed", "consistency", "availability", "backend"], "type": "tradeoff"},
        ]
    },
    
    "Frontend Developer": {
        "conceptual": [
            {"question": "Explain how React's virtual DOM works and why it improves performance.", "category": "React", "keywords": ["virtual DOM", "React", "performance", "reconciliation"], "type": "conceptual"},
            {"question": "What are React hooks and why were they introduced?", "category": "React", "keywords": ["hooks", "useState", "useEffect", "React"], "type": "conceptual"},
            {"question": "Explain the difference between client-side and server-side rendering.", "category": "Performance", "keywords": ["CSR", "SSR", "rendering", "performance"], "type": "conceptual"},
            {"question": "What is the event loop in JavaScript and how does it work?", "category": "JavaScript", "keywords": ["event loop", "async", "JavaScript", "callback"], "type": "conceptual"},
            {"question": "Explain CSS specificity and how the cascade works.", "category": "CSS", "keywords": ["CSS", "specificity", "cascade", "selectors"], "type": "conceptual"},
        ],
        "practical": [
            {"question": "How would you optimize a React application that is rendering slowly?", "category": "Performance", "keywords": ["optimization", "React", "performance", "memoization"], "type": "practical"},
            {"question": "Describe how you would implement responsive design for a complex web application.", "category": "UI/UX", "keywords": ["responsive", "CSS", "mobile", "design"], "type": "practical"},
            {"question": "How would you handle state management in a large React application?", "category": "React", "keywords": ["state", "Redux", "Context", "React"], "type": "practical"},
            {"question": "Walk me through how you would implement infinite scrolling in a React app.", "category": "JavaScript", "keywords": ["infinite scroll", "pagination", "performance", "JavaScript"], "type": "practical"},
            {"question": "How would you make a web application accessible to users with disabilities?", "category": "Accessibility", "keywords": ["accessibility", "ARIA", "WCAG", "a11y"], "type": "practical"},
        ],
        "debugging": [
            {"question": "Your React component is re-rendering too frequently. How do you debug this?", "category": "React", "keywords": ["React", "re-render", "debugging", "performance"], "type": "debugging"},
            {"question": "JavaScript code works in Chrome but fails in Safari. What's your debugging approach?", "category": "Debugging", "keywords": ["cross-browser", "debugging", "compatibility", "JavaScript"], "type": "debugging"},
            {"question": "Users report the page is blank on load. How do you troubleshoot this frontend issue?", "category": "Debugging", "keywords": ["debugging", "error", "console", "JavaScript"], "type": "debugging"},
        ],
    },
    
    "Data Scientist": {
        "ml_theory": [
            {"question": "Explain the bias-variance tradeoff in machine learning.", "category": "ML Theory", "keywords": ["bias", "variance", "overfitting", "underfitting", "machine learning"], "type": "conceptual"},
            {"question": "What is overfitting and how can you prevent it in machine learning models?", "category": "ML Theory", "keywords": ["overfitting", "regularization", "validation", "model"], "type": "conceptual"},
            {"question": "Explain gradient descent and its variants (SGD, Adam, etc.).", "category": "ML Theory", "keywords": ["gradient descent", "optimization", "SGD", "Adam"], "type": "conceptual"},
            {"question": "What is cross-validation and why is it important in data science?", "category": "ML Theory", "keywords": ["cross-validation", "k-fold", "validation", "model evaluation"], "type": "conceptual"},
            {"question": "Explain the difference between supervised and unsupervised learning.", "category": "ML Theory", "keywords": ["supervised", "unsupervised", "learning", "classification"], "type": "conceptual"},
        ],
        "statistics": [
            {"question": "What is p-value and how do you interpret it in statistical analysis?", "category": "Statistics", "keywords": ["p-value", "hypothesis testing", "statistics", "significance"], "type": "conceptual"},
            {"question": "Explain the Central Limit Theorem and its importance in data science.", "category": "Statistics", "keywords": ["CLT", "distribution", "statistics", "sampling"], "type": "conceptual"},
            {"question": "What is the difference between correlation and causation?", "category": "Statistics", "keywords": ["correlation", "causation", "statistics", "analysis"], "type": "conceptual"},
        ],
        "practical": [
            {"question": "How would you handle imbalanced datasets in a classification problem?", "category": "Data Preprocessing", "keywords": ["imbalanced", "SMOTE", "sampling", "classification", "data"], "type": "practical"},
            {"question": "Walk me through your approach to feature engineering for a new dataset.", "category": "Feature Engineering", "keywords": ["feature engineering", "preprocessing", "data", "model"], "type": "practical"},
            {"question": "How do you evaluate the performance of a regression model?", "category": "Model Evaluation", "keywords": ["regression", "metrics", "RMSE", "R-squared"], "type": "practical"},
            {"question": "Describe your process for selecting the best machine learning algorithm for a problem.", "category": "Model Selection", "keywords": ["algorithm selection", "model", "comparison", "metrics"], "type": "practical"},
            {"question": "How would you handle missing data in a dataset?", "category": "Data Preprocessing", "keywords": ["missing data", "imputation", "preprocessing", "cleaning"], "type": "practical"},
        ],
    },
    
    "ML Engineer": {
        "mlops": [
            {"question": "How do you monitor machine learning models in production?", "category": "MLOps", "keywords": ["monitoring", "production", "drift", "metrics", "mlops"], "type": "practical"},
            {"question": "Explain model versioning and why it's important in ML engineering.", "category": "MLOps", "keywords": ["versioning", "model", "deployment", "tracking"], "type": "conceptual"},
            {"question": "How would you handle model drift in production ML systems?", "category": "MLOps", "keywords": ["model drift", "retraining", "monitoring", "production"], "type": "practical"},
        ],
        "deployment": [
            {"question": "How would you deploy a machine learning model as a REST API?", "category": "Deployment", "keywords": ["deployment", "API", "REST", "serving", "model"], "type": "practical"},
            {"question": "Explain the difference between batch and real-time inference in ML systems.", "category": "Deployment", "keywords": ["batch", "real-time", "inference", "prediction"], "type": "conceptual"},
            {"question": "How do you optimize model inference time for production deployment?", "category": "Performance", "keywords": ["optimization", "inference", "latency", "performance"], "type": "practical"},
        ],
    },
    
    "Full Stack Developer": {
        "frontend": [
            {"question": "How would you optimize the initial page load time of a full-stack web application?", "category": "Performance", "keywords": ["optimization", "page load", "performance", "frontend"], "type": "practical"},
            {"question": "Explain how you would implement authentication in a full-stack application.", "category": "Authentication", "keywords": ["authentication", "JWT", "session", "security", "fullstack"], "type": "practical"},
        ],
        "backend": [
            {"question": "How do you design RESTful APIs for a full-stack application?", "category": "APIs", "keywords": ["REST", "API", "design", "endpoints", "backend"], "type": "practical"},
            {"question": "Explain your approach to database schema design in full-stack development.", "category": "Databases", "keywords": ["database", "schema", "design", "normalization"], "type": "practical"},
        ],
    },
    
    "DevOps Engineer": {
        "infrastructure": [
            {"question": "Explain Infrastructure as Code and its benefits in DevOps.", "category": "IaC", "keywords": ["infrastructure", "terraform", "IaC", "automation", "devops"], "type": "conceptual"},
            {"question": "How do you implement monitoring and alerting for production systems?", "category": "Monitoring", "keywords": ["monitoring", "alerting", "prometheus", "grafana"], "type": "practical"},
        ],
        "ci_cd": [
            {"question": "How would you design a CI/CD pipeline for a microservices architecture?", "category": "CI/CD", "keywords": ["CI/CD", "pipeline", "microservices", "automation"], "type": "practical"},
            {"question": "Explain the difference between blue-green and canary deployments.", "category": "Deployment", "keywords": ["blue-green", "canary", "deployment", "strategy"], "type": "conceptual"},
        ],
    }
}

ROLE_VALIDATION_KEYWORDS = {
    "Backend Developer": [
        "api", "rest", "graphql", "database", "sql", "nosql", "server", "backend",
        "authentication", "authorization", "jwt", "microservices", "caching",
        "redis", "endpoint", "route", "middleware", "orm", "migration"
    ],
    "Frontend Developer": [
        "react", "vue", "angular", "javascript", "typescript", "html", "css",
        "dom", "component", "hooks", "state", "props", "jsx", "frontend",
        "ui", "ux", "responsive", "browser", "webpack", "bundler"
    ],
    "Data Scientist": [
        "machine learning", "ml", "model", "algorithm", "data", "statistics",
        "regression", "classification", "clustering", "training", "prediction",
        "feature", "dataset", "pandas", "numpy", "scikit", "tensorflow"
    ],
    "ML Engineer": [
        "mlops", "deployment", "production", "inference", "serving", "pipeline",
        "docker", "kubernetes", "model", "monitoring", "drift", "retraining",
        "api", "batch", "real-time", "optimization", "scaling"
    ],
    "Full Stack Developer": [
        "frontend", "backend", "fullstack", "api", "database", "react", "node",
        "express", "mongodb", "postgresql", "authentication", "deployment",
        "integration", "rest", "websocket"
    ],
    "DevOps Engineer": [
        "ci/cd", "jenkins", "gitlab", "docker", "kubernetes", "terraform",
        "ansible", "monitoring", "prometheus", "grafana", "infrastructure",
        "deployment", "automation", "cloud", "aws", "azure", "pipeline"
    ]
}

def validate_question_relevance(question_text: str, job_role: str) -> bool:
    """Check if a question is relevant to the given job role."""
    keywords = ROLE_VALIDATION_KEYWORDS.get(job_role, [])
    question_lower = question_text.lower()
    
    for keyword in keywords:
        if keyword in question_lower:
            return True
    
    return False

def get_role_questions_by_category(job_role: str, num_questions: int = 5) -> list:
    """Get diverse questions from the role-specific question bank."""
    role_bank = ROLE_QUESTION_BANK.get(job_role, {})
    
    if not role_bank:
        return []
    
    all_questions = []
    for category_questions in role_bank.values():
        all_questions.extend(category_questions)
    
    random.shuffle(all_questions)
    
    return all_questions[:num_questions * 2]  # Get extra for diversity

# ═══════════════════════════════════════════════════════════
# GROQ AI
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
        response = requests.post("https://api.groq.com/openai/v1/chat/completions",
                                headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except:
        return None

def generate_personalized_questions(job_role, difficulty, resume_skills, conversation_history, num_questions=5):
    """
    Generate role-specific interview questions with strict validation.
    Questions are pulled from a curated role-based question bank.
    """
    
    # Get base questions from role-specific bank
    base_questions = get_role_questions_by_category(job_role, num_questions)
    
    if not base_questions:
        # Fallback to default questions if role not found
        return get_default_questions(job_role)
    
    # Validate all questions are role-relevant
    validated_questions = []
    
    for q in base_questions:
        if validate_question_relevance(q['question'], job_role):
            validated_questions.append(q)
            if len(validated_questions) >= num_questions:
                break
    
    # Ensure we have enough questions
    if len(validated_questions) < num_questions:
        additional_needed = num_questions - len(validated_questions)
        for q in base_questions:
            if q not in validated_questions:
                validated_questions.append(q)
                if len(validated_questions) >= num_questions:
                    break
    
    # Ensure diverse question types
    by_type = {}
    for q in validated_questions[:num_questions]:
        q_type = q.get('type', 'conceptual')
        if q_type not in by_type:
            by_type[q_type] = []
        by_type[q_type].append(q)
    
    # Build final list with diversity
    final_questions = []
    question_types = list(by_type.keys())
    
    while len(final_questions) < num_questions and by_type:
        for q_type in question_types:
            if q_type in by_type and by_type[q_type]:
                final_questions.append(by_type[q_type].pop(0))
                if not by_type[q_type]:
                    del by_type[q_type]
                if len(final_questions) >= num_questions:
                    break
    
    # Fill remaining if needed
    while len(final_questions) < num_questions and validated_questions:
        for q in validated_questions:
            if q not in final_questions:
                final_questions.append(q)
                if len(final_questions) >= num_questions:
                    break
    
    return final_questions[:num_questions]

def evaluate_with_rubric(question, answer, keywords, question_type="conceptual"):
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
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
    
    return keyword_rubric_evaluate(answer, keywords)

def keyword_rubric_evaluate(answer, keywords):
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
    """Fallback questions if role not in bank."""
    defaults = {
        "Backend Developer": [
            {"question": "Explain REST API design principles and best practices.", "category": "APIs", "keywords": ["REST", "API", "design", "backend"], "type": "conceptual"},
            {"question": "How do you optimize database queries for better performance?", "category": "Databases", "keywords": ["database", "optimization", "query", "performance"], "type": "practical"},
            {"question": "What is JWT authentication and when would you use it?", "category": "Authentication", "keywords": ["JWT", "authentication", "token", "security"], "type": "conceptual"},
            {"question": "How would you design a caching strategy for an API?", "category": "Performance", "keywords": ["caching", "API", "performance", "redis"], "type": "practical"},
            {"question": "Explain microservices architecture and its trade-offs.", "category": "Architecture", "keywords": ["microservices", "architecture", "backend", "scalability"], "type": "tradeoff"},
        ],
        "Frontend Developer": [
            {"question": "Explain React component lifecycle and hooks.", "category": "React", "keywords": ["React", "lifecycle", "component", "hooks"], "type": "conceptual"},
            {"question": "How do you optimize React application performance?", "category": "Performance", "keywords": ["React", "optimization", "performance", "frontend"], "type": "practical"},
            {"question": "What is the virtual DOM and how does it work?", "category": "React", "keywords": ["virtual DOM", "React", "rendering", "performance"], "type": "conceptual"},
            {"question": "How would you implement responsive design?", "category": "CSS", "keywords": ["responsive", "CSS", "mobile", "design"], "type": "practical"},
            {"question": "Explain state management in React applications.", "category": "React", "keywords": ["state", "React", "Redux", "Context"], "type": "tradeoff"},
        ],
        "Data Scientist": [
            {"question": "Explain the bias-variance tradeoff in machine learning.", "category": "ML Theory", "keywords": ["bias", "variance", "overfitting", "machine learning"], "type": "conceptual"},
            {"question": "How do you handle imbalanced datasets?", "category": "Data", "keywords": ["imbalanced", "sampling", "data", "classification"], "type": "practical"},
            {"question": "What is cross-validation and why is it important?", "category": "ML Theory", "keywords": ["cross-validation", "validation", "model", "evaluation"], "type": "conceptual"},
            {"question": "How do you select features for a machine learning model?", "category": "Feature Engineering", "keywords": ["feature selection", "engineering", "model", "data"], "type": "practical"},
            {"question": "Compare Random Forest and Gradient Boosting algorithms.", "category": "Algorithms", "keywords": ["Random Forest", "Gradient Boosting", "ensemble", "comparison"], "type": "tradeoff"},
        ],
        "ML Engineer": [
            {"question": "How do you deploy a machine learning model to production?", "category": "Deployment", "keywords": ["deployment", "production", "model", "mlops"], "type": "practical"},
            {"question": "Explain model monitoring and drift detection.", "category": "MLOps", "keywords": ["monitoring", "drift", "production", "model"], "type": "conceptual"},
            {"question": "How would you optimize model inference time?", "category": "Performance", "keywords": ["optimization", "inference", "performance", "model"], "type": "practical"},
        ],
        "Full Stack Developer": [
            {"question": "How do you design a full-stack application architecture?", "category": "Architecture", "keywords": ["architecture", "fullstack", "design", "scalability"], "type": "practical"},
            {"question": "Explain authentication flow in a full-stack app.", "category": "Authentication", "keywords": ["authentication", "security", "fullstack", "JWT"], "type": "conceptual"},
        ],
        "DevOps Engineer": [
            {"question": "How do you set up a CI/CD pipeline?", "category": "CI/CD", "keywords": ["CI/CD", "pipeline", "automation", "deployment"], "type": "practical"},
            {"question": "Explain Infrastructure as Code with Terraform.", "category": "IaC", "keywords": ["terraform", "IaC", "infrastructure", "automation"], "type": "conceptual"},
        ]
    }
    
    return defaults.get(job_role, defaults.get("Backend Developer", []))

def generate_improvement_plan(session_id, job_role):
    """Generate structured 7-day plan from actual performance data"""
    
    conn = sqlite3.connect('interview_memory.db')
    c = conn.cursor()
    c.execute('''SELECT rubric_scores FROM performance WHERE session_id = ?''', (session_id,))
    rubric_data = c.fetchall()
    conn.close()
    
    if not rubric_data:
        return None
    
    rubric_totals = {"correctness": 0, "depth": 0, "clarity": 0, "structure": 0, "real_world": 0}
    count = len(rubric_data)
    
    for rubric_json, in rubric_data:
        try:
            rubric = json.loads(rubric_json)
            for key in rubric_totals.keys():
                rubric_totals[key] += rubric.get(key, 0)
        except:
            pass
    
    rubric_avgs = {
        "correctness": rubric_totals["correctness"] / (count * 40),
        "depth": rubric_totals["depth"] / (count * 25),
        "clarity": rubric_totals["clarity"] / (count * 15),
        "structure": rubric_totals["structure"] / (count * 10),
        "real_world": rubric_totals["real_world"] / (count * 10)
    }
    
    sorted_rubrics = sorted(rubric_avgs.items(), key=lambda x: x[1])
    weakest = sorted_rubrics[0][0]
    
    plans = {
        "correctness": {
            "Data Scientist": [
                {"day": 1, "focus": "Core ML Concepts", "tasks": ["Review bias-variance tradeoff", "Study overfitting vs underfitting", "Practice explaining algorithms"], "resources": ["StatQuest YouTube", "Hands-On ML book"]},
                {"day": 2, "focus": "Algorithm Deep Dive", "tasks": ["Compare supervised vs unsupervised learning", "Explain 3 algorithms in detail", "Create comparison chart"], "resources": ["Scikit-learn docs", "ML Mastery"]},
                {"day": 3, "focus": "Model Evaluation", "tasks": ["Practice metrics (precision, recall, F1)", "Explain ROC curves", "Calculate metrics by hand"], "resources": ["Kaggle Learn", "Analytics Vidhya"]},
                {"day": 4, "focus": "Feature Engineering", "tasks": ["Study feature selection methods", "Practice encoding techniques", "Review dimensionality reduction"], "resources": ["Feature Engineering book", "Towards Data Science"]},
                {"day": 5, "focus": "Mock Interview Day", "tasks": ["Record yourself answering 5 questions", "Review and self-critique", "Identify gaps"], "resources": ["Pramp", "Interviewing.io"]},
                {"day": 6, "focus": "Edge Cases & Trade-offs", "tasks": ["Study when algorithms fail", "Compare time/space complexity", "Practice explaining trade-offs"], "resources": ["Big-O Cheat Sheet", "AlgoExpert"]},
                {"day": 7, "focus": "Final Review", "tasks": ["Retake interview on this platform", "Compare before/after scores", "Note improvements"], "resources": ["This platform"]}
            ],
            "Frontend Developer": [
                {"day": 1, "focus": "React Fundamentals", "tasks": ["Review component lifecycle", "Study hooks in depth", "Practice useState/useEffect"], "resources": ["React docs", "React Tutorial"]},
                {"day": 2, "focus": "State Management", "tasks": ["Compare Redux vs Context API", "Build mini app with state", "Explain data flow"], "resources": ["Redux docs", "egghead.io"]},
                {"day": 3, "focus": "Performance", "tasks": ["Study React.memo and useMemo", "Learn code splitting", "Practice lazy loading"], "resources": ["web.dev", "React Performance"]},
                {"day": 4, "focus": "Modern JS/TS", "tasks": ["Review ES6+ features", "Practice async/await", "Study TypeScript basics"], "resources": ["MDN Web Docs", "TypeScript Handbook"]},
                {"day": 5, "focus": "Mock Interview", "tasks": ["Record 5 technical answers", "Review code examples", "Practice live coding"], "resources": ["LeetCode Frontend", "CodeSandbox"]},
                {"day": 6, "focus": "Browser APIs", "tasks": ["Study DOM manipulation", "Review event handling", "Practice fetch/axios"], "resources": ["JavaScript.info", "MDN"]},
                {"day": 7, "focus": "Final Practice", "tasks": ["Retake interview", "Build small project", "Review mistakes"], "resources": ["This platform", "Frontend Mentor"]}
            ]
        },
        "depth": {
            "Data Scientist": [
                {"day": 1, "focus": "Adding Real Examples", "tasks": ["For each concept, find 2 real-world use cases", "Create example library", "Practice explaining with examples"], "resources": ["Kaggle case studies", "Papers with Code"]},
                {"day": 2, "focus": "Industry Applications", "tasks": ["Study how Netflix uses ML", "Review Uber's ML platform", "Find 3 case studies"], "resources": ["Tech blogs", "Medium Engineering"]},
                {"day": 3, "focus": "Edge Cases", "tasks": ["Identify when algorithms fail", "Study common pitfalls", "Practice troubleshooting"], "resources": ["Stack Overflow", "Cross Validated"]},
                {"day": 4, "focus": "Deep Technical Dive", "tasks": ["Pick 1 algorithm, study math", "Implement from scratch", "Explain every step"], "resources": ["Andrew Ng course", "3Blue1Brown"]},
                {"day": 5, "focus": "Comparative Analysis", "tasks": ["Compare 3 similar algorithms", "List pros/cons", "Practice choosing best fit"], "resources": ["Scikit-learn comparison", "ML cheatsheet"]},
                {"day": 6, "focus": "Production Insights", "tasks": ["Study MLOps practices", "Review model deployment", "Learn monitoring"], "resources": ["MLOps community", "Google MLOps"]},
                {"day": 7, "focus": "Practice with Depth", "tasks": ["Retake interview", "Include 2+ examples per answer", "Explain trade-offs"], "resources": ["This platform"]}
            ],
            "Frontend Developer": [
                {"day": 1, "focus": "Real-World Examples", "tasks": ["For each React concept, find production examples", "Study popular apps' architecture", "Document patterns"], "resources": ["React Patterns", "GitHub repos"]},
                {"day": 2, "focus": "Performance Deep Dive", "tasks": ["Study bundle size optimization", "Review render optimization", "Learn profiling"], "resources": ["Webpack Academy", "React DevTools"]},
                {"day": 3, "focus": "Accessibility Details", "tasks": ["Study WCAG guidelines", "Practice keyboard navigation", "Review screen readers"], "resources": ["a11y project", "ARIA practices"]},
                {"day": 4, "focus": "Browser Internals", "tasks": ["Study how rendering works", "Learn about reflows/repaints", "Review critical render path"], "resources": ["web.dev", "Browser rendering"]},
                {"day": 5, "focus": "Framework Comparisons", "tasks": ["Compare React vs Vue vs Angular", "List trade-offs", "Practice explaining choices"], "resources": ["State of JS", "Framework docs"]},
                {"day": 6, "focus": "Advanced Patterns", "tasks": ["Study HOCs vs Render Props vs Hooks", "Practice compound components", "Review design patterns"], "resources": ["Patterns.dev", "React patterns"]},
                {"day": 7, "focus": "Detailed Practice", "tasks": ["Retake interview", "Add specific examples", "Explain implementation details"], "resources": ["This platform"]}
            ]
        },
        "clarity": {
            "Data Scientist": [
                {"day": 1, "focus": "STAR Method", "tasks": ["Practice structuring answers: Situation, Task, Action, Result", "Record 3 answers", "Get feedback"], "resources": ["STAR method guide", "Mock Interview Practice"]},
                {"day": 2, "focus": "Clear Explanations", "tasks": ["Explain complex topics to non-technical friend", "Use analogies", "Avoid jargon"], "resources": ["Explain Like I'm 5", "Communication skills"]},
                {"day": 3, "focus": "Logical Flow", "tasks": ["Outline before answering", "Use transitions (First, Then, Finally)", "Practice sequencing"], "resources": ["Toastmasters", "Presentation skills"]},
                {"day": 4, "focus": "Conciseness", "tasks": ["Answer in 2 minutes max", "Remove filler words", "Practice elevator pitches"], "resources": ["Public speaking tips", "Brevity guide"]},
                {"day": 5, "focus": "Visual Thinking", "tasks": ["Draw diagrams while explaining", "Use whiteboard practice", "Create mental models"], "resources": ["System design", "Visual explanations"]},
                {"day": 6, "focus": "Active Listening", "tasks": ["Rephrase questions before answering", "Ask clarifying questions", "Practice pausing"], "resources": ["Interview communication", "Active listening"]},
                {"day": 7, "focus": "Structured Practice", "tasks": ["Retake interview", "Use clear structure in all answers", "Record and review"], "resources": ["This platform"]}
            ],
            "Frontend Developer": [
                {"day": 1, "focus": "Code Walkthroughs", "tasks": ["Practice explaining code line-by-line", "Use clear variable names", "Add comments"], "resources": ["Clean Code book", "Code review best practices"]},
                {"day": 2, "focus": "Technical Communication", "tasks": ["Explain async/await clearly", "Break down complex components", "Use diagrams"], "resources": ["Technical writing", "Developer communication"]},
                {"day": 3, "focus": "Problem-Solving Narration", "tasks": ["Think aloud while coding", "Explain your thought process", "Practice debugging narratives"], "resources": ["Coding interview patterns", "Pramp"]},
                {"day": 4, "focus": "Structured Answers", "tasks": ["Use frameworks: Problem → Approach → Solution", "Practice organized responses", "Eliminate rambling"], "resources": ["STAR method", "Interview prep"]},
                {"day": 5, "focus": "Simplification", "tasks": ["Explain React to a beginner", "Remove unnecessary complexity", "Use simple words"], "resources": ["ELI5 programming", "Teaching resources"]},
                {"day": 6, "focus": "Q&A Practice", "tasks": ["Practice answering unexpected questions", "Stay calm and organized", "Ask for clarification"], "resources": ["Mock interviews", "Interview.io"]},
                {"day": 7, "focus": "Clear Communication", "tasks": ["Retake interview", "Focus on logical flow", "Review clarity"], "resources": ["This platform"]}
            ]
        }
    }
    
    default_plan = plans.get(weakest, {}).get(job_role, None)
    
    if not default_plan:
        return [
            {"day": i+1, "focus": f"Improve {weakest.replace('_', ' ').title()}", 
             "tasks": [f"Study {weakest} techniques", "Practice daily", "Review examples"], 
             "resources": ["Online courses", "Technical blogs"]} 
            for i in range(7)
        ]
    
    return default_plan

def get_intro_questions(job_role, mode):
    """
    Generate introduction questions based on interview mode.
    Practice Mode: 2 questions (lighter, friendlier)
    Strict Interview: 3 questions (more formal, realistic)
    """
    
    if mode == "Practice Mode":
        return [
            {
                "question": f"Hi! Welcome to this practice interview for the {job_role} position. Let's start easy - tell me a bit about yourself and your background.",
                "category": "Introduction",
                "keywords": ["name", "background"],
                "is_intro": True
            },
            {
                "question": f"What interests you about working as a {job_role}?",
                "category": "Motivation",
                "keywords": ["interest", "passion"],
                "is_intro": True
            }
        ]
    else:  # Strict Interview
        return [
            {
                "question": f"Good morning. Thank you for joining us today. Please introduce yourself and walk me through your professional background relevant to this {job_role} position.",
                "category": "Introduction",
                "keywords": ["name", "background", "experience"],
                "is_intro": True
            },
            {
                "question": f"What specifically attracted you to apply for this {job_role} role at our company?",
                "category": "Motivation",
                "keywords": ["interest", "motivation", "company"],
                "is_intro": True
            },
            {
                "question": "Can you walk me through a challenging project you've worked on recently? What was your role, and what was the outcome?",
                "category": "Project Experience",
                "keywords": ["project", "challenge", "outcome"],
                "is_intro": True
            }
        ]

IT_JOB_ROLES = [
    "Data Scientist", "ML Engineer", "AI/ML Researcher", "Data Engineer", "Data Analyst",
    "Frontend Developer", "Backend Developer", "Full Stack Developer", "DevOps Engineer",
    "Cloud Engineer (AWS/Azure/GCP)", "Software Engineer", "QA Engineer",
    "Cybersecurity Analyst", "Database Administrator", "Mobile Developer (iOS/Android)",
    "UI/UX Designer", "Product Manager (Tech)", "Solutions Architect", "SRE",
    "Blockchain Developer", "NLP Engineer", "Computer Vision Engineer"
]

# ✅ FIXED: Only 2 modes now (removed Company Style)
INTERVIEW_MODES = {
    "Practice Mode": "Lighter interview flow, 2 intro + 3 technical questions",
    "Strict Interview": "Real interview simulation, 3 intro + 5 technical questions"
}

# ═══════════════════════════════════════════════════════════
# RESUME PARSING & SCORING
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
    s = re.sub(r"[^a-z0-9\.\+\-\s/]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return f" {s} "

def _skill_present(text: str, skill: str) -> bool:
    skill_n = _normalize_text(skill).strip()
    if f" {skill_n} " in text:
        return True
    for alias in _SKILL_ALIASES.get(skill_n, []):
        alias_n = _normalize_text(alias).strip()
        if f" {alias_n} " in text:
            return True
    return False

def calculate_resume_score(resume_text: str, skills: dict, experience: int, job_role: str) -> int:
    """Role-aware resume scoring (15-92 range)"""
    requirements = ROLE_REQUIRED_SKILLS.get(job_role, {
        "must_have": ["programming"],
        "preferred": [],
        "bonus": [],
        "min_experience": 1
    })
    
    all_resume_skills = []
    if isinstance(skills, dict):
        for _, skill_list in skills.items():
            if isinstance(skill_list, list):
                all_resume_skills.extend([str(s) for s in skill_list if s])
    
    resume_text = _normalize_text(resume_text)
    detected_skill_count = len(all_resume_skills)
    
    score = 0
    
    must_have = requirements["must_have"]
    must_found = sum(1 for sk in must_have if _skill_present(resume_text, sk))
    must_ratio = must_found / len(must_have) if len(must_have) > 0 else 0.0
    must_score = int(44 * must_ratio)
    missing = len(must_have) - must_found
    must_score -= missing * 6
    must_score = max(0, must_score)
    score += must_score
    
    preferred = requirements["preferred"]
    pref_found = sum(1 for sk in preferred if _skill_present(resume_text, sk))
    pref_score = min(28, pref_found * 4)
    score += pref_score
    
    bonus = requirements["bonus"]
    bonus_found = sum(1 for sk in bonus if _skill_present(resume_text, sk))
    bonus_score = min(10, bonus_found * 2)
    score += bonus_score
    
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
    
    if detected_skill_count >= 12:
        score += 6
    elif detected_skill_count >= 8:
        score += 4
    elif detected_skill_count >= 4:
        score += 2
    
    seed_str = f"{job_role}|{exp}|{'|'.join(sorted([s.lower() for s in all_resume_skills]))}"
    h = hashlib.md5(seed_str.encode("utf-8")).hexdigest()
    jitter = (int(h[:2], 16) % 5) - 2
    score += jitter
    
    final_score = max(15, min(92, score))
    return int(final_score)

# ═══════════════════════════════════════════════════════════
# TTS HELPER
# ═══════════════════════════════════════════════════════════
def speak_question(question_text: str, unique_key: str):
    """Speak question using browser TTS"""
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
if 'character_fullscreen' not in st.session_state:
    st.session_state.character_fullscreen = False
if 'current_question_text' not in st.session_state:
    st.session_state.current_question_text = ""

# ═══════════════════════════════════════════════════════════
# GLOBAL CSS - FIXED UI
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
.main-header { font-size: 3rem; font-weight: bold; text-align: center; color: #1E88E5; }

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

.question-card {
    background: #0f172a;
    border-radius: 12px;
    padding: 32px;
    margin: 20px 0;
    border-left: 5px solid #3b82f6;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
}
.question-card h3 {
    color: #f8fafc !important;
    font-size: 1.4rem !important;
    line-height: 1.8 !important;
    margin-bottom: 16px !important;
    font-weight: 500 !important;
}
.question-card p {
    color: #cbd5e1;
    font-size: 1rem;
    line-height: 1.6;
}

.caption-box {
    background: #1e293b;
    border: 2px solid #3b82f6;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 16px 0;
    text-align: center;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}
.caption-box h4 {
    color: #60a5fa;
    font-size: 0.9rem;
    margin: 0 0 8px 0;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.caption-box p {
    color: #f8fafc;
    font-size: 1.2rem;
    line-height: 1.6;
    margin: 0;
}

.score-card { 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 24px; 
    border-radius: 12px; 
    color: white; 
    text-align: center; 
}

.ideal-answer { 
    background: #e8f5e9; 
    border-left: 4px solid #4caf50;
    padding: 16px; 
    border-radius: 8px; 
    margin: 10px 0;
    color: #1b5e20;
}

.rewritten-answer { 
    background: #e3f2fd; 
    border-left: 4px solid #2196f3;
    padding: 16px; 
    border-radius: 8px; 
    margin: 10px 0;
    color: #0d47a1;
}

/* ✅ Fixed button styling - no more vertical text */
.stButton>button { 
    background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
    color: white !important; 
    border-radius: 8px; 
    padding: 0.6rem 2rem !important; 
    font-weight: 600;
    border: none;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
    text-align: center;
    display: inline-block;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(30, 136, 229, 0.4);
}

/* ✅ Fix column alignment - prevents vertical button layout */
[data-testid="column"] {
    display: flex;
    align-items: center;
    flex-direction: column;
}

/* ✅ Ensure iframe fits properly - no overflow */
iframe {
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    width: 100%;
    max-width: 100%;
}
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
            st.session_state.resume_score = calculate_resume_score(text, skills, exp, job_role)
            st.balloons()
            st.rerun()
    
    if st.session_state.resume_skills:
        score = st.session_state.resume_score
        st.markdown(f"<div class='score-card'><h2>{score}%</h2><p>{job_role} Match</p></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# ✅ FIXED INTERVIEW PAGE - CLEAN UI, 2 MODES ONLY
# ═══════════════════════════════════════════════════════════
elif page == "🎤 Interview":
    st.title("🎤 Professional Interview")
    
    # ✅ Get dynamic question counts based on mode
    intro_count = 2 if interview_mode == "Practice Mode" else 3
    tech_count = 3 if interview_mode == "Practice Mode" else 5
    total_count = intro_count + tech_count
    
    # Restart button
    if st.session_state.interview_stage != 'not_started':
        col_restart, col_spacer = st.columns([1, 5])
        with col_restart:
            if st.button("🔄 Restart", use_container_width=True):
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
                st.rerun()
    
    # ✅ Top info bar - Fixed layout (no vertical buttons)
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        st.markdown(f"### 🎯 {job_role}")
    with col2:
        st.markdown(f"**Mode:** {interview_mode.split()[0]}")
    with col3:
        if st.session_state.interview_stage != 'not_started':
            elapsed = (datetime.now() - st.session_state.start_time).seconds
            st.markdown(f"**⏱️** {elapsed//60:02d}:{elapsed%60:02d}")
        else:
            st.markdown(f"**⏱️** --:--")
    with col4:
        if st.session_state.question_start_time and st.session_state.interview_stage != 'not_started':
            st.markdown(f"**🕐** {(datetime.now() - st.session_state.question_start_time).seconds}s")
    
    st.markdown("---")
    
    # ✅ 3D Interviewer Section - Fixed layout
    st.subheader("🤖 AI Interviewer")
    
    # ✅ Fullscreen toggle - Fixed horizontal layout
    col_fs, col_spacer = st.columns([1, 5])
    with col_fs:
        if st.button(
            "🖥️ Fullscreen" if not st.session_state.character_fullscreen else "🔲 Exit", 
            use_container_width=True
        ):
            st.session_state.character_fullscreen = not st.session_state.character_fullscreen
            st.rerun()
    
    # Character iframe - responsive height
    iframe_height = 850 if st.session_state.character_fullscreen else 600
    st.components.v1.iframe(FRONTEND_URL, height=iframe_height, scrolling=False)
    
    # Voice interview integration (collapsible)
    with st.expander("🎙️ Voice Interview Mode", expanded=False):
        st.info("💡 Use microphone for hands-free interview practice")
        voice_url = f"{FRONTEND_URL}/voice"
        st.components.v1.html(f"""
        <iframe 
            src="{voice_url}" 
            width="100%" 
            height="700" 
            frameborder="0"
            allow="microphone"
            style="border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.2);"
        ></iframe>
        """, height=700)
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════
    # ✅ INTERVIEW FLOW - Dynamic by Mode
    # ═══════════════════════════════════════════════════════════
    
    if st.session_state.interview_stage == 'not_started':
        # ✅ Dynamic interview structure display based on mode
        if interview_mode == "Practice Mode":
            structure_html = f"""
            <div class='question-card'>
                <h3>📋 Practice Interview Structure</h3>
                <p><strong>Round 1:</strong> Introduction ({intro_count} questions)</p>
                <p><strong>Round 2:</strong> Technical ({tech_count} questions)</p>
                <p><strong>Total:</strong> {total_count} questions</p>
                <p style='color: #60a5fa; margin-top: 16px;'>
                    ✨ Friendly practice simulation - Take your time and learn!
                </p>
            </div>
            """
        else:  # Strict Interview
            structure_html = f"""
            <div class='question-card'>
                <h3>📋 Professional Interview Structure</h3>
                <p><strong>Round 1:</strong> Introduction ({intro_count} questions)</p>
                <p><strong>Round 2:</strong> Technical ({tech_count} questions)</p>
                <p><strong>Total:</strong> {total_count} questions</p>
                <p style='color: #f59e0b; margin-top: 16px;'>
                    🎯 Real interview simulation - Professional evaluation
                </p>
            </div>
            """
        
        st.markdown(structure_html, unsafe_allow_html=True)
        
        # Start button
        if st.button("🚀 START INTERVIEW", use_container_width=True, type="primary"):
            st.session_state.interview_stage = 'intro'
            st.session_state.question_num = 1
            st.session_state.start_time = datetime.now()
            st.session_state.question_start_time = datetime.now()
            
            # ✅ Generate intro questions based on mode
            st.session_state.intro_questions = get_intro_questions(job_role, interview_mode)
            
            st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.rerun()
    
    elif st.session_state.interview_stage == 'intro':
        intro_qs = st.session_state.intro_questions
        
        if st.session_state.question_num <= len(intro_qs):
            q = intro_qs[st.session_state.question_num - 1]
            
            st.session_state.current_question_text = q['question']
            
            # Progress indicator
            st.subheader(f"Introduction - Question {st.session_state.question_num}/{len(intro_qs)}")
            
            # Live caption with question
            st.markdown(f"""
            <div class='caption-box'>
                <h4>🎤 AI Interviewer is asking:</h4>
                <p>{q['question']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Auto-speak question
            speak_question(q['question'], f"intro_{st.session_state.session_id}_{st.session_state.question_num}")
            
            # Replay button
            col_replay, col_spacer = st.columns([1, 5])
            with col_replay:
                if st.button("🔊 Replay", use_container_width=True):
                    speak_question(q['question'], f"intro_replay_{st.session_state.question_num}_{datetime.now().timestamp()}")
            
            # Answer input
            answer = st.text_area("Your Answer:", height=120, key=f"intro_{st.session_state.question_num}")
            
            # Submit button
            if st.button("📤 Submit Answer", use_container_width=True, type="primary"):
                if answer and len(answer.strip()) > 10:
                    answer_time = (datetime.now() - st.session_state.question_start_time).seconds if st.session_state.question_start_time else 0
                    
                    # Save to database
                    save_conversation(st.session_state.session_id, q['question'], answer, q['category'])
                    
                    st.session_state.conversation_history.append({"q": q['question'], "a": answer})
                    st.session_state.answers.append({
                        "q": q['question'], "a": answer, "category": q['category'],
                        "is_intro": True, "time_taken": answer_time
                    })
                    
                    st.session_state.question_num += 1
                    st.session_state.question_start_time = datetime.now()
                    
                    # Move to technical stage when intro complete
                    if st.session_state.question_num > len(intro_qs):
                        st.session_state.interview_stage = 'technical'
                        st.session_state.question_num = 1
                        
                        # ✅ Generate technical questions with dynamic count based on mode
                        tech_count = 3 if interview_mode == "Practice Mode" else 5
                        
                        with st.spinner("Generating personalized technical questions..."):
                            context = get_conversation_context(st.session_state.session_id)
                            st.session_state.technical_questions = generate_personalized_questions(
                                job_role, 
                                difficulty, 
                                st.session_state.resume_skills, 
                                context, 
                                num_questions=tech_count  # ✅ Dynamic based on mode
                            )
                        st.success(f"✅ Generated {tech_count} technical questions based on your background!")
                    
                    st.rerun()
                else:
                    st.warning("⚠️ Please provide a longer answer (at least 10 characters)")
    
    elif st.session_state.interview_stage == 'technical':
        questions = st.session_state.technical_questions
        
        if st.session_state.question_num <= len(questions):
            q = questions[st.session_state.question_num - 1]
            
            st.session_state.current_question_text = q['question']
            
            # Progress indicator
            st.subheader(f"Technical - Question {st.session_state.question_num}/{len(questions)}")
            
            # Live caption with question
            st.markdown(f"""
            <div class='caption-box'>
                <h4>🎤 AI Interviewer is asking:</h4>
                <p>{q['question']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Auto-speak question
            speak_question(q['question'], f"tech_{st.session_state.session_id}_{st.session_state.question_num}")
            
            # Replay button
            col_replay, col_spacer = st.columns([1, 5])
            with col_replay:
                if st.button("🔊 Replay", use_container_width=True):
                    speak_question(q['question'], f"tech_replay_{st.session_state.question_num}_{datetime.now().timestamp()}")
            
            # Question metadata
            st.markdown(f"""
            <p style='color: #94a3b8; font-size: 0.95rem; margin-top: 8px;'>
                <strong>Type:</strong> {q.get('type', 'conceptual').title()} | 
                <strong>Category:</strong> {q.get('category', 'General')}
            </p>
            """, unsafe_allow_html=True)
            
            # Answer input
            answer = st.text_area("Your Answer:", height=150, key=f"tech_{st.session_state.question_num}")
            
            # Submit controls
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("📤 Submit Answer", use_container_width=True, type="primary"):
                    if answer and len(answer.strip()) > 15:
                        answer_time = (datetime.now() - st.session_state.question_start_time).seconds if st.session_state.question_start_time else 0
                        
                        with st.spinner("Evaluating your answer..."):
                            result = evaluate_with_rubric(q['question'], answer, q['keywords'], q.get('type'))
                            
                            # Save to database
                            save_conversation(st.session_state.session_id, q['question'], answer, q['category'])
                            save_performance(
                                st.session_state.session_id, 
                                q['question'], 
                                answer, 
                                result['total_score'], 
                                result['rubric'], 
                                result['feedback'], 
                                answer_time
                            )
                            
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
                            
                            # Rubric breakdown
                            cols = st.columns(5)
                            r = result['rubric']
                            cols[0].metric("Correctness", f"{r['correctness']}/40")
                            cols[1].metric("Depth", f"{r['depth']}/25")
                            cols[2].metric("Clarity", f"{r['clarity']}/15")
                            cols[3].metric("Structure", f"{r['structure']}/10")
                            cols[4].metric("Real-world", f"{r['real_world']}/10")
                            
                            # Ideal answer outline
                            if result.get('ideal_answer_outline'):
                                st.markdown("**💡 Key Points to Cover:**")
                                st.markdown(
                                    "<div class='ideal-answer'>" + 
                                    "<br>".join([f"• {p}" for p in result['ideal_answer_outline']]) + 
                                    "</div>", 
                                    unsafe_allow_html=True
                                )
                            
                            # Professional rewrite
                            if result.get('rewritten_answer'):
                                st.markdown("**✨ Professional Version:**")
                                st.markdown(
                                    f"<div class='rewritten-answer'>{result['rewritten_answer']}</div>", 
                                    unsafe_allow_html=True
                                )
                            
                            st.session_state.question_num += 1
                            st.session_state.question_start_time = datetime.now()
                            
                            # Complete interview when all questions done
                            if st.session_state.question_num > len(questions):
                                st.session_state.interview_stage = 'complete'
                                avg = sum(st.session_state.scores) / len(st.session_state.scores)
                                save_session(
                                    st.session_state.session_id, 
                                    job_role, 
                                    difficulty, 
                                    interview_mode, 
                                    avg
                                )
                            
                            time.sleep(2)
                            st.rerun()
                    else:
                        st.warning("⚠️ Please provide a more detailed answer (at least 15 characters)")
            
            with col2:
                st.metric("Words", len(answer.split()) if answer else 0)
            
            # Progress bar
            st.progress(min((st.session_state.question_num - 1) / len(questions), 1.0))
    
    elif st.session_state.interview_stage == 'complete':
        st.success("🎉 Interview Complete!")
        st.info("📊 Go to the Results page for detailed feedback and your personalized improvement plan")
        
        # Summary stats
        if st.session_state.scores:
            avg = sum(st.session_state.scores) / len(st.session_state.scores)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Overall Score", f"{avg:.0f}%")
            with col2:
                st.metric("Questions Answered", len(st.session_state.scores))
            with col3:
                st.metric("Mode", interview_mode)

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
        
        st.markdown("---")
        
        if st.button("📈 Generate 7-Day Plan"):
            with st.spinner("Creating personalized plan..."):
                plan = generate_improvement_plan(st.session_state.session_id, job_role)
                
                if plan:
                    st.success("✅ Personalized 7-Day Improvement Plan")
                    for day_plan in plan:
                        with st.expander(f"📅 Day {day_plan['day']}: {day_plan['focus']}", expanded=(day_plan['day']==1)):
                            st.markdown(f"**🎯 Focus:** {day_plan['focus']}")
                            
                            st.markdown("**📝 Tasks:**")
                            for task in day_plan['tasks']:
                                st.markdown(f"✓ {task}")
                            
                            st.markdown("**📚 Resources:**")
                            for resource in day_plan['resources']:
                                st.markdown(f"• {resource}")
                else:
                    st.info("Complete an interview to generate a personalized plan.")

elif page == "📈 Progress":
    st.title("📈 Performance Dashboard")
    
    sessions = load_session_history()
    
    if not sessions:
        st.info("💡 Complete interviews to track your progress!")
    else:
        df = pd.DataFrame(sessions, columns=['ID', 'Role', 'Difficulty', 'Score', 'Date'])
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
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
        
        st.subheader("📈 Score Trend Over Time")
        chart_df = df[['Date', 'Score']].copy()
        chart_df = chart_df.set_index('Date')
        st.line_chart(chart_df, use_container_width=True, height=300)
        
        st.markdown("---")
        
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
                st.bar_chart(category_df.set_index('Category'), use_container_width=True, height=300)
        
        st.markdown("---")
        
        st.subheader("📋 Session History")
        
        display_df = df[['Date', 'Role', 'Difficulty', 'Score']].copy()
        display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d %H:%M')
        display_df['Score'] = display_df['Score'].apply(lambda x: f"{x:.0f}%")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("<div style='text-align:center;color:#888'><p>AI Interview Prep | SQLite Memory | Premium Features</p></div>", unsafe_allow_html=True)