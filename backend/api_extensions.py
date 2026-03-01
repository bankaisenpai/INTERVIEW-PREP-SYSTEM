# api_extensions.py
# ADD THIS FILE to your backend folder (same level as app_final_sqlite.py)
# Run with: uvicorn api_extensions:app --reload --port 8000

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import os
from datetime import datetime
import re
from dotenv import load_dotenv
import requests
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import PyPDF2
import io

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

app = FastAPI()

# CORS - allow your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (use Redis/SQLite in production)
interview_sessions = {}

# ═══════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════
class StartInterviewRequest(BaseModel):
    role: str
    level: str
    mode: str  # "practice" or "real"

class RespondRequest(BaseModel):
    session_id: str
    user_transcript: str

class STARAnalysis(BaseModel):
    situation: Optional[str]
    task: Optional[str]
    action: Optional[str]
    result: Optional[str]
    missing: List[str]
    improved_answer: str

# ═══════════════════════════════════════════════════════════
# LOAD QUESTION BANK & RUBRICS
# ═══════════════════════════════════════════════════════════
def load_questions():
    with open('questions.json', 'r') as f:
        return json.load(f)

def load_rubrics():
    with open('rubrics.json', 'r') as f:
        return json.load(f)

# ═══════════════════════════════════════════════════════════
# GROQ AI CALLS
# ═══════════════════════════════════════════════════════════
def call_groq(prompt: str, temperature=0.7, max_tokens=1000):
    if not GROQ_API_KEY:
        return None
    
    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            timeout=20
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except Exception as e:
        print(f"Groq error: {e}")
        return None

# ═══════════════════════════════════════════════════════════
# FILLER WORDS ANALYSIS
# ═══════════════════════════════════════════════════════════
FILLER_WORDS = ['um', 'uh', 'like', 'you know', 'basically', 'actually', 'sort of', 'kind of']

def analyze_fillers(transcript: str):
    count = 0
    for filler in FILLER_WORDS:
        count += len(re.findall(r'\b' + filler + r'\b', transcript.lower()))
    return count

def estimate_wpm(transcript: str, duration_seconds: int):
    word_count = len(transcript.split())
    if duration_seconds > 0:
        return int((word_count / duration_seconds) * 60)
    return 0

# ═══════════════════════════════════════════════════════════
# STAR ANALYSIS
# ═══════════════════════════════════════════════════════════
def analyze_star(transcript: str):
    prompt = f"""Analyze this interview answer using the STAR method (Situation, Task, Action, Result).

Answer: {transcript}

Extract:
- Situation: What was the context?
- Task: What needed to be done?
- Action: What did they do?
- Result: What was the outcome?

Return JSON:
{{
  "situation": "...",
  "task": "...",
  "action": "...",
  "result": "...",
  "missing": ["situation", "result"],
  "improved_answer": "Rewrite answer in STAR format..."
}}"""

    response = call_groq(prompt, temperature=0.3, max_tokens=800)
    if response:
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
    
    return {
        "situation": None,
        "task": None,
        "action": None,
        "result": None,
        "missing": ["situation", "task", "action", "result"],
        "improved_answer": "Could not analyze"
    }

# ═══════════════════════════════════════════════════════════
# INTERVIEW ENDPOINTS
# ═══════════════════════════════════════════════════════════
@app.post("/api/interview/start")
async def start_interview(req: StartInterviewRequest):
    """Initialize interview session"""
    
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Load question bank
    questions = load_questions()
    role_questions = questions.get(req.role, {}).get(req.level, [])
    
    if not role_questions:
        raise HTTPException(status_code=400, detail="No questions found for role/level")
    
    # Generate first question
    first_q = role_questions[0]
    
    # Create session
    interview_sessions[session_id] = {
        "role": req.role,
        "level": req.level,
        "mode": req.mode,
        "questions": role_questions,
        "current_index": 0,
        "conversation": [],
        "started_at": datetime.now().isoformat()
    }
    
    return {
        "session_id": session_id,
        "interviewer_text": f"Hello! Welcome to your {req.role} interview. {first_q['question']}",
        "next_question": first_q['question'],
        "mode": req.mode,
        "total_questions": len(role_questions)
    }

