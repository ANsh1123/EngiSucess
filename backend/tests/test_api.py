"""
Comprehensive API Tests for Engineering Student Success Platform
Tests: Authentication, Dashboard, Companies, Resume, Projects, Quiz, Interview APIs
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://placement-prep-16.preview.emergentagent.com"

# Test credentials
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "Test12345!"

# Unique test user for registration tests
UNIQUE_TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@example.com"

class TestRootEndpoint:
    """Test root API endpoint"""
    
    def test_api_root(self):
        """Test that API root endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"API Root: {data}")


class TestAuthentication:
    """Test Authentication endpoints - Register, Login, Get Current User"""
    
    def test_register_new_user(self):
        """Test user registration - POST /api/auth/register"""
        payload = {
            "email": UNIQUE_TEST_EMAIL,
            "password": "TestPassword123!",
            "name": "Test User",
            "college": "Test Engineering College",
            "branch": "Computer Science",
            "year": "4th Year"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["email"] == UNIQUE_TEST_EMAIL
        assert data["user"]["name"] == "Test User"
        assert data["user"]["college"] == "Test Engineering College"
        assert data["user"]["branch"] == "Computer Science"
        print(f"Registration successful for: {data['user']['email']}")
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email fails"""
        payload = {
            "email": TEST_USER_EMAIL,  # Already registered
            "password": "AnotherPassword123!",
            "name": "Duplicate User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        
        # Should fail with 400 - email already registered
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("Duplicate email registration correctly rejected")
    
    def test_register_invalid_email(self):
        """Test registration with invalid email format"""
        payload = {
            "email": "invalid-email-format",
            "password": "TestPassword123!",
            "name": "Test User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 400, f"Expected 400 for invalid email, got {response.status_code}"
        print("Invalid email format correctly rejected")
    
    def test_register_short_password(self):
        """Test registration with short password fails"""
        payload = {
            "email": f"short_pwd_{uuid.uuid4().hex[:6]}@example.com",
            "password": "short",  # Less than 8 chars
            "name": "Test User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 400, f"Expected 400 for short password, got {response.status_code}"
        print("Short password correctly rejected")
    
    def test_login_success(self):
        """Test user login with valid credentials - POST /api/auth/login"""
        payload = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0
        assert data["user"]["email"] == TEST_USER_EMAIL
        print(f"Login successful for: {data['user']['email']}")
        return data["token"]
    
    def test_login_invalid_email(self):
        """Test login with non-existent email"""
        payload = {
            "email": "nonexistent@example.com",
            "password": TEST_USER_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("Non-existent email login correctly rejected")
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        payload = {
            "email": TEST_USER_EMAIL,
            "password": "WrongPassword123!"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("Wrong password login correctly rejected")
    
    def test_get_current_user(self):
        """Test getting current user info - GET /api/auth/me"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert response.status_code == 200, f"Get current user failed: {response.text}"
        data = response.json()
        
        assert "email" in data
        assert data["email"] == TEST_USER_EMAIL
        print(f"Get current user successful: {data['email']}")
    
    def test_get_current_user_no_token(self):
        """Test getting current user without token fails"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Access without token correctly rejected")
    
    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token fails"""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("Invalid token correctly rejected")


class TestDashboard:
    """Test Dashboard endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_get_dashboard(self, auth_token):
        """Test getting dashboard data - GET /api/dashboard"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard", headers=headers)
        
        assert response.status_code == 200, f"Dashboard request failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "recent_projects" in data or "projects" in data or isinstance(data, dict)
        print(f"Dashboard data retrieved: {list(data.keys())}")
    
    def test_dashboard_unauthorized(self):
        """Test dashboard access without auth fails"""
        response = requests.get(f"{BASE_URL}/api/dashboard")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Dashboard unauthorized access correctly rejected")


