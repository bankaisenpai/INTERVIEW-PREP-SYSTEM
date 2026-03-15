import unittest
from app import (
    extract_skills_deterministic,
    calculate_resume_score,
    normalize_resume_text,
    ROLE_SKILL_PRIORITIES,
    format_skills_for_ui,
    validate_score_stability,
)

class TestResumeATS(unittest.TestCase):
    def setUp(self):
        self.backend_text = """
        John Doe\n        Summary: Backend developer with 3 years of experience building REST APIs using FastAPI and Django.\n        Skills: Python, FastAPI, Django, SQLAlchemy, PostgreSQL, MySQL, Docker, GitHub Actions, API Testing, Git, Linux.\n        Projects: Built order management service with REST API, JWT authentication, and deployment using Docker + GitHub Actions.\n        Internship: Backend intern at Acme building microservices.\n        Education: BSc Computer Science.
        """

    def test_same_input_stable_score(self):
        role = 'Backend Developer'
        skills = extract_skills_deterministic(self.backend_text)
        score1 = calculate_resume_score(self.backend_text, skills, 3, role)
        score2 = calculate_resume_score(self.backend_text, skills, 3, role)
        self.assertEqual(score1, score2)
        stable, score_repeat = validate_score_stability(self.backend_text, role, repeats=5)
        self.assertTrue(stable)
        self.assertEqual(score1, score_repeat)

    def test_backend_keywords_detected(self):
        skills = extract_skills_deterministic(self.backend_text)
        flat = [s.lower() for cat in skills for s in skills[cat]]
        expected = ['fastapi', 'django', 'postgresql', 'mysql', 'docker', 'jwt', 'git', 'linux']
        for kw in expected:
            self.assertTrue(any(kw in s.lower() for s in flat), f"Missing expected keyword {kw}")

    def test_skill_formatting(self):
        skills = {'Backend': ['Python', 'Django'], 'DevOps': ['Docker', 'GitHub Actions']}
        out = format_skills_for_ui(skills)
        self.assertEqual(sorted(out, key=str.lower), sorted(['Python', 'Django', 'Docker', 'GitHub Actions'], key=str.lower))

    def test_missing_keywords_sorted(self):
        role = 'Backend Developer'
        normalized = normalize_resume_text('Python, Flask')
        required = ROLE_SKILL_PRIORITIES[role]['must']
        missing = sorted([k for k in required if k not in normalized])
        self.assertEqual(missing, sorted(missing))

    def test_no_duplicate_counting_skills(self):
        text = 'Python Python JavaScript SQL SQL'
        skills = extract_skills_deterministic(text)
        flat = [s.lower() for cat in skills for s in skills[cat]]
        self.assertEqual(flat.count('python'), 1)
        self.assertEqual(flat.count('sql'), 1)

if __name__ == '__main__':
    unittest.main()
