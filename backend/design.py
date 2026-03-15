"""
UI Design Components for AI Interview Prep System - COMPLETE PRODUCTION VERSION
✅ Login/Register pages with authentication
✅ Fixed Resume page (no raw data display)
✅ ALL existing interview/results/progress pages intact
✅ Clean, modern, minimal UI
✅ User-specific sessions
"""

import streamlit as st
import pandas as pd
import json
import sqlite3
from datetime import datetime
import time
import hashlib
import re

# ═══════════════════════════════════════════════════════════
# USER AUTHENTICATION SYSTEM
# ═══════════════════════════════════════════════════════════

def init_users_database():
    """Initialize users table in SQLite"""
    try:
        with sqlite3.connect('interview_memory.db') as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    except Exception as e:
        st.error(f"Database initialization error: {e}")

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, email: str, full_name: str, password: str) -> tuple:
    """Register a new user. Returns (success: bool, message: str)"""
    try:
        with sqlite3.connect('interview_memory.db') as conn:
            c = conn.cursor()
            password_hash = hash_password(password)
            c.execute('''
                INSERT INTO users (username, email, full_name, password_hash)
                VALUES (?, ?, ?, ?)
            ''', (username, email, full_name, password_hash))
            conn.commit()
            return True, "Registration successful!"
    except sqlite3.IntegrityError:
        return False, "Username or email already exists"
    except Exception as e:
        return False, f"Registration failed: {str(e)}"

def authenticate_user(username_or_email: str, password: str) -> tuple:
    """Authenticate user. Returns (success: bool, user_data: dict or None)"""
    try:
        with sqlite3.connect('interview_memory.db') as conn:
            c = conn.cursor()
            password_hash = hash_password(password)
            
            c.execute('''
                SELECT id, username, email, full_name 
                FROM users 
                WHERE (username = ? OR email = ?) AND password_hash = ?
            ''', (username_or_email, username_or_email, password_hash))
            
            user = c.fetchone()
            if user:
                return True, {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'full_name': user[3]
                }
            else:
                return False, None
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return False, None

def is_logged_in() -> bool:
    """Check if user is logged in"""
    return st.session_state.get('logged_in', False)

def get_current_user() -> dict:
    """Get current logged in user data"""
    return st.session_state.get('user', None)

def logout_user():
    """Logout current user"""
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.page = 'login'

# ═══════════════════════════════════════════════════════════
# AUTHENTICATION UI PAGES
# ═══════════════════════════════════════════════════════════