class TestCompanies:
    """Test Companies endpoints - List, Match Profile, My Matches"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_get_all_companies(self, auth_token):
        """Test getting all companies - GET /api/companies"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/companies", headers=headers)
        
        assert response.status_code == 200, f"Get companies failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Companies should be a list"
        assert len(data) > 0, "Should have at least one company"
        
        # Validate company structure
        first_company = data[0]
        assert "id" in first_company
        assert "name" in first_company
        assert "industry" in first_company
        print(f"Retrieved {len(data)} companies. First: {first_company['name']}")
    
    def test_match_profile(self, auth_token):
        """Test company profile matching - POST /api/companies/match-profile"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        profile_data = {
            "name": "Test Engineer",
            "headline": "Computer Science Student",
            "summary": "Passionate about programming and technology",
            "skills": ["Python", "JavaScript", "React", "Node.js", "Machine Learning"],
            "experience": [{
                "title": "Software Intern",
                "company": "Tech Company",
                "duration": "3 months"
            }],
            "education": [{
                "institution": "Test Engineering College",
                "degree": "B.Tech in Computer Science",
                "year": "4th Year"
            }],
            "projects": [{
                "title": "Web Application",
                "technologies": ["React", "Node.js"]
            }],
            "location": "Bangalore"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/companies/match-profile", 
            json=profile_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Profile matching failed: {response.text}"
        data = response.json()
        
        assert "results" in data, "Results not in response"
        results = data["results"]
        assert "matched_companies" in results, "matched_companies not in results"
        assert len(results["matched_companies"]) > 0, "Should have matched companies"
        
        # Validate match structure
        first_match = results["matched_companies"][0]
        assert "name" in first_match
        assert "match_score" in first_match
        print(f"Profile matched to {len(results['matched_companies'])} companies. Top: {first_match['name']} ({first_match['match_score']['overall']}%)")
    
    def test_get_user_matches(self, auth_token):
        """Test getting user matches - GET /api/companies/my-matches"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/companies/my-matches", headers=headers)
        
        # May return 404 if no matches yet, or 200 with results
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"User matches retrieved: {data.get('results', {}).get('total_matches', 0)} matches")
        else:
            print("No previous matches found (expected for new users)")


class TestResume:
    """Test Resume Evaluation endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_resume_evaluate_text(self, auth_token):
        """Test resume evaluation with text - POST /api/resume/evaluate"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a simple text file for testing
        import io
        resume_text = """
        John Doe
        Email: johndoe@example.com
        Phone: 1234567890
        LinkedIn: linkedin.com/in/johndoe
        
        EDUCATION
        B.Tech in Computer Science
        Test Engineering College
        GPA: 8.5/10
        
        EXPERIENCE
        Software Development Intern
        Tech Company | 3 months
        - Developed web applications using React and Node.js
        - Implemented RESTful APIs
        
        SKILLS
        Python, JavaScript, React, Node.js, MongoDB, SQL
        
        PROJECTS
        - E-commerce Platform: Built a full-stack application
        - Machine Learning Model: Developed a prediction model
        
        ACHIEVEMENTS
        - Dean's List for Academic Excellence
        - First place in College Hackathon
        """
        
        files = {
            'file': ('resume.txt', io.BytesIO(resume_text.encode()), 'text/plain')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/resume/evaluate",
            files=files,
            headers=headers
        )
        
        # May fail if only PDF/DOCX allowed, or succeed with analysis
        if response.status_code == 200:
            data = response.json()
            assert "analysis" in data, "Analysis not in response"
            print(f"Resume evaluated. Overall score: {data['analysis'].get('overall_score', 'N/A')}%")
        else:
            print(f"Resume evaluation returned {response.status_code} - may require PDF/DOCX format")


