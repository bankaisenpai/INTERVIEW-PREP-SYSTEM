# api_extensions.py - ENHANCED VERSION
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime
import re
from dotenv import load_dotenv
import requests
import PyPDF2
import io

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

app = FastAPI(title="AI-Powered Interview Preparation System API", version="2.0.0")

# CORS - PRODUCTION: Tighten this to your specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: In production, use specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (use Redis/PostgreSQL in production)
interview_sessions: Dict[str, Dict[str, Any]] = {}

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

class InterviewResponse(BaseModel):
    """
    Unified response model for frontend consumption.
    
    Frontend should:
    - Display `interviewer_text` as the interviewer's speech
    - Show `next_question` in captions
    - Trigger talking animation while TTS plays interviewer_text
    - Display feedback metrics in real-time
    - Check `complete` flag to end interview
    """
    session_id: str
    interviewer_text: str
    next_question: Optional[str] = None
    complete: bool = False
    rubric_scores: Optional[Dict[str, int]] = None
    overall_score: Optional[int] = None
    feedback: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    star_analysis: Optional[Dict[str, Any]] = None

# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════
def load_questions() -> Dict:
    """Load question bank from questions.json"""
    try:
        with open('questions.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default questions if file not found
        return {
            "Data Scientist": {
                "Intermediate": [
                    {"question": "Explain the bias-variance tradeoff.", "category": "ML Theory"},
                    {"question": "How do you handle imbalanced datasets?", "category": "Data Prep"},
                    {"question": "What is cross-validation?", "category": "Model Eval"}
                ]
            }
        }

def load_rubrics() -> Dict:
    """Load scoring rubrics from rubrics.json"""
    try:
        with open('rubrics.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "Data Scientist": {
                "technical": 40,
                "communication": 30,
                "problem_solving": 30
            }
        }