def render_login_page():
    """Render clean login page"""
    
    st.markdown("""
    <style>
    .main { background: #0f172a; }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h1 style='color: #667eea; font-size: 2.5rem; margin-bottom: 0.5rem;'>🎤 AI-Powered Interview Preparation System</h1>
            <p style='color: #94a3b8; font-size: 1rem;'>Sign in to your account</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            username_or_email = st.text_input(
                "Username or Email",
                placeholder="Enter your username or email",
                key="login_username"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("🚀 Login", type="primary", use_container_width=True):
                    if username_or_email and password:
                        success, user_data = authenticate_user(username_or_email, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user = user_data
                            st.session_state.page = 'home'
                            st.success("✅ Login successful!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials")
                    else:
                        st.warning("⚠️ Please fill in all fields")
            
            with col_btn2:
                if st.button("📝 Register", use_container_width=True):
                    st.session_state.page = 'register'
                    st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("""
            <div style='text-align: center; color: #64748b; font-size: 0.875rem; margin-top: 1.5rem;'>
                New user? Click Register to create an account
            </div>
            """, unsafe_allow_html=True)


def render_register_page():
    """Render clean register page"""
    
    st.markdown("""
    <style>
    .main { background: #0f172a; }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h1 style='color: #667eea; font-size: 2.5rem; margin-bottom: 0.5rem;'>🎤 AI-Powered Interview Preparation System</h1>
            <p style='color: #94a3b8; font-size: 1rem;'>Create your account</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            full_name = st.text_input(
                "Full Name",
                placeholder="John Doe",
                key="register_fullname"
            )
            
            email = st.text_input(
                "Email",
                placeholder="john@example.com",
                key="register_email"
            )
            
            username = st.text_input(
                "Username",
                placeholder="johndoe",
                key="register_username"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Minimum 6 characters",
                key="register_password"
            )
            
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter password",
                key="register_confirm_password"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("✅ Register", type="primary", use_container_width=True):
                    if not all([full_name, email, username, password, confirm_password]):
                        st.warning("⚠️ Please fill in all fields")
                    elif len(password) < 6:
                        st.warning("⚠️ Password must be at least 6 characters")
                    elif password != confirm_password:
                        st.error("❌ Passwords do not match")
                    elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                        st.warning("⚠️ Please enter a valid email")
                    else:
                        success, message = register_user(username, email, full_name, password)
                        if success:
                            st.success(f"✅ {message}")
                            st.info("Please login with your credentials")
                            time.sleep(1.5)
                            st.session_state.page = 'login'
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
            
            with col_btn2:
                if st.button("◀️ Back to Login", use_container_width=True):
                    st.session_state.page = 'login'
                    st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("""
            <div style='text-align: center; color: #64748b; font-size: 0.875rem; margin-top: 1.5rem;'>
                Already have an account? Click Back to Login
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# QUESTION BANK DATA
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
    "Backend Developer": ["api", "rest", "graphql", "database", "sql", "nosql", "server", "backend", "authentication", "authorization", "jwt", "microservices", "caching", "redis", "endpoint", "route", "middleware", "orm", "migration"],
    "Frontend Developer": ["react", "vue", "angular", "javascript", "typescript", "html", "css", "dom", "component", "hooks", "state", "props", "jsx", "frontend", "ui", "ux", "responsive", "browser", "webpack", "bundler"],
    "Data Scientist": ["machine learning", "ml", "model", "algorithm", "data", "statistics", "regression", "classification", "clustering", "training", "prediction", "feature", "dataset", "pandas", "numpy", "scikit", "tensorflow"],
    "ML Engineer": ["mlops", "deployment", "production", "inference", "serving", "pipeline", "docker", "kubernetes", "model", "monitoring", "drift", "retraining", "api", "batch", "real-time", "optimization", "scaling"],
    "Full Stack Developer": ["frontend", "backend", "fullstack", "api", "database", "react", "node", "express", "mongodb", "postgresql", "authentication", "deployment", "integration", "rest", "websocket"],
    "DevOps Engineer": ["ci/cd", "jenkins", "gitlab", "docker", "kubernetes", "terraform", "ansible", "monitoring", "prometheus", "grafana", "infrastructure", "deployment", "automation", "cloud", "aws", "azure", "pipeline"]
}

DEFAULT_QUESTIONS = {
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
    ],
    "Data Scientist": [
        {"question": "Explain the bias-variance tradeoff in machine learning.", "category": "ML Theory", "keywords": ["bias", "variance", "overfitting", "machine learning"], "type": "conceptual"},
        {"question": "How do you handle imbalanced datasets?", "category": "Data", "keywords": ["imbalanced", "sampling", "data", "classification"], "type": "practical"},
    ],
    "ML Engineer": [
        {"question": "How do you deploy a machine learning model to production?", "category": "Deployment", "keywords": ["deployment", "production", "model", "mlops"], "type": "practical"},
    ],
    "Full Stack Developer": [
        {"question": "How do you design a full-stack application architecture?", "category": "Architecture", "keywords": ["architecture", "fullstack", "design", "scalability"], "type": "practical"},
    ],
    "DevOps Engineer": [
        {"question": "How do you set up a CI/CD pipeline?", "category": "CI/CD", "keywords": ["CI/CD", "pipeline", "automation", "deployment"], "type": "practical"},
    ]
}

# ═══════════════════════════════════════════════════════════
# COMPLETE IMPROVEMENT PLAN DATA - KEEPING FROM YOUR FILE
# ═══════════════════════════════════════════════════════════

def get_improvement_plan_data():
    """Complete 7-day improvement plans for ALL combinations"""
    return {
        "correctness": {
            "Backend Developer": [
                {"day": 1, "focus": "API Design Fundamentals", "tasks": ["Review REST vs GraphQL differences", "Study HTTP methods and status codes", "Create API design checklist"], "resources": ["MDN Web Docs", "REST API Tutorial"]},
                {"day": 2, "focus": "Database Best Practices", "tasks": ["Learn indexing strategies", "Study SQL optimization techniques", "Practice query performance analysis"], "resources": ["Use The Index Luke", "PostgreSQL docs"]},
                {"day": 3, "focus": "Authentication & Security", "tasks": ["Deep dive into JWT structure", "Compare session vs token auth", "Review OWASP Top 10"], "resources": ["JWT.io", "OWASP Cheat Sheets"]},
                {"day": 4, "focus": "Microservices Patterns", "tasks": ["Study service communication patterns", "Learn about API gateways", "Review circuit breaker pattern"], "resources": ["Microservices.io", "Martin Fowler blog"]},
                {"day": 5, "focus": "Mock Interview Practice", "tasks": ["Record yourself answering 5 backend questions", "Review and identify knowledge gaps", "Create flashcards for weak areas"], "resources": ["Pramp", "Interviewing.io"]},
                {"day": 6, "focus": "System Design Basics", "tasks": ["Study load balancing concepts", "Learn about caching strategies", "Review database replication"], "resources": ["System Design Primer", "High Scalability blog"]},
                {"day": 7, "focus": "Final Review & Retake", "tasks": ["Retake interview on this platform", "Compare before/after scores", "Document key learnings"], "resources": ["This platform", "Personal notes"]}
            ],
            "Frontend Developer": [
                {"day": 1, "focus": "React Core Concepts", "tasks": ["Master component lifecycle", "Deep dive into hooks (useState, useEffect, useContext)", "Build mini app to practice"], "resources": ["React docs", "React Tutorial"]},
                {"day": 2, "focus": "State Management Mastery", "tasks": ["Compare Redux vs Context API", "Study Redux Toolkit", "Implement state management in sample project"], "resources": ["Redux docs", "egghead.io"]},
                {"day": 3, "focus": "Performance Optimization", "tasks": ["Learn React.memo and useMemo", "Study code splitting with React.lazy", "Practice lazy loading techniques"], "resources": ["web.dev", "React Performance docs"]},
                {"day": 4, "focus": "Modern JavaScript/TypeScript", "tasks": ["Review ES6+ features (arrow functions, destructuring, spread)", "Practice async/await patterns", "Study TypeScript basics"], "resources": ["MDN Web Docs", "TypeScript Handbook"]},
                {"day": 5, "focus": "Mock Interview Day", "tasks": ["Record 5 technical answers", "Review code examples you wrote", "Practice live coding challenges"], "resources": ["LeetCode Frontend", "CodeSandbox"]},
                {"day": 6, "focus": "Browser APIs & DOM", "tasks": ["Study DOM manipulation best practices", "Review event handling patterns", "Practice fetch/axios usage"], "resources": ["JavaScript.info", "MDN"]},
                {"day": 7, "focus": "Final Practice", "tasks": ["Retake interview", "Build small React project", "Review all notes"], "resources": ["This platform", "Frontend Mentor"]}
            ],
            "Data Scientist": [
                {"day": 1, "focus": "ML Algorithm Foundations", "tasks": ["Review bias-variance tradeoff in depth", "Study overfitting vs underfitting with examples", "Create algorithm comparison chart"], "resources": ["StatQuest YouTube", "Hands-On ML book"]},
                {"day": 2, "focus": "Algorithm Deep Dive", "tasks": ["Compare supervised vs unsupervised learning", "Explain 3 algorithms (decision tree, SVM, neural net) in detail", "Document use cases for each"], "resources": ["Scikit-learn docs", "ML Mastery"]},
                {"day": 3, "focus": "Model Evaluation Metrics", "tasks": ["Master precision, recall, F1-score calculations", "Understand ROC curves and AUC", "Practice metric selection for different problems"], "resources": ["Kaggle Learn", "Analytics Vidhya"]},
                {"day": 4, "focus": "Feature Engineering Techniques", "tasks": ["Study feature selection methods (RFE, feature importance)", "Practice encoding techniques (one-hot, label, target)", "Review dimensionality reduction (PCA, t-SNE)"], "resources": ["Feature Engineering book", "Towards Data Science"]},
                {"day": 5, "focus": "Mock Interview Practice", "tasks": ["Record yourself explaining 5 ML concepts", "Review and self-critique clarity", "Identify knowledge gaps"], "resources": ["Pramp", "Interviewing.io"]},
                {"day": 6, "focus": "Edge Cases & Trade-offs", "tasks": ["Study when algorithms fail", "Compare time/space complexity of algorithms", "Practice explaining trade-offs between models"], "resources": ["Big-O Cheat Sheet", "AlgoExpert"]},
                {"day": 7, "focus": "Comprehensive Review", "tasks": ["Retake interview on this platform", "Compare before/after rubric scores", "Create personal ML cheat sheet"], "resources": ["This platform", "Personal notes"]}
            ],
            "ML Engineer": [
                {"day": 1, "focus": "MLOps Fundamentals", "tasks": ["Study model versioning best practices", "Learn about experiment tracking tools", "Review deployment pipelines"], "resources": ["MLflow docs", "Weights & Biases"]},
                {"day": 2, "focus": "Production Model Serving", "tasks": ["Compare batch vs real-time inference", "Study model serving frameworks (TensorFlow Serving, TorchServe)", "Learn about API design for models"], "resources": ["TensorFlow docs", "FastAPI"]},
                {"day": 3, "focus": "Model Monitoring", "tasks": ["Study drift detection techniques", "Learn monitoring metrics and alerting", "Review retraining strategies"], "resources": ["Evidently AI", "Prometheus docs"]},
                {"day": 4, "focus": "Performance Optimization", "tasks": ["Study model quantization and pruning", "Learn about ONNX for model optimization", "Practice latency optimization techniques"], "resources": ["ONNX docs", "ML optimization guides"]},
                {"day": 5, "focus": "Mock Interview", "tasks": ["Practice explaining MLOps concepts", "Review deployment scenarios", "Prepare system design answers"], "resources": ["Pramp", "ML System Design"]},
                {"day": 6, "focus": "Containerization & Orchestration", "tasks": ["Deep dive into Docker for ML", "Study Kubernetes basics", "Review CI/CD for ML pipelines"], "resources": ["Docker docs", "Kubernetes tutorials"]},
                {"day": 7, "focus": "Final Review", "tasks": ["Retake interview", "Review all MLOps patterns", "Create deployment checklist"], "resources": ["This platform"]}
            ],
            "Full Stack Developer": [
                {"day": 1, "focus": "Frontend Architecture", "tasks": ["Study component design patterns", "Review state management options", "Learn about frontend performance"], "resources": ["React Patterns", "web.dev"]},
                {"day": 2, "focus": "Backend Architecture", "tasks": ["Review API design patterns", "Study database schema design", "Learn about microservices"], "resources": ["API guidelines", "Database design"]},
                {"day": 3, "focus": "Authentication & Authorization", "tasks": ["Master JWT implementation", "Study OAuth 2.0 flows", "Review session management"], "resources": ["Auth0 docs", "OAuth guide"]},
                {"day": 4, "focus": "Integration Testing", "tasks": ["Learn E2E testing strategies", "Study API testing with Postman", "Review integration patterns"], "resources": ["Testing guides", "Postman docs"]},
                {"day": 5, "focus": "Mock Interview", "tasks": ["Practice full-stack scenarios", "Review architecture decisions", "Explain tech stack choices"], "resources": ["System design interviews"]},
                {"day": 6, "focus": "Deployment & DevOps", "tasks": ["Study CI/CD pipelines", "Learn about containerization", "Review cloud deployment"], "resources": ["GitHub Actions", "Docker"]},
                {"day": 7, "focus": "Final Review", "tasks": ["Retake interview", "Build mini full-stack project", "Document learnings"], "resources": ["This platform"]}
            ],
            "DevOps Engineer": [
                {"day": 1, "focus": "Infrastructure as Code", "tasks": ["Master Terraform basics", "Study CloudFormation", "Practice IaC patterns"], "resources": ["Terraform docs", "IaC guides"]},
                {"day": 2, "focus": "CI/CD Pipeline Design", "tasks": ["Study Jenkins pipelines", "Learn GitHub Actions", "Review deployment strategies"], "resources": ["Jenkins docs", "GitHub Actions"]},
                {"day": 3, "focus": "Container Orchestration", "tasks": ["Deep dive into Kubernetes", "Study pod management", "Learn about service mesh"], "resources": ["Kubernetes docs", "K8s tutorials"]},
                {"day": 4, "focus": "Monitoring & Observability", "tasks": ["Study Prometheus and Grafana", "Learn about logging strategies", "Review alerting best practices"], "resources": ["Prometheus docs", "Observability guides"]},
                {"day": 5, "focus": "Mock Interview", "tasks": ["Practice explaining DevOps concepts", "Review incident response", "Prepare for scenario questions"], "resources": ["DevOps interviews"]},
                {"day": 6, "focus": "Security & Compliance", "tasks": ["Study security scanning tools", "Learn about secrets management", "Review compliance requirements"], "resources": ["Security guides", "Vault docs"]},
                {"day": 7, "focus": "Final Review", "tasks": ["Retake interview", "Create DevOps checklist", "Document automation ideas"], "resources": ["This platform"]}
            ]
        },
        "depth": {
            "Backend Developer": [
                {"day": 1, "focus": "Real-World API Examples", "tasks": ["Study 3 popular APIs (Stripe, Twilio, GitHub)", "Document their design patterns", "Note what makes them developer-friendly"], "resources": ["API documentation sites", "API design blogs"]},
                {"day": 2, "focus": "Database Case Studies", "tasks": ["Research how Netflix uses databases", "Study Uber's database architecture", "Learn from Pinterest's sharding strategy"], "resources": ["Engineering blogs", "High Scalability"]},
                {"day": 3, "focus": "Production Debugging", "tasks": ["Study common production issues", "Learn debugging tools (New Relic, Datadog)", "Practice root cause analysis"], "resources": ["Post-mortems", "Debugging guides"]},
                {"day": 4, "focus": "Scalability Patterns", "tasks": ["Deep dive into horizontal scaling", "Study load balancing strategies", "Learn about database replication"], "resources": ["System Design Primer", "Scalability talks"]},
                {"day": 5, "focus": "Security Deep Dive", "tasks": ["Study SQL injection prevention", "Learn about rate limiting implementations", "Review authentication vulnerabilities"], "resources": ["OWASP", "Security guides"]},
                {"day": 6, "focus": "Performance Optimization", "tasks": ["Study caching strategies (Redis patterns)", "Learn about connection pooling", "Review query optimization"], "resources": ["Redis docs", "Performance guides"]},
                {"day": 7, "focus": "Comprehensive Practice", "tasks": ["Retake interview with detailed examples", "Include 2+ real-world cases per answer", "Explain trade-offs in depth"], "resources": ["This platform"]}
            ],
            "Frontend Developer": [
                {"day": 1, "focus": "Real-World React Patterns", "tasks": ["Study Airbnb's React architecture", "Review Facebook's component structure", "Document reusable patterns"], "resources": ["React Patterns", "GitHub repos"]},
                {"day": 2, "focus": "Performance Deep Dive", "tasks": ["Study bundle size optimization techniques", "Learn about render optimization", "Practice with Chrome DevTools profiler"], "resources": ["Webpack Academy", "React DevTools"]},
                {"day": 3, "focus": "Accessibility in Practice", "tasks": ["Study WCAG 2.1 guidelines", "Practice keyboard navigation patterns", "Test with screen readers"], "resources": ["a11y project", "ARIA practices"]},
                {"day": 4, "focus": "Browser Rendering Internals", "tasks": ["Study how browsers render pages", "Learn about reflows and repaints", "Review critical render path"], "resources": ["web.dev", "Browser internals"]},
                {"day": 5, "focus": "Framework Comparisons", "tasks": ["Compare React, Vue, and Angular architectures", "List trade-offs for each", "Practice explaining framework choices"], "resources": ["State of JS", "Framework docs"]},
                {"day": 6, "focus": "Advanced Patterns", "tasks": ["Study HOCs vs Render Props vs Hooks", "Practice compound components", "Review design pattern implementations"], "resources": ["Patterns.dev", "Advanced React"]},
                {"day": 7, "focus": "Detailed Practice", "tasks": ["Retake interview", "Add specific examples to answers", "Explain implementation details"], "resources": ["This platform"]}
            ],
            "Data Scientist": [
                {"day": 1, "focus": "Industry ML Applications", "tasks": ["Study Netflix recommendation system", "Research Spotify's music recommendations", "Document Amazon's product recommendations"], "resources": ["Tech blogs", "ML case studies"]},
                {"day": 2, "focus": "Real Dataset Challenges", "tasks": ["Work with Kaggle datasets", "Practice data cleaning on real data", "Document common issues found"], "resources": ["Kaggle", "UCI ML Repository"]},
                {"day": 3, "focus": "Algorithm Failure Modes", "tasks": ["Study when linear regression fails", "Learn about neural network pitfalls", "Document edge cases for algorithms"], "resources": ["ML debugging guides", "Stack Overflow"]},
                {"day": 4, "focus": "Production ML Stories", "tasks": ["Read about ML in production failures", "Study successful ML deployments", "Learn from ML post-mortems"], "resources": ["ML Ops blog", "Papers with Code"]},
                {"day": 5, "focus": "Feature Engineering Examples", "tasks": ["Study winning Kaggle solutions", "Learn feature engineering tricks", "Practice on real datasets"], "resources": ["Kaggle winners", "Feature Tools"]},
                {"day": 6, "focus": "Model Interpretability", "tasks": ["Study SHAP and LIME", "Practice explaining model predictions", "Learn about model debugging"], "resources": ["Interpretable ML book", "SHAP docs"]},
                {"day": 7, "focus": "Comprehensive Practice", "tasks": ["Retake interview with examples", "Include real-world use cases", "Explain practical trade-offs"], "resources": ["This platform"]}
            ],
            "ML Engineer": [
                {"day": 1, "focus": "MLOps Case Studies", "tasks": ["Study Netflix's ML platform", "Research Uber's Michelangelo", "Document Airbnb's ML infrastructure"], "resources": ["Engineering blogs", "MLOps conferences"]},
                {"day": 2, "focus": "Production Issues", "tasks": ["Study model drift examples", "Learn about inference latency problems", "Review monitoring failures"], "resources": ["ML in production blog", "Post-mortems"]},
                {"day": 3, "focus": "Deployment Patterns", "tasks": ["Study canary deployments for ML", "Learn about shadow mode testing", "Review blue-green for models"], "resources": ["MLOps guides", "Deployment patterns"]},
                {"day": 4, "focus": "Performance Optimization", "tasks": ["Study model serving optimizations", "Learn about quantization examples", "Review batch inference patterns"], "resources": ["TensorFlow optimization", "ONNX"]},
                {"day": 5, "focus": "Scaling Strategies", "tasks": ["Study distributed training examples", "Learn about model parallelism", "Review data parallelism"], "resources": ["Distributed ML", "Horovod docs"]},
                {"day": 6, "focus": "Cost Optimization", "tasks": ["Study inference cost reduction", "Learn about auto-scaling patterns", "Review spot instance strategies"], "resources": ["Cloud cost guides", "ML at scale"]},
                {"day": 7, "focus": "Practical Review", "tasks": ["Retake interview with examples", "Include production scenarios", "Explain real challenges"], "resources": ["This platform"]}
            ],
            "Full Stack Developer": [
                {"day": 1, "focus": "Full-Stack Examples", "tasks": ["Study complete app architectures", "Review popular tech stacks", "Document integration patterns"], "resources": ["GitHub repos", "Architecture blogs"]},
                {"day": 2, "focus": "Integration Challenges", "tasks": ["Study common API integration issues", "Learn about CORS problems", "Review authentication flows"], "resources": ["Integration guides", "API docs"]},
                {"day": 3, "focus": "Performance Optimization", "tasks": ["Study full-stack performance", "Learn about caching strategies", "Review database optimization"], "resources": ["web.dev", "Performance guides"]},
                {"day": 4, "focus": "Deployment Stories", "tasks": ["Study deployment failures", "Learn about rollback strategies", "Review zero-downtime deploys"], "resources": ["DevOps blogs", "Deployment guides"]},
                {"day": 5, "focus": "Testing Strategies", "tasks": ["Study E2E testing examples", "Learn about integration testing", "Review testing pyramids"], "resources": ["Testing guides", "Cypress docs"]},
                {"day": 6, "focus": "Security Examples", "tasks": ["Study common vulnerabilities", "Learn about secure coding", "Review authentication issues"], "resources": ["OWASP", "Security guides"]},
                {"day": 7, "focus": "Complete Practice", "tasks": ["Retake interview with examples", "Include full-stack scenarios", "Explain design decisions"], "resources": ["This platform"]}
            ],
            "DevOps Engineer": [
                {"day": 1, "focus": "Infrastructure Examples", "tasks": ["Study large-scale infrastructures", "Review IaC implementations", "Document automation patterns"], "resources": ["Engineering blogs", "IaC examples"]},
                {"day": 2, "focus": "Incident Response", "tasks": ["Study real incident post-mortems", "Learn about debugging production", "Review alerting strategies"], "resources": ["Post-mortems", "SRE book"]},
                {"day": 3, "focus": "CI/CD Patterns", "tasks": ["Study enterprise CI/CD setups", "Learn about deployment strategies", "Review pipeline optimization"], "resources": ["CI/CD guides", "Pipeline examples"]},
                {"day": 4, "focus": "Monitoring Examples", "tasks": ["Study observability setups", "Learn about metric collection", "Review dashboard design"], "resources": ["Grafana examples", "Monitoring guides"]},
                {"day": 5, "focus": "Security Practices", "tasks": ["Study security scanning tools", "Learn about vulnerability management", "Review compliance patterns"], "resources": ["Security guides", "DevSecOps"]},
                {"day": 6, "focus": "Cost Optimization", "tasks": ["Study cloud cost reduction", "Learn about resource optimization", "Review auto-scaling patterns"], "resources": ["Cloud cost guides", "FinOps"]},
                {"day": 7, "focus": "Complete Practice", "tasks": ["Retake interview with examples", "Include production scenarios", "Explain trade-offs"], "resources": ["This platform"]}
            ]
        },
        "clarity": {
            "Backend Developer": [
                {"day": 1, "focus": "STAR Method Practice", "tasks": ["Structure 5 answers using STAR format", "Record yourself explaining backend concepts", "Get feedback from peers"], "resources": ["STAR method guide", "Mock interviews"]},
                {"day": 2, "focus": "Technical Explanation", "tasks": ["Explain REST APIs to non-technical person", "Use analogies for complex concepts", "Practice avoiding jargon"], "resources": ["Communication guides", "ELI5 Reddit"]},
                {"day": 3, "focus": "Logical Flow", "tasks": ["Outline answers before speaking", "Use transitions (First, Then, Finally)", "Practice sequencing ideas"], "resources": ["Presentation skills", "Toastmasters"]},
                {"day": 4, "focus": "Conciseness Training", "tasks": ["Answer in 90 seconds max", "Remove filler words", "Practice elevator pitches"], "resources": ["Public speaking", "Communication skills"]},
                {"day": 5, "focus": "Visual Communication", "tasks": ["Draw architecture diagrams", "Use whiteboard for explanations", "Practice visual thinking"], "resources": ["System design", "Diagram tools"]},
                {"day": 6, "focus": "Active Listening", "tasks": ["Rephrase questions before answering", "Ask clarifying questions", "Practice pausing to think"], "resources": ["Interview skills", "Active listening"]},
                {"day": 7, "focus": "Final Practice", "tasks": ["Retake interview with clear structure", "Focus on logical flow", "Review recorded answers"], "resources": ["This platform"]}
            ],
            "Frontend Developer": [
                {"day": 1, "focus": "Code Explanation", "tasks": ["Practice explaining code line-by-line", "Use clear variable names", "Add helpful comments"], "resources": ["Clean Code book", "Code review guides"]},
                {"day": 2, "focus": "Technical Communication", "tasks": ["Explain React concepts clearly", "Break down complex components", "Use diagrams to illustrate"], "resources": ["Technical writing", "Documentation guides"]},
                {"day": 3, "focus": "Problem-Solving Narration", "tasks": ["Think aloud while coding", "Explain your thought process", "Practice debugging narratives"], "resources": ["Coding interview patterns", "Pramp"]},
                {"day": 4, "focus": "Structured Answers", "tasks": ["Use Problem → Approach → Solution framework", "Practice organized responses", "Eliminate rambling"], "resources": ["STAR method", "Interview prep"]},
                {"day": 5, "focus": "Simplification Practice", "tasks": ["Explain complex concepts simply", "Remove unnecessary complexity", "Use everyday language"], "resources": ["ELI5", "Teaching resources"]},
                {"day": 6, "focus": "Q&A Practice", "tasks": ["Answer unexpected questions calmly", "Stay organized under pressure", "Ask for clarification when needed"], "resources": ["Mock interviews", "Interview.io"]},
                {"day": 7, "focus": "Final Review", "tasks": ["Retake interview", "Focus on clarity", "Review communication quality"], "resources": ["This platform"]}
            ],
            "Data Scientist": [
                {"day": 1, "focus": "STAR Method for ML", "tasks": ["Structure ML answers with Situation-Task-Action-Result", "Record 3 ML explanations", "Get feedback on clarity"], "resources": ["STAR guide", "Mock interviews"]},
                {"day": 2, "focus": "Simplifying ML Concepts", "tasks": ["Explain ML to non-technical people", "Use everyday analogies", "Avoid technical jargon"], "resources": ["ELI5", "Communication skills"]},
                {"day": 3, "focus": "Logical Answer Structure", "tasks": ["Outline before answering", "Use clear transitions", "Practice sequencing ideas"], "resources": ["Presentation skills", "Toastmasters"]},
                {"day": 4, "focus": "Concise Explanations", "tasks": ["Answer in 2 minutes max", "Remove filler words", "Practice elevator pitches for ML"], "resources": ["Public speaking", "ML communication"]},
                {"day": 5, "focus": "Visual ML Explanations", "tasks": ["Draw model architectures", "Sketch decision boundaries", "Use diagrams for processes"], "resources": ["ML visualization", "Diagram tools"]},
                {"day": 6, "focus": "Active Listening", "tasks": ["Rephrase ML questions", "Ask clarifying questions", "Practice pausing to think"], "resources": ["Interview skills", "Active listening"]},
                {"day": 7, "focus": "Clear Communication", "tasks": ["Retake interview", "Focus on clarity and structure", "Record and review answers"], "resources": ["This platform"]}
            ],
            "ML Engineer": [
                {"day": 1, "focus": "MLOps Communication", "tasks": ["Practice explaining MLOps clearly", "Use diagrams for pipelines", "Structure technical answers"], "resources": ["Communication guides", "MLOps talks"]},
                {"day": 2, "focus": "System Explanation", "tasks": ["Explain ML systems to stakeholders", "Use simple language", "Focus on business value"], "resources": ["Technical writing", "Stakeholder communication"]},
                {"day": 3, "focus": "Problem-Solution Clarity", "tasks": ["Structure answers as Problem→Solution", "Be concise and clear", "Use examples"], "resources": ["STAR method", "Communication skills"]},
                {"day": 4, "focus": "Technical Deep-Dives", "tasks": ["Explain complex systems simply", "Break down into components", "Use analogies"], "resources": ["System design", "Technical communication"]},
                {"day": 5, "focus": "Documentation Practice", "tasks": ["Write clear technical docs", "Practice explaining decisions", "Review with peers"], "resources": ["Documentation guides", "Writing resources"]},
                {"day": 6, "focus": "Presentation Skills", "tasks": ["Present ML systems", "Practice demos", "Get feedback on clarity"], "resources": ["Presentation guides", "Demo best practices"]},
                {"day": 7, "focus": "Final Communication", "tasks": ["Retake interview", "Focus on clear explanations", "Review communication"], "resources": ["This platform"]}
            ],
            "Full Stack Developer": [
                {"day": 1, "focus": "Architecture Communication", "tasks": ["Practice explaining full-stack architecture", "Use diagrams", "Structure answers clearly"], "resources": ["System design", "Communication guides"]},
                {"day": 2, "focus": "Technical Storytelling", "tasks": ["Tell stories about projects", "Use STAR method", "Practice with examples"], "resources": ["Storytelling guides", "STAR method"]},
                {"day": 3, "focus": "Code Walkthroughs", "tasks": ["Practice explaining code clearly", "Use clear naming", "Add helpful comments"], "resources": ["Clean Code", "Code review guides"]},
                {"day": 4, "focus": "Problem Explanation", "tasks": ["Explain technical problems clearly", "Break down complexity", "Use simple language"], "resources": ["Technical writing", "Communication skills"]},
                {"day": 5, "focus": "Design Decision Communication", "tasks": ["Explain tech stack choices", "Justify decisions clearly", "Use trade-off analysis"], "resources": ["Architecture guides", "Decision docs"]},
                {"day": 6, "focus": "Team Communication", "tasks": ["Practice stakeholder communication", "Explain to non-technical audience", "Focus on clarity"], "resources": ["Communication guides", "Presentation skills"]},
                {"day": 7, "focus": "Final Practice", "tasks": ["Retake interview", "Focus on clear structure", "Review communication"], "resources": ["This platform"]}
            ],
            "DevOps Engineer": [
                {"day": 1, "focus": "Infrastructure Communication", "tasks": ["Explain infrastructure clearly", "Use diagrams", "Structure technical answers"], "resources": ["System design", "Communication guides"]},
                {"day": 2, "focus": "Incident Explanation", "tasks": ["Practice explaining incidents", "Use clear timeline", "Focus on resolution steps"], "resources": ["Post-mortem guides", "Communication skills"]},
                {"day": 3, "focus": "Technical Documentation", "tasks": ["Write clear runbooks", "Practice explaining procedures", "Get feedback on clarity"], "resources": ["Documentation guides", "Writing resources"]},
                {"day": 4, "focus": "Stakeholder Communication", "tasks": ["Explain technical concepts to business", "Use simple language", "Focus on impact"], "resources": ["Stakeholder communication", "Business guides"]},
                {"day": 5, "focus": "Problem-Solution Structure", "tasks": ["Structure answers clearly", "Use Problem→Solution format", "Practice conciseness"], "resources": ["STAR method", "Communication skills"]},
                {"day": 6, "focus": "Diagram Communication", "tasks": ["Practice explaining with diagrams", "Use architecture drawings", "Visualize systems"], "resources": ["Diagram tools", "Visual communication"]},
                {"day": 7, "focus": "Final Communication", "tasks": ["Retake interview", "Focus on clarity", "Review explanations"], "resources": ["This platform"]}
            ]
        },
        "structure": {
            "Backend Developer": [
                {"day": 1, "focus": "Answer Framework Practice", "tasks": ["Learn and practice STAR method", "Structure 5 backend answers", "Create answer templates"], "resources": ["STAR guide", "Interview frameworks"]},
                {"day": 2, "focus": "Logical Flow Training", "tasks": ["Practice organizing thoughts before speaking", "Use bullet point outlines", "Sequence ideas logically"], "resources": ["Organization skills", "Mind mapping"]},
                {"day": 3, "focus": "Introduction-Body-Conclusion", "tasks": ["Structure answers with intro/body/conclusion", "Practice transitions", "Add clear summaries"], "resources": ["Presentation skills", "Communication guides"]},
                {"day": 4, "focus": "Technical Problem Structure", "tasks": ["Use Problem→Approach→Solution format", "Practice with coding problems", "Document thinking process"], "resources": ["Problem-solving guides", "Algorithms"]},
                {"day": 5, "focus": "Mock Interview Structure", "tasks": ["Record yourself answering", "Analyze answer structure", "Identify gaps in organization"], "resources": ["Pramp", "Mock interviews"]},
                {"day": 6, "focus": "Comparison Frameworks", "tasks": ["Structure comparison answers", "Use side-by-side format", "Practice trade-off analysis"], "resources": ["Decision frameworks", "Comparison guides"]},
                {"day": 7, "focus": "Final Structured Practice", "tasks": ["Retake interview with clear structure", "Use consistent format", "Review organization quality"], "resources": ["This platform"]}
            ],
            "Frontend Developer": [
                {"day": 1, "focus": "Component Explanation Structure", "tasks": ["Structure component explanations", "Use Props→State→Lifecycle format", "Practice with examples"], "resources": ["React docs", "Component guides"]},
                {"day": 2, "focus": "Problem-Solving Format", "tasks": ["Structure debugging explanations", "Use Error→Hypothesis→Solution format", "Practice with real bugs"], "resources": ["Debugging guides", "Problem-solving"]},
                {"day": 3, "focus": "Architecture Organization", "tasks": ["Structure architecture explanations", "Use layers approach", "Practice with diagrams"], "resources": ["Architecture guides", "System design"]},
                {"day": 4, "focus": "Code Review Structure", "tasks": ["Structure code explanations", "Use top-down approach", "Practice code walkthroughs"], "resources": ["Code review guides", "Clean Code"]},
                {"day": 5, "focus": "Mock Interview Organization", "tasks": ["Record structured answers", "Analyze organization", "Get feedback on structure"], "resources": ["Mock interviews", "Peer feedback"]},
                {"day": 6, "focus": "Performance Explanation Structure", "tasks": ["Structure performance discussions", "Use Measure→Analyze→Optimize format", "Practice with examples"], "resources": ["Performance guides", "Optimization"]},
                {"day": 7, "focus": "Final Organized Practice", "tasks": ["Retake interview", "Use consistent structure", "Review organization"], "resources": ["This platform"]}
            ],
            "Data Scientist": [
                {"day": 1, "focus": "ML Problem Structure", "tasks": ["Structure ML answers with Problem→Data→Model→Evaluation", "Practice with 5 ML questions", "Create answer templates"], "resources": ["ML interview guides", "Problem-solving"]},
                {"day": 2, "focus": "Algorithm Explanation Format", "tasks": ["Structure algorithm explanations", "Use Purpose→How it works→Use cases format", "Practice with 3 algorithms"], "resources": ["Algorithm guides", "ML resources"]},
                {"day": 3, "focus": "Data Analysis Structure", "tasks": ["Structure data analysis explanations", "Use EDA→Insights→Actions format", "Practice with datasets"], "resources": ["Data analysis guides", "EDA resources"]},
                {"day": 4, "focus": "Model Comparison Framework", "tasks": ["Structure comparison answers", "Use side-by-side metrics", "Practice trade-off analysis"], "resources": ["Model comparison", "Decision frameworks"]},
                {"day": 5, "focus": "Mock Interview Organization", "tasks": ["Record structured ML answers", "Analyze organization", "Identify improvements"], "resources": ["Mock interviews", "Peer review"]},
                {"day": 6, "focus": "Project Presentation Structure", "tasks": ["Structure project explanations", "Use Context→Challenge→Solution→Impact", "Practice with portfolio"], "resources": ["Project presentation", "Storytelling"]},
                {"day": 7, "focus": "Final Structured Practice", "tasks": ["Retake interview", "Use consistent ML structure", "Review organization"], "resources": ["This platform"]}
            ],
            "ML Engineer": [
                {"day": 1, "focus": "MLOps Pipeline Structure", "tasks": ["Structure pipeline explanations", "Use Data→Train→Deploy→Monitor format", "Practice with examples"], "resources": ["MLOps guides", "Pipeline docs"]},
                {"day": 2, "focus": "System Design Organization", "tasks": ["Structure ML system designs", "Use Requirements→Architecture→Trade-offs format", "Practice with scenarios"], "resources": ["System design", "ML architecture"]},
                {"day": 3, "focus": "Problem-Solution Framework", "tasks": ["Structure production problem answers", "Use Issue→Investigation→Solution format", "Practice with incidents"], "resources": ["Troubleshooting guides", "Problem-solving"]},
                {"day": 4, "focus": "Deployment Structure", "tasks": ["Structure deployment explanations", "Use Plan→Execute→Monitor format", "Practice with examples"], "resources": ["Deployment guides", "MLOps"]},
                {"day": 5, "focus": "Mock Interview Organization", "tasks": ["Record structured MLOps answers", "Analyze organization", "Get feedback"], "resources": ["Mock interviews", "Peer review"]},
                {"day": 6, "focus": "Monitoring Explanation Structure", "tasks": ["Structure monitoring discussions", "Use Metrics→Alerts→Actions format", "Practice with examples"], "resources": ["Monitoring guides", "Observability"]},
                {"day": 7, "focus": "Final Organized Practice", "tasks": ["Retake interview", "Use consistent structure", "Review organization"], "resources": ["This platform"]}
            ],
            "Full Stack Developer": [
                {"day": 1, "focus": "Full-Stack Structure", "tasks": ["Structure full-stack answers", "Use Frontend→Backend→Database format", "Practice with examples"], "resources": ["Full-stack guides", "Architecture"]},
                {"day": 2, "focus": "Feature Development Organization", "tasks": ["Structure feature explanations", "Use Requirements→Design→Implementation format", "Practice with projects"], "resources": ["Feature planning", "Development guides"]},
                {"day": 3, "focus": "API Design Structure", "tasks": ["Structure API explanations", "Use Endpoints→Request/Response→Error handling format", "Practice with examples"], "resources": ["API design", "REST guides"]},
                {"day": 4, "focus": "Debugging Framework", "tasks": ["Structure debugging explanations", "Use Reproduce→Isolate→Fix→Verify format", "Practice with bugs"], "resources": ["Debugging guides", "Problem-solving"]},
                {"day": 5, "focus": "Mock Interview Organization", "tasks": ["Record structured full-stack answers", "Analyze organization", "Get feedback"], "resources": ["Mock interviews", "Peer review"]},
                {"day": 6, "focus": "Architecture Explanation Structure", "tasks": ["Structure architecture discussions", "Use Components→Interactions→Trade-offs format", "Practice with examples"], "resources": ["Architecture guides", "System design"]},
                {"day": 7, "focus": "Final Structured Practice", "tasks": ["Retake interview", "Use consistent structure", "Review organization"], "resources": ["This platform"]}
            ],
            "DevOps Engineer": [
                {"day": 1, "focus": "Infrastructure Explanation Structure", "tasks": ["Structure infrastructure answers", "Use Components→Connections→Automation format", "Practice with examples"], "resources": ["Infrastructure guides", "IaC"]},
                {"day": 2, "focus": "CI/CD Pipeline Organization", "tasks": ["Structure pipeline explanations", "Use Stages→Actions→Outputs format", "Practice with examples"], "resources": ["CI/CD guides", "Pipeline docs"]},
                {"day": 3, "focus": "Incident Response Structure", "tasks": ["Structure incident answers", "Use Detect→Diagnose→Resolve→Prevent format", "Practice with scenarios"], "resources": ["Incident guides", "Post-mortems"]},
                {"day": 4, "focus": "Deployment Strategy Organization", "tasks": ["Structure deployment explanations", "Use Strategy→Steps→Rollback format", "Practice with examples"], "resources": ["Deployment guides", "DevOps"]},
                {"day": 5, "focus": "Mock Interview Organization", "tasks": ["Record structured DevOps answers", "Analyze organization", "Get feedback"], "resources": ["Mock interviews", "Peer review"]},
                {"day": 6, "focus": "Monitoring Explanation Structure", "tasks": ["Structure monitoring discussions", "Use Collect→Analyze→Alert format", "Practice with examples"], "resources": ["Monitoring guides", "Observability"]},
                {"day": 7, "focus": "Final Structured Practice", "tasks": ["Retake interview", "Use consistent structure", "Review organization"], "resources": ["This platform"]}
            ]
        },
        "real_world": {
            "Backend Developer": [
                {"day": 1, "focus": "Production System Examples", "tasks": ["Study real production architectures", "Document 3 real-world systems", "Note practical trade-offs"], "resources": ["Engineering blogs", "Case studies"]},
                {"day": 2, "focus": "Scalability Scenarios", "tasks": ["Research how companies scale", "Study Netflix, Uber, Airbnb architectures", "Document scaling patterns"], "resources": ["High Scalability blog", "Engineering talks"]},
                {"day": 3, "focus": "Real Bug Stories", "tasks": ["Study production incidents", "Learn from post-mortems", "Document debugging approaches"], "resources": ["Post-mortem collection", "Incident reports"]},
                {"day": 4, "focus": "API Design Examples", "tasks": ["Study popular APIs (Stripe, Twilio)", "Document design patterns", "Note best practices"], "resources": ["API documentation", "Design blogs"]},
                {"day": 5, "focus": "Mock Interview with Examples", "tasks": ["Practice answering with real examples", "Include production scenarios", "Reference actual systems"], "resources": ["Mock interviews", "System design"]},
                {"day": 6, "focus": "Performance Case Studies", "tasks": ["Study performance optimizations", "Learn from real bottlenecks", "Document solutions"], "resources": ["Performance blogs", "Optimization talks"]},
                {"day": 7, "focus": "Final Practice with Context", "tasks": ["Retake interview", "Include real-world examples", "Reference production systems"], "resources": ["This platform"]}
            ],
            "Frontend Developer": [
                {"day": 1, "focus": "Real App Architectures", "tasks": ["Study production React apps", "Document architecture patterns", "Note design decisions"], "resources": ["Open source projects", "Architecture blogs"]},
                {"day": 2, "focus": "Performance Stories", "tasks": ["Study real performance fixes", "Learn from optimization case studies", "Document techniques"], "resources": ["web.dev case studies", "Performance talks"]},
                {"day": 3, "focus": "Accessibility Examples", "tasks": ["Study accessible web apps", "Learn from real implementations", "Document patterns"], "resources": ["Accessibility examples", "A11y case studies"]},
                {"day": 4, "focus": "State Management Cases", "tasks": ["Study real Redux implementations", "Learn from production apps", "Document patterns"], "resources": ["GitHub repos", "Redux examples"]},
                {"day": 5, "focus": "Mock Interview with Examples", "tasks": ["Practice with real app references", "Include production scenarios", "Reference actual code"], "resources": ["Mock interviews", "Code reviews"]},
                {"day": 6, "focus": "Design Pattern Examples", "tasks": ["Study real component patterns", "Learn from popular libraries", "Document approaches"], "resources": ["React patterns", "Component libraries"]},
                {"day": 7, "focus": "Final Practice with Context", "tasks": ["Retake interview", "Include real examples", "Reference production apps"], "resources": ["This platform"]}
            ],
            "Data Scientist": [
                {"day": 1, "focus": "Industry ML Applications", "tasks": ["Study Netflix recommendations", "Research Spotify algorithms", "Document Amazon ML systems"], "resources": ["Tech blogs", "ML case studies"]},
                {"day": 2, "focus": "Real Dataset Challenges", "tasks": ["Work with Kaggle competition data", "Study winning solutions", "Document real problems"], "resources": ["Kaggle", "Competition write-ups"]},
                {"day": 3, "focus": "Production ML Stories", "tasks": ["Study ML deployment cases", "Learn from production issues", "Document lessons learned"], "resources": ["ML Ops blog", "Production ML"]},
                {"day": 4, "focus": "Feature Engineering Examples", "tasks": ["Study winning Kaggle features", "Learn engineering tricks", "Document techniques"], "resources": ["Kaggle winners", "Feature engineering"]},
                {"day": 5, "focus": "Mock Interview with Cases", "tasks": ["Practice with real examples", "Include production scenarios", "Reference actual systems"], "resources": ["Mock interviews", "Case studies"]},
                {"day": 6, "focus": "Model Deployment Examples", "tasks": ["Study real ML deployments", "Learn from production stories", "Document patterns"], "resources": ["MLOps", "Deployment cases"]},
                {"day": 7, "focus": "Final Practice with Context", "tasks": ["Retake interview", "Include real-world examples", "Reference production ML"], "resources": ["This platform"]}
            ],
            "ML Engineer": [
                {"day": 1, "focus": "MLOps Platform Examples", "tasks": ["Study Netflix ML platform", "Research Uber Michelangelo", "Document real systems"], "resources": ["Engineering blogs", "MLOps talks"]},
                {"day": 2, "focus": "Production Issues", "tasks": ["Study model drift cases", "Learn from production failures", "Document solutions"], "resources": ["ML production blog", "Post-mortems"]},
                {"day": 3, "focus": "Deployment Pattern Examples", "tasks": ["Study real ML deployments", "Learn canary deployment cases", "Document strategies"], "resources": ["MLOps guides", "Deployment cases"]},
                {"day": 4, "focus": "Scaling Stories", "tasks": ["Study distributed training examples", "Learn from scaling cases", "Document approaches"], "resources": ["Distributed ML", "Scaling blogs"]},
                {"day": 5, "focus": "Mock Interview with Examples", "tasks": ["Practice with real cases", "Include production scenarios", "Reference actual systems"], "resources": ["Mock interviews", "MLOps"]},
                {"day": 6, "focus": "Cost Optimization Cases", "tasks": ["Study cost reduction examples", "Learn from real optimizations", "Document strategies"], "resources": ["Cloud cost guides", "ML at scale"]},
                {"day": 7, "focus": "Final Practice with Context", "tasks": ["Retake interview", "Include real examples", "Reference production ML"], "resources": ["This platform"]}
            ],
            "Full Stack Developer": [
                {"day": 1, "focus": "Full-Stack App Examples", "tasks": ["Study production apps", "Document architecture patterns", "Note tech stack choices"], "resources": ["GitHub repos", "Architecture blogs"]},
                {"day": 2, "focus": "Integration Stories", "tasks": ["Study real integration challenges", "Learn from production issues", "Document solutions"], "resources": ["Integration guides", "Case studies"]},
                {"day": 3, "focus": "Deployment Examples", "tasks": ["Study real deployments", "Learn from deployment stories", "Document strategies"], "resources": ["DevOps blogs", "Deployment guides"]},
                {"day": 4, "focus": "Performance Cases", "tasks": ["Study full-stack optimizations", "Learn from performance fixes", "Document techniques"], "resources": ["Performance blogs", "Optimization talks"]},
                {"day": 5, "focus": "Mock Interview with Examples", "tasks": ["Practice with real cases", "Include production scenarios", "Reference actual apps"], "resources": ["Mock interviews", "System design"]},
                {"day": 6, "focus": "Security Examples", "tasks": ["Study security implementations", "Learn from vulnerability fixes", "Document patterns"], "resources": ["Security guides", "OWASP"]},
                {"day": 7, "focus": "Final Practice with Context", "tasks": ["Retake interview", "Include real examples", "Reference production systems"], "resources": ["This platform"]}
            ],
            "DevOps Engineer": [
                {"day": 1, "focus": "Infrastructure Examples", "tasks": ["Study large-scale infrastructures", "Document real IaC setups", "Note automation patterns"], "resources": ["Engineering blogs", "IaC examples"]},
                {"day": 2, "focus": "Incident Stories", "tasks": ["Study real incident responses", "Learn from post-mortems", "Document resolution approaches"], "resources": ["Post-mortems", "SRE book"]},
                {"day": 3, "focus": "CI/CD Examples", "tasks": ["Study enterprise pipelines", "Learn from real setups", "Document patterns"], "resources": ["CI/CD guides", "Pipeline examples"]},
                {"day": 4, "focus": "Monitoring Cases", "tasks": ["Study observability setups", "Learn from real implementations", "Document strategies"], "resources": ["Monitoring guides", "Observability"]},
                {"day": 5, "focus": "Mock Interview with Examples", "tasks": ["Practice with real cases", "Include production scenarios", "Reference actual systems"], "resources": ["Mock interviews", "DevOps"]},
                {"day": 6, "focus": "Cost Optimization Stories", "tasks": ["Study cloud cost reduction", "Learn from real optimizations", "Document approaches"], "resources": ["Cloud cost guides", "FinOps"]},
                {"day": 7, "focus": "Final Practice with Context", "tasks": ["Retake interview", "Include real examples", "Reference production systems"], "resources": ["This platform"]}
            ]
        }
    }

def generate_improvement_plan_with_mode(session_id, job_role, interview_mode):
    """Generate personalized 7-day plan"""
    from app import get_active_interview_config
    
    try:
        with sqlite3.connect('interview_memory.db') as conn:
            c = conn.cursor()
            c.execute('''SELECT rubric_scores FROM performance WHERE session_id = ?''', (session_id,))
            rubric_data = c.fetchall()
    except Exception:
        rubric_data = []
    
    if rubric_data:
        rubric_totals = {"correctness": 0, "depth": 0, "clarity": 0, "structure": 0, "real_world": 0}
        count = len(rubric_data)
        
        for rubric_json, in rubric_data:
            try:
                rubric = json.loads(rubric_json)
                for key in rubric_totals.keys():
                    rubric_totals[key] += rubric.get(key, 0)
            except Exception:
                pass
        
        max_scores = {"correctness": 40, "depth": 25, "clarity": 15, "structure": 10, "real_world": 10}
        rubric_avgs = {}
        for key in rubric_totals:
            avg_score = rubric_totals[key] / count if count > 0 else 0
            max_score = max_scores[key]
            rubric_avgs[key] = (avg_score / max_score) if max_score > 0 else 0
        
        sorted_rubrics = sorted(rubric_avgs.items(), key=lambda x: x[1])
        weakest = sorted_rubrics[0][0]
    else:
        weakest = "correctness"
    
    plans = get_improvement_plan_data()
    plan = plans.get(weakest, {}).get(job_role, None)
    
    if not plan:
        for category in ["correctness", "depth", "clarity", "structure", "real_world"]:
            if category in plans and job_role in plans[category]:
                plan = plans[category][job_role]
                break
    
    if not plan:
        plan = _create_smart_fallback_plan(job_role, weakest, interview_mode)
    
    if interview_mode == "Practice Mode":
        plan = _adjust_plan_tone_practice(plan, job_role, weakest)
    else:
        plan = _adjust_plan_tone_strict(plan, job_role, weakest)
    
    return plan

def _create_smart_fallback_plan(job_role, weakest_rubric, interview_mode):
    """Create intelligent fallback plan"""
    rubric_focus = {
        "correctness": "technical accuracy and core concepts",
        "depth": "detailed understanding and real-world examples",
        "clarity": "clear communication and explanation skills",
        "structure": "answer organization and logical flow",
        "real_world": "practical applications and production experience"
    }
    
    focus_area = rubric_focus.get(weakest_rubric, "overall interview skills")
    
    return [
        {"day": 1, "focus": f"Assess {focus_area.title()}", 
         "tasks": [
             f"Review your interview answers focusing on {focus_area}",
             f"Identify 3 specific areas within {weakest_rubric} that need work",
             "Create a personal improvement checklist"
         ], 
         "resources": ["Your interview recording", "Notes from feedback", "Self-assessment guides"]},
        {"day": 2, "focus": f"Learn Core {job_role} Skills", 
         "tasks": [
             f"Study 2-3 key {job_role} concepts you struggled with",
             "Watch tutorial videos or read documentation",
             "Take notes on key points and examples"
         ], 
         "resources": [f"{job_role} tutorials", "Official documentation", "Online courses"]},
        {"day": 3, "focus": "Practice with Examples", 
         "tasks": [
             f"Find 5 example questions for {job_role}",
             "Practice answering out loud or in writing",
             "Time yourself to build speed and confidence"
         ], 
         "resources": ["Interview question banks", "Practice platforms", "YouTube tutorials"]},
        {"day": 4, "focus": "Deep Dive Study Session", 
         "tasks": [
             f"Pick one complex {job_role} topic",
             "Study it thoroughly with multiple resources",
             "Create your own explanation in simple terms"
         ], 
         "resources": ["Technical blogs", "Books", "Video courses"]},
        {"day": 5, "focus": "Mock Interview Practice", 
         "tasks": [
             f"Do a full mock {job_role} interview",
             "Record yourself if possible",
             "Review your performance and note improvements needed"
         ], 
         "resources": ["Mock interview platforms", "Pramp", "Interviewing.io"]},
        {"day": 6, "focus": f"Strengthen {focus_area.title()}", 
         "tasks": [
             f"Focus specifically on improving {weakest_rubric}",
             "Practice techniques that address this weakness",
             "Get feedback from peers or mentors"
         ], 
         "resources": ["Peer review", "Mentorship", "Focused practice guides"]},
        {"day": 7, "focus": "Final Review and Retake", 
         "tasks": [
             "Review all your notes from the week",
             f"Retake the {job_role} interview on this platform",
             "Compare your new scores with previous attempt"
         ], 
         "resources": ["This platform", "Your weekly notes", "Progress tracker"]}
    ]

def _adjust_plan_tone_practice(plan, job_role, weakest):
    """Adjust plan tone for Practice Mode"""
    adjusted = []
    for day in plan:
        adjusted_day = day.copy()
        adjusted_day["focus"] = f"🎓 {day['focus']}"
        if day["day"] in [1, 4, 7]:
            adjusted_day["tasks"].append(f"💡 Remember: This is practice - focus on learning, not perfection!")
        adjusted.append(adjusted_day)
    return adjusted

def _adjust_plan_tone_strict(plan, job_role, weakest):
    """Adjust plan tone for Strict Interview"""
    adjusted = []
    for day in plan:
        adjusted_day = day.copy()
        adjusted_day["focus"] = f"⭐ {day['focus']}"
        if day["day"] in [1, 4, 7]:
            adjusted_day["tasks"].append(f"🎯 Track your progress: Measure improvement in {weakest} rubric scores")
        adjusted.append(adjusted_day)
    return adjusted

# ═══════════════════════════════════════════════════════════
# CSS STYLING
# ═══════════════════════════════════════════════════════════

def apply_custom_css():
    """Apply custom CSS styling"""
    st.markdown("""
    <style>
    .main-header { 
        font-size: 3rem; 
        font-weight: bold; 
        text-align: center; 
        color: #1E88E5; 
        margin-bottom: 2rem;
    }

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

    .score-card { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 24px; 
        border-radius: 12px; 
        color: white; 
        text-align: center;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    }
    
    .metric-card {
        background: linear-gradient(145deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(148, 163, 184, 0.1);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #60a5fa;
        margin: 8px 0;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .skill-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 6px 14px;
        margin: 4px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .missing-badge {
        display: inline-block;
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 6px 14px;
        margin: 4px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 500;
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
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 136, 229, 0.4);
    }

    iframe {
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        width: 100%;
        max-width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# PAGE RENDERING FUNCTIONS
# ═══════════════════════════════════════════════════════════

def render_home_page():
    """Render home page with user greeting"""
    from app import load_session_history
    
    user = get_current_user()
    sessions = load_session_history()
    
    st.markdown("<h1 class='main-header'>🎤 AI-Powered Interview Preparation System</h1>", unsafe_allow_html=True)
    if user:
        st.subheader(f"Welcome, {user['full_name']}!")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3, gap="large")

    total_sessions = len(sessions) if sessions else 0
    latest_score = f"{sessions[0][3]:.0f}%" if sessions else "N/A"
    improvement = f"{(sessions[0][3] - sessions[-1][3]):+.0f}%" if sessions and len(sessions) > 1 else "+0%"

    with col1:
        st.markdown("""
        <div class='feature-card'>
            <h3>💾 SQLite Memory</h3>
            <p style='margin-top:8px;'>Store your history across sessions</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;margin-top:14px;color:#9aa4b2;font-size:14px;'>Total Sessions</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center;font-size:32px;font-weight:600;color:#fff;margin-top:4px;'>{total_sessions}</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='feature-card'>
            <h3>🎯 Adaptive AI</h3>
            <p style='margin-top:8px;'>Personalized role-based questions</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;margin-top:14px;color:#9aa4b2;font-size:14px;'>Latest Score</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center;font-size:32px;font-weight:600;color:#fff;margin-top:4px;'>{latest_score}</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='feature-card'>
            <h3>📊 5-Factor Rubric</h3>
            <p style='margin-top:8px;'>Track strengths and improvement</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;margin-top:14px;color:#9aa4b2;font-size:14px;'>Improvement</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center;font-size:32px;font-weight:600;color:#fff;margin-top:4px;'>{improvement}</div>", unsafe_allow_html=True)



def render_resume_page(job_role):
    """FIXED: Clean Resume Analysis page - NO raw data display"""
    from app import (
        parse_resume,
        calculate_resume_score,
        generate_backend_recommendations,
        normalize_resume_text,
        _has_keyword,
        ROLE_SKILL_PRIORITIES
    )
    
    st.title("📄 Resume Analysis")
    st.caption("AI-powered ATS scoring and skill matching")
    
    st.markdown("---")
    
    col_upload, col_spacer = st.columns([3, 1])
    
    with col_upload:
        uploaded = st.file_uploader(
            "Upload Resume (PDF)", 
            type=['pdf'],
            help="Upload your resume in PDF format"
        )
        
        if uploaded:
            if st.button("🔍 Analyze Resume", type="primary"):
                with st.spinner("🤖 Analyzing resume..."):
                    text, skills, exp = parse_resume(uploaded)
                    st.session_state.resume_text = text
                    st.session_state.resume_skills = skills
                    st.session_state.resume_experience = exp
                    st.session_state.resume_score = calculate_resume_score(text, skills, exp, job_role)
                    st.balloons()
                    st.rerun()
    
    if st.session_state.resume_text:
        st.markdown("---")

        current_score = calculate_resume_score(
            st.session_state.resume_text,
            st.session_state.resume_skills,
            st.session_state.resume_experience,
            job_role
        )

        role_keywords = ROLE_SKILL_PRIORITIES.get(job_role, ROLE_SKILL_PRIORITIES['Backend Developer'])
        missing_keywords = sorted(
            [k for k in role_keywords.get('must', []) if not _has_keyword(normalize_resume_text(st.session_state.resume_text), k)]
        )

        # show main metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>ATS Score</div>
                <div class='metric-value'>{current_score}%</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            total_skills = sum(len(skills) for skills in st.session_state.resume_skills.values())
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>Skills Found</div>
                <div class='metric-value'>{total_skills}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            exp_text = f"{st.session_state.resume_experience}" if st.session_state.resume_experience > 0 else "N/A"
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>Experience</div>
                <div class='metric-value'>{exp_text} yrs</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            status = "Excellent" if current_score >= 80 else "Good" if current_score >= 60 else "Needs Improvement"
            status_color = "#10b981" if current_score >= 80 else "#f59e0b" if current_score >= 60 else "#ef4444"
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>Status</div>
                <div class='metric-value' style='color: {status_color};'>{status}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        if st.session_state.resume_skills:
            st.subheader("🛠️ Technical Skills")
            aggregate = []
            for category in sorted(st.session_state.resume_skills):
                skills = sorted(st.session_state.resume_skills[category], key=lambda s: s.lower())
                aggregate.extend(skills)
                st.markdown(f"**{category}:**")
                badges_html = ""
                for skill in skills:
                    badges_html += f"<span class='skill-badge'>{skill}</span>"
                st.markdown(badges_html, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
            if not aggregate:
                st.info("💡 No technical skills detected. Add more keywords to your resume.")
        else:
            st.info("💡 No technical skills detected. Add more keywords to your resume.")

        st.markdown("---")
        st.subheader("🎯 Backend ATS Insights")

        st.markdown("**Missing Keywords (sorted):**")
        if missing_keywords:
            missing_html = "".join([f"<span class='missing-badge'>{kw.title()}</span>" for kw in missing_keywords])
            st.markdown(missing_html, unsafe_allow_html=True)
        else:
            st.success("✅ All must-have keywords for this role are present.")

        recommendations = generate_backend_recommendations(
            st.session_state.resume_text,
            st.session_state.resume_skills,
            job_role
        )
        st.markdown("**Recommendations:**")
        for rec in recommendations:
            st.write(f"• {rec}")

        st.markdown("---")

    else:
        st.info("👆 Upload your resume to get started")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Analysis includes:**")
            st.write("• ATS compatibility score")
            st.write("• Technical skills match")
            st.write("• Experience assessment")
        
        with col2:
            st.markdown("**You'll receive:**")
            st.write("• Score 0-100")
            st.write("• Skill breakdown")
            st.write("• Improvement tips")


def render_interview_page(job_role, difficulty, interview_mode):
    """Render interview page - keeping ALL your existing code"""
    from app import (
        INTERVIEW_MODE_CONFIG, FRONTEND_URL, get_active_interview_config,
        save_conversation, save_performance, save_session, get_conversation_context,
        get_intro_questions, generate_personalized_questions, evaluate_with_rubric,
        speak_question, reset_interview_state
    )
    
    # Session configuration
    if st.session_state.interview_stage != 'not_started':
        config = get_active_interview_config()
        active_role = config['job_role']
        active_difficulty = config['difficulty']
        active_mode = config['mode']
        mode_config = INTERVIEW_MODE_CONFIG.get(active_mode, INTERVIEW_MODE_CONFIG[interview_mode])
    else:
        active_role = job_role
        active_difficulty = difficulty
        active_mode = interview_mode
        mode_config = INTERVIEW_MODE_CONFIG.get(interview_mode, INTERVIEW_MODE_CONFIG['Practice Mode'])

    intro_count = mode_config.get("intro_count", 2)
    tech_count = mode_config.get("tech_count", 3)
    total_count = intro_count + tech_count

    if 'character_fullscreen' not in st.session_state:
        st.session_state.character_fullscreen = False

    # Header row
    st.markdown("## Interview Session")
    st.markdown("<br>", unsafe_allow_html=True)
    col_role, col_mode, col_timer, col_qnum = st.columns([2, 2, 1.2, 1.2], gap="medium")
    with col_role:
        st.markdown(f"**Role**: {active_role}")
    with col_mode:
        st.markdown(f"**Mode**: {active_mode}")
    with col_timer:
        if st.session_state.interview_stage != 'not_started':
            elapsed = (datetime.now() - st.session_state.start_time).seconds
            st.markdown(f"**Timer**: {elapsed//60:02d}:{elapsed%60:02d}")
        else:
            st.markdown("**Timer**: --:--")
    with col_qnum:
        qnum_label = st.session_state.question_num if st.session_state.question_num else 0
        st.markdown(f"**Question**: {qnum_label}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Avatar section
    st.markdown("<div style='text-align:center;padding:8px 0 8px 0;'>", unsafe_allow_html=True)
    st.markdown("<p style='margin:0;font-size:1rem;font-weight:600;'>🤖 AI Interviewer</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("⬆️ Expand AI Interviewer" if not st.session_state.character_fullscreen else "⬇️ Collapse AI Interviewer", key="toggle_interviewer_size"):
        st.session_state.character_fullscreen = not st.session_state.character_fullscreen

    # Embedding avatar frame
    iframe_height = 650 if st.session_state.character_fullscreen else 420
    try:
        st.components.v1.iframe(FRONTEND_URL, height=iframe_height, scrolling=False)
    except Exception:
        st.error("3D interviewer unavailable. Please check FRONTEND_URL")

    st.markdown("<br>", unsafe_allow_html=True)

    # Interview structure and start button
    if st.session_state.interview_stage == 'not_started':
        st.markdown("<div style='background:#0f172a;padding:14px;border-radius:12px;border:1px solid #1f2937;'>", unsafe_allow_html=True)
        st.markdown(f"**Total Questions**: {intro_count + tech_count}  •  **Intro**: {intro_count}  •  **Technical**: {tech_count}")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Start Interview", type="primary", use_container_width=True):
            st.session_state.active_job_role = job_role
            st.session_state.active_difficulty = difficulty
            st.session_state.active_interview_mode = interview_mode
            st.session_state.interview_stage = 'intro'
            st.session_state.question_num = 1
            st.session_state.start_time = datetime.now()
            st.session_state.question_start_time = datetime.now()
            st.session_state.intro_questions = get_intro_questions(job_role, interview_mode)
            st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.rerun()
    elif st.session_state.interview_stage == 'intro':
        _render_intro_questions(active_role, active_difficulty, tech_count, mode_config)
    elif st.session_state.interview_stage == 'technical':
        _render_technical_questions(mode_config)
    elif st.session_state.interview_stage == 'complete':
        _render_completion_screen(active_mode)


def _render_interview_structure(mode_config, intro_count, tech_count, total_count, job_role, difficulty, interview_mode):
    """Helper to render interview structure"""
    from app import get_intro_questions, get_conversation_context, generate_personalized_questions
    
    st.subheader("📋 Interview Summary")
    with st.container():
        st.markdown("<div style='background:#0b1320;padding:0.75rem;border-radius:12px;border:1px solid #1f2937;'>", unsafe_allow_html=True)
        st.write(f"**Mode:** {interview_mode} | **Total:** {total_count} questions")
        st.write(f"• Introduction: {intro_count} | • Technical: {tech_count}")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.button("🚀 Start Interview", key="start_btn", type="primary", use_container_width=True):
        st.session_state.active_job_role = job_role
        st.session_state.active_difficulty = difficulty
        st.session_state.active_interview_mode = interview_mode
        
        st.session_state.interview_stage = 'intro'
        st.session_state.question_num = 1
        st.session_state.start_time = datetime.now()
        st.session_state.question_start_time = datetime.now()
        st.session_state.intro_questions = get_intro_questions(job_role, interview_mode)
        st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.rerun()


def _render_intro_questions(active_role, active_difficulty, tech_count, mode_config):
    """Helper to render intro questions"""
    from app import save_conversation, get_conversation_context, generate_personalized_questions, speak_question

    intro_qs = st.session_state.intro_questions
    if st.session_state.question_num <= len(intro_qs):
        q = intro_qs[st.session_state.question_num - 1]
        st.session_state.current_question_text = q['question']

        st.markdown(f"### Question {st.session_state.question_num}")
        st.markdown(f"**{q['question']}**")
        speak_question(q['question'], f"intro_{st.session_state.session_id}_{st.session_state.question_num}")

        answer = st.text_area(
            "",
            height=140,
            key=f"intro_{st.session_state.question_num}",
            placeholder="Type your answer...",
            label_visibility="collapsed"
        )

        btn_col1, btn_col2 = st.columns([1, 1], gap="small")
        with btn_col1:
            if st.button("Submit Answer", key="submit_intro", use_container_width=True):
                if answer and len(answer.strip()) > 10:
                    answer_time = (datetime.now() - st.session_state.question_start_time).seconds if st.session_state.question_start_time else 0
                    save_conversation(st.session_state.session_id, q['question'], answer, q['category'])
                    st.session_state.answers.append({"q": q['question'], "a": answer, "category": q['category'], "is_intro": True, "time_taken": answer_time})
                    st.session_state.question_num += 1
                    st.session_state.question_start_time = datetime.now()
                    st.session_state.last_spoken_question_id = None
                    if st.session_state.question_num > len(intro_qs):
                        st.session_state.interview_stage = 'technical'
                        st.session_state.question_num = 1
                        with st.spinner("Generating technical questions..."):
                            context = get_conversation_context(st.session_state.session_id)
                            st.session_state.technical_questions = generate_personalized_questions(active_role, active_difficulty, st.session_state.resume_skills, context, num_questions=tech_count)
                        st.success(f"Generated {tech_count} technical questions")
                    st.rerun()
                else:
                    st.warning("Please write at least 10 characters")
        with btn_col2:
            if st.button("Repeat Question", key="repeat_intro", use_container_width=True):
                st.session_state.last_spoken_question_id = None
                speak_question(q['question'], f"replay_{datetime.now().timestamp()}")

        metrics_col1, metrics_col2 = st.columns(2)
        metrics_col1.markdown(f"**Words**: {len(answer.split()) if answer else 0}")
        metrics_col2.markdown(f"**Chars**: {len(answer) if answer else 0}")


def _render_technical_questions(mode_config):
    """Helper to render technical questions"""
    from app import save_conversation, save_performance, save_session, evaluate_with_rubric, speak_question, get_active_interview_config

    questions = st.session_state.technical_questions
    if st.session_state.question_num <= len(questions):
        q = questions[st.session_state.question_num - 1]
        st.session_state.current_question_text = q['question']

        st.markdown(f"### Question {st.session_state.question_num}")
        st.markdown(f"**{q['question']}**")
        speak_question(q['question'], f"tech_{st.session_state.session_id}_{st.session_state.question_num}")

        answer = st.text_area(
            "",
            height=170,
            key=f"tech_{st.session_state.question_num}",
            placeholder="Type your answer...",
            label_visibility="collapsed"
        )

        btn_col1, btn_col2 = st.columns([1, 1], gap="small")
        with btn_col1:
            if st.button("Submit Answer", key="submit_tech", use_container_width=True):
                if answer and len(answer.strip()) > 15:
                    answer_time = (datetime.now() - st.session_state.question_start_time).seconds if st.session_state.question_start_time else 0
                    with st.spinner("Evaluating..."):
                        result = evaluate_with_rubric(q['question'], answer, q['keywords'], q.get('type'))
                        save_conversation(st.session_state.session_id, q['question'], answer, q['category'])
                        save_performance(st.session_state.session_id, q['question'], answer, result['total_score'], result['rubric'], result['feedback'], answer_time)
                        st.session_state.answers.append({"q": q['question'], "a": answer, "category": q['category'], "score": result['total_score'], "rubric": result['rubric'], "feedback": result['feedback'], "time_taken": answer_time})
                        st.session_state.scores.append(result['total_score'])
                        st.session_state.rubric_scores.append(result['rubric'])
                        if mode_config.get("immediate_feedback", False):
                            _render_feedback_display(result)
                        st.session_state.question_num += 1
                        st.session_state.question_start_time = datetime.now()
                        st.session_state.last_spoken_question_id = None
                        if st.session_state.question_num > len(questions):
                            st.session_state.interview_stage = 'complete'
                            avg = sum(st.session_state.scores) / len(st.session_state.scores) if st.session_state.scores else 0
                            config = get_active_interview_config()
                            save_session(st.session_state.session_id, config['job_role'], config['difficulty'], config['mode'], avg)
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("Please write at least 15 characters")
        with btn_col2:
            if st.button("Repeat Question", key="repeat_tech", use_container_width=True):
                st.session_state.last_spoken_question_id = None
                speak_question(q['question'], f"replay_{datetime.now().timestamp()}")

        stats_c1, stats_c2 = st.columns(2)
        stats_c1.markdown(f"**Words**: {len(answer.split()) if answer else 0}")
        stats_c2.markdown(f"**Chars**: {len(answer) if answer else 0}")


def _render_feedback_display(result):
    """Helper to render feedback"""
    score_color = "🟢" if result['total_score'] >= 70 else "🟡" if result['total_score'] >= 50 else "🔴"
    
    st.success(f"{score_color} **Your Score: {result['total_score']}/100**")
    
    st.markdown("### 📊 Rubric Breakdown")
    cols = st.columns(5)
    r = result['rubric']
    
    rubric_items = [
        ("Correctness", r['correctness'], 40),
        ("Depth", r['depth'], 25),
        ("Clarity", r['clarity'], 15),
        ("Structure", r['structure'], 10),
        ("Real-world", r['real_world'], 10)
    ]
    
    for idx, (label, score, max_score) in enumerate(rubric_items):
        with cols[idx]:
            st.metric(label, f"{score}/{max_score}")
    
    if result.get('ideal_answer_outline'):
        st.markdown("### 💡 Key Points to Cover")
        st.markdown("<div class='ideal-answer'>" + "<br>".join([f"• {p}" for p in result['ideal_answer_outline']]) + "</div>", unsafe_allow_html=True)
    
    if result.get('rewritten_answer'):
        st.markdown("### ✨ Professional Version")
        st.markdown(f"<div class='rewritten-answer'>{result['rewritten_answer']}</div>", unsafe_allow_html=True)


def _render_completion_screen(active_mode):
    """Helper to render completion screen"""
    st.balloons()
    
    st.success("🎉 **Interview Complete!** Great job!")
    
    if st.session_state.scores:
        avg = sum(st.session_state.scores) / len(st.session_state.scores)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Overall Score", f"{avg:.0f}%")
        with col2:
            st.metric("Questions Answered", len(st.session_state.scores))
        with col3:
            st.metric("Mode", active_mode)
    
    st.info("📊 Navigate to the **Results** page for detailed feedback and your 7-day improvement plan!")


def render_results_page():
    """Render results page with FIXED improvement plan generation"""
    from app import get_active_interview_config
    
    st.title("📊 Performance Report")
    
    if not st.session_state.answers:
        st.warning("⚠️ No interview completed. Please complete an interview first.")
    else:
        tech = [a for a in st.session_state.answers if not a.get('is_intro')]
        avg = sum([a.get('score', 0) for a in tech]) / len(tech) if tech else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='score-card'><h2>{avg:.0f}%</h2><p>Overall Score</p></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='score-card'><h2>{len(tech)}</h2><p>Questions Answered</p></div>", unsafe_allow_html=True)
        with col3:
            avg_time = sum([a.get('time_taken', 0) for a in tech]) / len(tech) if tech else 0
            st.markdown(f"<div class='score-card'><h2>{avg_time:.0f}s</h2><p>Avg Time</p></div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.subheader("📝 Question-by-Question Breakdown")
        for i, ans in enumerate(tech, 1):
            score = ans.get('score', 0)
            with st.expander(f"Q{i}: {ans['q'][:60]}... | Score: {score}/100", expanded=False):
                st.markdown(f"**Question:** {ans['q']}")
                st.markdown(f"**Your Answer:** {ans['a']}")
                
                if ans.get('ideal_answer'):
                    st.markdown("**💡 Key Points:**")
                    for p in ans['ideal_answer']:
                        st.markdown(f"• {p}")
                
                if ans.get('strengths'):
                    st.markdown("**✅ Strengths:**")
                    for s in ans['strengths']:
                        st.markdown(f"• {s}")
                
                if ans.get('improvements'):
                    st.markdown("**⚠️ Areas for Improvement:**")
                    for imp in ans['improvements']:
                        st.markdown(f"• {imp}")
        
        st.markdown("---")
        
        config = get_active_interview_config()
        active_role = config['job_role'] if config['job_role'] else "Unknown Role"
        active_mode = config['mode'] if config['mode'] else "Practice Mode"
        
        if st.button("📈 Generate Personalized 7-Day Improvement Plan", type="primary"):
            with st.spinner("🤖 Analyzing your performance and creating personalized plan..."):
                plan = generate_improvement_plan_with_mode(
                    st.session_state.session_id, 
                    active_role,
                    active_mode
                )
                
                if plan:
                    mode_emoji = "🎓" if active_mode == "Practice Mode" else "⭐"
                    st.success(f"{mode_emoji} Personalized 7-Day Plan for {active_role} ({active_mode})")
                    
                    st.info(f"**Focus Area:** Based on your weakest rubric category, this plan targets your specific improvement needs.")
                    
                    for day_plan in plan:
                        day_num = day_plan['day']
                        
                        if day_num in [1, 7]:
                            border_color = "#667eea"
                        elif day_num in [2, 4, 6]:
                            border_color = "#10b981"
                        else:
                            border_color = "#3b82f6"
                        
                        with st.expander(
                            f"{day_plan['focus']}", 
                            expanded=(day_num == 1)
                        ):
                            st.markdown(f"#### 📅 Day {day_num}")
                            st.markdown(f"**🎯 Focus:** {day_plan['focus']}")
                            
                            st.markdown("**📝 Tasks:**")
                            for task in day_plan['tasks']:
                                st.markdown(f"✓ {task}")
                            
                            st.markdown("**📚 Resources:**")
                            for resource in day_plan['resources']:
                                st.markdown(f"• {resource}")
                            
                            if day_num < 7:
                                st.markdown(f"""
                                <div style='
                                    border-bottom: 2px solid {border_color};
                                    margin-top: 16px;
                                    opacity: 0.3;
                                '></div>
                                """, unsafe_allow_html=True)
                else:
                    st.error("❌ Could not generate improvement plan. Please try again or complete more interview questions.")


def render_progress_page():
    """Render progress dashboard"""
    from app import load_session_history
    
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
        st.line_chart(chart_df, height=300)
        
        st.markdown("---")
        
        st.subheader("📊 Performance by Category")
        
        try:
            with sqlite3.connect('interview_memory.db') as conn:
                c = conn.cursor()
                c.execute('''SELECT rubric_scores FROM performance''')
                all_rubrics = c.fetchall()
        except Exception:
            all_rubrics = []
        
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
                except Exception:
                    pass
            
            if count > 0:
                category_avgs = {k: v / count for k, v in category_totals.items()}
                category_df = pd.DataFrame(list(category_avgs.items()), columns=['Category', 'Score'])
                st.bar_chart(category_df.set_index('Category'), height=300)
        
        st.markdown("---")
        
        st.subheader("📋 Session History")
        
        display_df = df[['Date', 'Role', 'Difficulty', 'Score']].copy()
        display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d %H:%M')
        display_df['Score'] = display_df['Score'].apply(lambda x: f"{x:.0f}%")
        
        st.dataframe(display_df, hide_index=True)