@app.post("/api/interview/respond")
async def respond_to_answer(req: RespondRequest):
    """Process user answer and generate next question"""
    
    session = interview_sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Analyze user answer
    filler_count = analyze_fillers(req.user_transcript)
    wpm = estimate_wpm(req.user_transcript, 30)  # Estimate 30s speaking time
    star = analyze_star(req.user_transcript)
    
    # Load rubric
    rubrics = load_rubrics()
    rubric = rubrics.get(session['role'], rubrics['Data Scientist'])
    
    # Score answer using AI
    current_q = session['questions'][session['current_index']]
    
    score_prompt = f"""Score this interview answer using this rubric:
{json.dumps(rubric, indent=2)}

Question: {current_q['question']}
Answer: {req.user_transcript}

Return JSON with scores for each category (0-100) and overall score."""

    score_response = call_groq(score_prompt, temperature=0.3)
    scores = {"overall": 70, "technical": 70, "communication": 70}  # Fallback
    
    if score_response:
        try:
            match = re.search(r'\{.*\}', score_response, re.DOTALL)
            if match:
                scores = json.loads(match.group())
        except:
            pass
    
    # Save to conversation
    session['conversation'].append({
        "question": current_q['question'],
        "answer": req.user_transcript,
        "scores": scores,
        "star": star,
        "filler_count": filler_count,
        "wpm": wpm
    })
    
    # Move to next question
    session['current_index'] += 1
    
    if session['current_index'] >= len(session['questions']):
        # Interview complete
        return {
            "session_id": req.session_id,
            "interviewer_text": "Thank you! That completes the interview.",
            "complete": True,
            "rubric_scores": scores,
            "star": star,
            "metrics": {"filler_count": filler_count, "wpm": wpm}
        }
    
    # Get next question
    next_q = session['questions'][session['current_index']]
    
    return {
        "session_id": req.session_id,
        "interviewer_text": f"Great. Next question: {next_q['question']}",
        "next_question": next_q['question'],
        "rubric_scores": scores,
        "overall_score": scores.get('overall', 70),
        "star": star,
        "feedback": {
            "strengths": ["Clear communication"] if filler_count < 3 else [],
            "improvements": ["Reduce filler words"] if filler_count >= 3 else [],
            "filler_notes": f"Used {filler_count} filler words",
            "clarity_notes": "Good" if wpm > 100 and wpm < 160 else "Speak at moderate pace"
        },
        "metrics": {
            "filler_count": filler_count,
            "wpm": wpm
        }
    }

# ═══════════════════════════════════════════════════════════
# PDF EXPORT
# ═══════════════════════════════════════════════════════════
@app.get("/api/interview/report/{session_id}")
async def generate_report(session_id: str):
    """Generate PDF report"""
    
    session = interview_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Create PDF
    filename = f"report_{session_id}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph(f"Interview Report - {session['role']}", styles['Title']))
    story.append(Spacer(1, 0.2*inch))
    
    # Summary
    avg_score = sum([c['scores'].get('overall', 0) for c in session['conversation']]) / len(session['conversation'])
    story.append(Paragraph(f"Overall Score: {avg_score:.0f}%", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    # Questions
    for i, conv in enumerate(session['conversation'], 1):
        story.append(Paragraph(f"Q{i}: {conv['question']}", styles['Heading3']))
        story.append(Paragraph(f"Answer: {conv['answer']}", styles['BodyText']))
        story.append(Paragraph(f"Score: {conv['scores'].get('overall', 0)}/100", styles['BodyText']))
        story.append(Spacer(1, 0.1*inch))
    
    doc.build(story)
    
    return {"filename": filename, "download_url": f"/download/{filename}"}

# ═══════════════════════════════════════════════════════════
# RESUME ANALYSIS
# ═══════════════════════════════════════════════════════════
@app.post("/api/resume/analyze")
async def analyze_resume(file: UploadFile = File(...), role: str = "Data Scientist"):
    """Analyze resume and provide improvements"""
    
    # Parse resume
    content = await file.read()
    
    if file.filename.endswith('.pdf'):
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = "\n".join([page.extract_text() for page in pdf_reader.pages])
    else:
        text = content.decode('utf-8')
    
    # AI analysis
    prompt = f"""Analyze this resume for a {role} position:

{text[:2000]}

Provide:
1. ATS-friendly rewrite suggestions
2. Missing skills for {role}
3. Bullet point improvements
4. Summary rewrite

Return JSON:
{{
  "ats_score": 75,
  "missing_skills": ["skill1", "skill2"],
  "bullet_improvements": [{{"original": "...", "improved": "..."}}],
  "summary_rewrite": "..."
}}"""

    response = call_groq(prompt, temperature=0.5, max_tokens=1500)
    
    result = {
        "ats_score": 70,
        "missing_skills": ["Python", "SQL"],
        "bullet_improvements": [],
        "summary_rewrite": "Could not generate"
    }
    
    if response:
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                result = json.loads(match.group())
        except:
            pass
    
    return result

@app.get("/health")
async def health():
    return {"status": "ok", "groq_key": "configured" if GROQ_API_KEY else "missing"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)