def call_groq(prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> Optional[str]:
    """Call Groq API with error handling"""
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
        else:
            print(f"Groq API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Groq error: {e}")
        return None

# Filler words analysis
FILLER_WORDS = ['um', 'uh', 'like', 'you know', 'basically', 'actually', 'sort of', 'kind of']

def analyze_fillers(transcript: str) -> int:
    """Count filler words in transcript"""
    count = 0
    for filler in FILLER_WORDS:
        count += len(re.findall(r'\b' + filler + r'\b', transcript.lower()))
    return count

def estimate_wpm(transcript: str, duration_seconds: int = 30) -> int:
    """Estimate words per minute"""
    word_count = len(transcript.split())
    if duration_seconds > 0:
        return int((word_count / duration_seconds) * 60)
    return 0

def analyze_star(transcript: str) -> Dict[str, Any]:
    """Analyze answer using STAR method"""
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
        except Exception as e:
            print(f"STAR analysis error: {e}")
    
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

@app.post("/api/interview/start", response_model=InterviewResponse)
async def start_interview(req: StartInterviewRequest):
    """
    Initialize interview session.
    
    Frontend should:
    1. Call this endpoint when user clicks "Start Interview"
    2. Display interviewer_text as speech
    3. Trigger talking animation
    4. Show next_question in captions
    """
    try:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Load question bank
        questions = load_questions()
        role_questions = questions.get(req.role, {}).get(req.level, [])
        
        if not role_questions:
            raise HTTPException(
                status_code=400,
                detail=f"No questions found for role '{req.role}' at level '{req.level}'"
            )
        
        # Get first question
        first_q = role_questions[0]
        
        # Create session
        interview_sessions[session_id] = {
            "role": req.role,
            "level": req.level,
            "mode": req.mode,
            "questions": role_questions,
            "current_index": 0,
            "conversation": [],
            "started_at": datetime.now().isoformat(),
            "total_questions": len(role_questions)
        }
        
        interviewer_greeting = f"Hello! Welcome to your {req.role} interview at {req.level} level. Let's begin."
        
        return InterviewResponse(
            session_id=session_id,
            interviewer_text=f"{interviewer_greeting} {first_q['question']}",
            next_question=first_q['question'],
            complete=False,
            metrics={"total_questions": len(role_questions), "current_question": 1}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")

@app.post("/api/interview/respond", response_model=InterviewResponse)
async def respond_to_answer(req: RespondRequest):
    """
    Process user answer and generate next question.
    
    Frontend should:
    1. Call this after user submits answer (voice or text)
    2. Display feedback metrics in real-time
    3. Play interviewer_text with talking animation
    4. Show next_question in captions
    5. If complete=True, end interview and show results
    """
    try:
        session = interview_sessions.get(req.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Analyze user answer
        filler_count = analyze_fillers(req.user_transcript)
        wpm = estimate_wpm(req.user_transcript, 30)
        star = analyze_star(req.user_transcript)
        
        # Load rubric
        rubrics = load_rubrics()
        rubric = rubrics.get(session['role'], rubrics.get('Data Scientist', {}))
        
        # Get current question
        current_q = session['questions'][session['current_index']]
        
        # Score answer using AI
        score_prompt = f"""Score this interview answer using this rubric:
{json.dumps(rubric, indent=2)}

Question: {current_q['question']}
Answer: {req.user_transcript}

Return JSON with scores for each category (0-100) and overall score (0-100).
Example: {{"technical": 75, "communication": 80, "overall": 77}}"""

        score_response = call_groq(score_prompt, temperature=0.3)
        
        # Default scores
        scores = {"overall": 70, "technical": 70, "communication": 70}
        
        if score_response:
            try:
                match = re.search(r'\{.*\}', score_response, re.DOTALL)
                if match:
                    parsed_scores = json.loads(match.group())
                    scores.update(parsed_scores)
            except Exception as e:
                print(f"Score parsing error: {e}")
        
        # Save to conversation
        session['conversation'].append({
            "question": current_q['question'],
            "answer": req.user_transcript,
            "scores": scores,
            "star": star,
            "filler_count": filler_count,
            "wpm": wpm,
            "timestamp": datetime.now().isoformat()
        })
        
        # Move to next question
        session['current_index'] += 1
        
        # Check if interview complete
        if session['current_index'] >= len(session['questions']):
            # Interview complete
            avg_score = sum([c['scores']['overall'] for c in session['conversation']]) / len(session['conversation'])
            
            return InterviewResponse(
                session_id=req.session_id,
                interviewer_text="Thank you! That completes the interview. You did great!",
                complete=True,
                overall_score=int(avg_score),
                rubric_scores=scores,
                feedback={
                    "strengths": ["Clear communication"] if filler_count < 3 else [],
                    "improvements": ["Reduce filler words"] if filler_count >= 3 else [],
                    "filler_notes": f"Used {filler_count} filler words",
                    "clarity_notes": "Good pace" if 100 < wpm < 160 else "Adjust speaking pace"
                },
                metrics={
                    "total_answered": len(session['conversation']),
                    "average_score": int(avg_score),
                    "filler_count": filler_count,
                    "wpm": wpm
                },
                star_analysis=star
            )
        
        # Get next question
        next_q = session['questions'][session['current_index']]
        
        return InterviewResponse(
            session_id=req.session_id,
            interviewer_text=f"Good. Next question: {next_q['question']}",
            next_question=next_q['question'],
            complete=False,
            rubric_scores=scores,
            overall_score=scores.get('overall', 70),
            feedback={
                "strengths": ["Clear communication"] if filler_count < 3 else [],
                "improvements": ["Reduce filler words"] if filler_count >= 3 else [],
                "filler_notes": f"Used {filler_count} filler words",
                "clarity_notes": "Good pace" if 100 < wpm < 160 else "Speak at moderate pace"
            },
            metrics={
                "filler_count": filler_count,
                "wpm": wpm,
                "current_question": session['current_index'] + 1,
                "total_questions": session['total_questions']
            },
            star_analysis=star
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")

@app.get("/api/interview/session/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    session = interview_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.post("/api/resume/analyze")
async def analyze_resume(file: UploadFile = File(...), role: str = "Data Scientist"):
    """Analyze resume and provide improvements"""
    try:
        content = await file.read()
        
        # Parse resume
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
            except Exception as e:
                print(f"Resume analysis error: {e}")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze resume: {str(e)}")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "groq_key": "configured" if GROQ_API_KEY else "missing",
        "active_sessions": len(interview_sessions),
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)