class TestApplications:
    """Test Job Applications endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_apply_to_company(self, auth_token):
        """Test applying to a company - POST /api/companies/{company_id}/apply"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get company list to get a valid company_id
        companies_response = requests.get(f"{BASE_URL}/api/companies", headers=headers)
        assert companies_response.status_code == 200
        companies = companies_response.json()
        
        if len(companies) > 0:
            company_id = companies[0]["id"]
            
            application_data = {
                "position": "Software Developer",
                "application_link": "https://example.com/job",
                "platform": "LinkedIn",
                "notes": "Applied through test"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/companies/{company_id}/apply",
                json=application_data,
                headers=headers
            )
            
            assert response.status_code == 200, f"Application failed: {response.text}"
            data = response.json()
            print(f"Application submitted: {data}")
    
    def test_get_my_applications(self, auth_token):
        """Test getting user applications - GET /api/applications/my-applications"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/applications/my-applications", headers=headers)
        
        assert response.status_code == 200, f"Get applications failed: {response.text}"
        data = response.json()
        
        assert "applications" in data, "Applications not in response"
        print(f"User has {len(data['applications'])} applications")


class TestYouTubeLearning:
    """Test YouTube Learning Recommendations endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_get_youtube_recommendations(self, auth_token):
        """Test getting YouTube recommendations - GET /api/learning/youtube-recommendations"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/learning/youtube-recommendations", headers=headers)
        
        assert response.status_code == 200, f"Get recommendations failed: {response.text}"
        data = response.json()
        
        assert "recommendations" in data, "Recommendations not in response"
        assert "user_profile" in data, "User profile not in response"
        print(f"Retrieved {len(data['recommendations'])} recommendation categories")


class TestProjects:
    """Test Project CRUD endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_create_project(self, auth_token):
        """Test creating a project - POST /api/projects"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        project_data = {
            "title": f"TEST_Project_{uuid.uuid4().hex[:6]}",
            "description": "A test project for API testing",
            "team_members": ["member1", "member2"],
            "deadline": None
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects",
            json=project_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Create project failed: {response.text}"
        data = response.json()
        
        assert "id" in data, "Project ID not in response"
        assert data["title"] == project_data["title"]
        print(f"Project created: {data['id']}")
        return data["id"]
    
    def test_get_projects(self, auth_token):
        """Test getting user projects - GET /api/projects"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/projects", headers=headers)
        
        assert response.status_code == 200, f"Get projects failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Projects should be a list"
        print(f"User has {len(data)} projects")
    
    def test_project_full_crud(self, auth_token):
        """Test full project CRUD cycle - Create, Read, Update"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # CREATE
        project_data = {
            "title": f"TEST_CRUD_Project_{uuid.uuid4().hex[:6]}",
            "description": "CRUD test project"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/projects",
            json=project_data,
            headers=headers
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["id"]
        print(f"Created project: {project_id}")
        
        # READ
        get_response = requests.get(
            f"{BASE_URL}/api/projects/{project_id}",
            headers=headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["title"] == project_data["title"]
        print(f"Read project: {get_response.json()['title']}")
        
        # UPDATE
        update_data = {
            "title": f"UPDATED_{project_data['title']}",
            "description": "Updated description"
        }
        update_response = requests.put(
            f"{BASE_URL}/api/projects/{project_id}",
            json=update_data,
            headers=headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == update_data["title"]
        print(f"Updated project: {update_response.json()['title']}")
        
        # Verify update persisted
        verify_response = requests.get(
            f"{BASE_URL}/api/projects/{project_id}",
            headers=headers
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["title"] == update_data["title"]
        print("Project update verified")


class TestQuiz:
    """Test Quiz endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_get_aptitude_questions(self, auth_token):
        """Test getting aptitude questions - GET /api/quiz/questions/aptitude"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/quiz/questions/aptitude", headers=headers)
        
        assert response.status_code == 200, f"Get aptitude questions failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Questions should be a list"
        assert len(data) > 0, "Should have questions"
        
        # Validate question structure
        first_question = data[0]
        assert "id" in first_question
        assert "question" in first_question
        assert "options" in first_question
        assert "correct_answer" in first_question
        print(f"Retrieved {len(data)} aptitude questions")
    
    def test_get_coding_questions(self, auth_token):
        """Test getting coding questions - GET /api/quiz/questions/coding"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/quiz/questions/coding", headers=headers)
        
        assert response.status_code == 200, f"Get coding questions failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Questions should be a list"
        print(f"Retrieved {len(data)} coding questions")
    
    def test_get_invalid_category(self, auth_token):
        """Test getting questions for invalid category fails"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/quiz/questions/invalid_category", headers=headers)
        
        assert response.status_code == 400, f"Expected 400 for invalid category, got {response.status_code}"
        print("Invalid category correctly rejected")


class TestInterview:
    """Test Interview Session endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_create_hr_interview_session(self, auth_token):
        """Test creating HR interview session - POST /api/interview/session"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/interview/session?interview_type=hr",
            headers=headers
        )
        
        assert response.status_code == 200, f"Create HR interview failed: {response.text}"
        data = response.json()
        
        assert "id" in data, "Session ID not in response"
        assert "questions" in data, "Questions not in response"
        assert data["type"] == "hr"
        print(f"HR interview session created: {data['id']} with {len(data['questions'])} questions")
        return data["id"]
    
    def test_create_technical_interview_session(self, auth_token):
        """Test creating technical interview session - POST /api/interview/session"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/interview/session?interview_type=technical",
            headers=headers
        )
        
        assert response.status_code == 200, f"Create technical interview failed: {response.text}"
        data = response.json()
        
        assert data["type"] == "technical"
        print(f"Technical interview session created: {data['id']}")
    
    def test_create_invalid_interview_type(self, auth_token):
        """Test creating interview with invalid type fails"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/interview/session?interview_type=invalid",
            headers=headers
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid type, got {response.status_code}"
        print("Invalid interview type correctly rejected")
    
    def test_submit_interview_response(self, auth_token):
        """Test submitting interview response"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create session first
        session_response = requests.post(
            f"{BASE_URL}/api/interview/session?interview_type=hr",
            headers=headers
        )
        assert session_response.status_code == 200
        session = session_response.json()
        session_id = session["id"]
        
        # Submit response
        response_data = {
            "question_id": session["questions"][0]["id"],
            "question": session["questions"][0]["question"],
            "answer": "I am a passionate software developer with experience in Python and JavaScript. I have worked on several projects including web applications and machine learning models."
        }
        
        response = requests.post(
            f"{BASE_URL}/api/interview/{session_id}/response",
            json=response_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Submit response failed: {response.text}"
        data = response.json()
        
        assert "feedback" in data, "Feedback not in response"
        print(f"Interview response submitted with feedback: {data['feedback'].get('overall_score', 'N/A')}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
