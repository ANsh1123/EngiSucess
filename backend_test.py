#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Engineering Student Success Platform
Tests all backend endpoints with realistic data
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from frontend environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://placement-prep-16.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

print(f"Testing backend at: {API_BASE_URL}")

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.project_id = None
        self.task_id = None
        self.quiz_session_id = None
        self.interview_session_id = None
        
        # Test data for engineering student
        self.test_user = {
            "email": "rajesh.kumar@vit.ac.in",
            "password": "SecurePass123!",
            "name": "Rajesh Kumar",
            "college": "VIT University",
            "branch": "Computer Science Engineering",
            "year": "Final Year"
        }
        
        self.test_project = {
            "title": "Smart Campus Management System",
            "description": "A comprehensive web application for managing campus facilities, student services, and academic resources using MERN stack",
            "team_members": ["Priya Sharma", "Amit Singh", "Neha Gupta"],
            "deadline": (datetime.now() + timedelta(days=60)).isoformat()
        }
        
        self.test_task = {
            "title": "Implement User Authentication Module",
            "description": "Create JWT-based authentication system with role-based access control",
            "assigned_to": "Rajesh Kumar",
            "priority": "high",
            "due_date": (datetime.now() + timedelta(days=14)).isoformat()
        }

    def test_health_check(self):
        """Test basic API health"""
        print("\n=== Testing API Health Check ===")
        try:
            response = self.session.get(f"{API_BASE_URL}/")
            print(f"Health check status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")
                return True
            else:
                print(f"Health check failed: {response.text}")
                return False
        except Exception as e:
            print(f"Health check error: {str(e)}")
            return False

    def test_user_registration(self):
        """Test user registration"""
        print("\n=== Testing User Registration ===")
        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/register",
                json=self.test_user
            )
            print(f"Registration status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('token')
                self.user_data = data.get('user')
                print(f"Registration successful! User ID: {self.user_data.get('id')}")
                print(f"Token received: {self.auth_token[:20]}...")
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                print("User already exists, proceeding to login...")
                return self.test_user_login()
            else:
                print(f"Registration failed: {response.text}")
                return False
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return False

    def test_user_login(self):
        """Test user login"""
        print("\n=== Testing User Login ===")
        try:
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
            response = self.session.post(
                f"{API_BASE_URL}/auth/login",
                json=login_data
            )
            print(f"Login status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('token')
                self.user_data = data.get('user')
                print(f"Login successful! User: {self.user_data.get('name')}")
                print(f"Token received: {self.auth_token[:20]}...")
                return True
            else:
                print(f"Login failed: {response.text}")
                return False
        except Exception as e:
            print(f"Login error: {str(e)}")
            return False

    def test_protected_route(self):
        """Test JWT token validation on protected route"""
        print("\n=== Testing Protected Route (JWT Validation) ===")
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(
                f"{API_BASE_URL}/auth/me",
                headers=headers
            )
            print(f"Protected route status: {response.status_code}")
            
            if response.status_code == 200:
                user_info = response.json()
                print(f"Current user: {user_info.get('name')} ({user_info.get('email')})")
                return True
            else:
                print(f"Protected route failed: {response.text}")
                return False
        except Exception as e:
            print(f"Protected route error: {str(e)}")
            return False

    def test_create_project(self):
        """Test project creation"""
        print("\n=== Testing Project Creation ===")
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.post(
                f"{API_BASE_URL}/projects",
                json=self.test_project,
                headers=headers
            )
            print(f"Project creation status: {response.status_code}")
            
            if response.status_code == 200:
                project_data = response.json()
                self.project_id = project_data.get('id')
                print(f"Project created successfully! ID: {self.project_id}")
                print(f"Project title: {project_data.get('title')}")
                return True
            else:
                print(f"Project creation failed: {response.text}")
                return False
        except Exception as e:
            print(f"Project creation error: {str(e)}")
            return False

    def test_get_user_projects(self):
        """Test getting user projects"""
        print("\n=== Testing Get User Projects ===")
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(
                f"{API_BASE_URL}/projects",
                headers=headers
            )
            print(f"Get projects status: {response.status_code}")
            
            if response.status_code == 200:
                projects = response.json()
                print(f"Found {len(projects)} projects")
                for project in projects:
                    print(f"- {project.get('title')} (Status: {project.get('status')})")
                return True
            else:
                print(f"Get projects failed: {response.text}")
                return False
        except Exception as e:
            print(f"Get projects error: {str(e)}")
            return False

    def test_update_project(self):
        """Test project update"""
        print("\n=== Testing Project Update ===")
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            update_data = {
                "title": "Smart Campus Management System v2.0",
                "description": "Enhanced version with AI-powered features and mobile app integration",
                "team_members": self.test_project["team_members"] + ["Vikram Patel"]
            }
            response = self.session.put(
                f"{API_BASE_URL}/projects/{self.project_id}",
                json=update_data,
                headers=headers
            )
            print(f"Project update status: {response.status_code}")
            
            if response.status_code == 200:
                updated_project = response.json()
                print(f"Project updated successfully!")
                print(f"New title: {updated_project.get('title')}")
                print(f"Team size: {len(updated_project.get('team_members', []))}")
                return True
            else:
                print(f"Project update failed: {response.text}")
                return False
        except Exception as e:
            print(f"Project update error: {str(e)}")
            return False

    def test_create_task(self):
        """Test task creation within project"""
        print("\n=== Testing Task Creation ===")
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.post(
                f"{API_BASE_URL}/projects/{self.project_id}/tasks",
                json=self.test_task,
                headers=headers
            )
            print(f"Task creation status: {response.status_code}")
            
            if response.status_code == 200:
                task_data = response.json()
                self.task_id = task_data.get('id')
                print(f"Task created successfully! ID: {self.task_id}")
                print(f"Task title: {task_data.get('title')}")
                print(f"Priority: {task_data.get('priority')}")
                return True
            else:
                print(f"Task creation failed: {response.text}")
                return False
        except Exception as e:
            print(f"Task creation error: {str(e)}")
            return False

    def test_update_task_status(self):
        """Test task status updates (todo -> in_progress -> completed)"""
        print("\n=== Testing Task Status Updates ===")
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Update to in_progress
            response = self.session.put(
                f"{API_BASE_URL}/tasks/{self.task_id}",
                json={"status": "in_progress"},
                headers=headers
            )
            print(f"Task update to in_progress status: {response.status_code}")
            
            if response.status_code == 200:
                task_data = response.json()
                print(f"Task status updated to: {task_data.get('status')}")
                
                # Update to completed
                response = self.session.put(
                    f"{API_BASE_URL}/tasks/{self.task_id}",
                    json={"status": "completed"},
                    headers=headers
                )
                print(f"Task update to completed status: {response.status_code}")
                
                if response.status_code == 200:
                    task_data = response.json()
                    print(f"Task status updated to: {task_data.get('status')}")
                    return True
                else:
                    print(f"Task completion update failed: {response.text}")
                    return False
            else:
                print(f"Task progress update failed: {response.text}")
                return False
        except Exception as e:
            print(f"Task status update error: {str(e)}")
            return False

    def test_quiz_system(self):
        """Test quiz system functionality"""
        print("\n=== Testing Quiz System ===")
        try:
            # Test getting aptitude questions
            response = self.session.get(f"{API_BASE_URL}/quiz/questions/aptitude")
            print(f"Get aptitude questions status: {response.status_code}")
            
            if response.status_code == 200:
                questions = response.json()
                print(f"Found {len(questions)} aptitude questions")
                
                # Test getting coding questions
                response = self.session.get(f"{API_BASE_URL}/quiz/questions/coding")
                print(f"Get coding questions status: {response.status_code}")
                
                if response.status_code == 200:
                    coding_questions = response.json()
                    print(f"Found {len(coding_questions)} coding questions")
                    
                    # Create quiz session
                    headers = {"Authorization": f"Bearer {self.auth_token}"}
                    response = self.session.post(
                        f"{API_BASE_URL}/quiz/session?category=aptitude",
                        headers=headers
                    )
                    print(f"Create quiz session status: {response.status_code}")
                    
                    if response.status_code == 200:
                        session_data = response.json()
                        self.quiz_session_id = session_data.get('id')
                        print(f"Quiz session created! ID: {self.quiz_session_id}")
                        
                        # Submit a quiz answer
                        answer_data = {
                            "session_id": self.quiz_session_id,
                            "question_id": questions[0]["id"],
                            "selected_answer": questions[0]["correct_answer"],
                            "is_correct": True
                        }
                        response = self.session.post(
                            f"{API_BASE_URL}/quiz/answer",
                            json=answer_data,
                            headers=headers
                        )
                        print(f"Submit quiz answer status: {response.status_code}")
                        
                        if response.status_code == 200:
                            print("Quiz answer submitted successfully!")
                            return True
                        else:
                            print(f"Quiz answer submission failed: {response.text}")
                            return False
                    else:
                        print(f"Quiz session creation failed: {response.text}")
                        return False
                else:
                    print(f"Get coding questions failed: {response.text}")
                    return False
            else:
                print(f"Get aptitude questions failed: {response.text}")
                return False
        except Exception as e:
            print(f"Quiz system error: {str(e)}")
            return False

    def test_mock_interview_system(self):
        """Test mock interview system"""
        print("\n=== Testing Mock Interview System ===")
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create HR interview session
            response = self.session.post(
                f"{API_BASE_URL}/interview/session?interview_type=hr",
                headers=headers
            )
            print(f"Create HR interview session status: {response.status_code}")
            
            if response.status_code == 200:
                session_data = response.json()
                self.interview_session_id = session_data.get('id')
                print(f"HR interview session created! ID: {self.interview_session_id}")
                print(f"Questions count: {len(session_data.get('questions', []))}")
                
                # Submit interview response
                response_data = {
                    "question_id": session_data['questions'][0]['id'],
                    "response": "I am a final year Computer Science Engineering student at VIT University with strong programming skills in Python, Java, and JavaScript. I have experience in full-stack development and have worked on several projects including a smart campus management system. I am passionate about technology and eager to contribute to innovative solutions."
                }
                response = self.session.post(
                    f"{API_BASE_URL}/interview/{self.interview_session_id}/response",
                    json=response_data,
                    headers=headers
                )
                print(f"Submit interview response status: {response.status_code}")
                
                if response.status_code == 200:
                    print("Interview response submitted successfully!")
                    
                    # Test technical interview
                    response = self.session.post(
                        f"{API_BASE_URL}/interview/session?interview_type=technical",
                        headers=headers
                    )
                    print(f"Create technical interview session status: {response.status_code}")
                    
                    if response.status_code == 200:
                        tech_session = response.json()
                        print(f"Technical interview session created! Questions: {len(tech_session.get('questions', []))}")
                        return True
                    else:
                        print(f"Technical interview creation failed: {response.text}")
                        return False
                else:
                    print(f"Interview response submission failed: {response.text}")
                    return False
            else:
                print(f"HR interview session creation failed: {response.text}")
                return False
        except Exception as e:
            print(f"Mock interview system error: {str(e)}")
            return False

    def test_company_information(self):
        """Test company information API"""
        print("\n=== Testing Company Information ===")
        try:
            # Get all companies
            response = self.session.get(f"{API_BASE_URL}/companies")
            print(f"Get all companies status: {response.status_code}")
            
            if response.status_code == 200:
                companies = response.json()
                print(f"Found {len(companies)} companies")
                
                if companies:
                    company_id = companies[0]["id"]
                    print(f"Sample company: {companies[0]['name']} - {companies[0]['industry']}")
                    
                    # Get specific company details
                    response = self.session.get(f"{API_BASE_URL}/companies/{company_id}")
                    print(f"Get company details status: {response.status_code}")
                    
                    if response.status_code == 200:
                        company_details = response.json()
                        print(f"Company details: {company_details['name']}")
                        print(f"Salary range: {company_details['salary_range']}")
                        print(f"Locations: {', '.join(company_details['locations'])}")
                        return True
                    else:
                        print(f"Get company details failed: {response.text}")
                        return False
                else:
                    print("No companies found in database")
                    return False
            else:
                print(f"Get companies failed: {response.text}")
                return False
        except Exception as e:
            print(f"Company information error: {str(e)}")
            return False

    def test_dashboard(self):
        """Test dashboard data API"""
        print("\n=== Testing Dashboard ===")
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(
                f"{API_BASE_URL}/dashboard",
                headers=headers
            )
            print(f"Get dashboard data status: {response.status_code}")
            
            if response.status_code == 200:
                dashboard_data = response.json()
                print(f"Recent projects: {len(dashboard_data.get('recent_projects', []))}")
                print(f"Recent tasks: {len(dashboard_data.get('recent_tasks', []))}")
                quiz_stats = dashboard_data.get('quiz_stats', {})
                print(f"Quiz sessions: {quiz_stats.get('total_sessions', 0)}")
                print(f"Average score: {quiz_stats.get('average_score', 0):.2f}")
                return True
            else:
                print(f"Get dashboard data failed: {response.text}")
                return False
        except Exception as e:
            print(f"Dashboard error: {str(e)}")
            return False

    def test_profile_management(self):
        """Test profile management API"""
        print("\n=== Testing Profile Management ===")
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Update profile
            profile_update = {
                "college": "VIT University, Vellore",
                "branch": "Computer Science and Engineering",
                "year": "Final Year (2024)",
                "profile_picture": "https://example.com/profile.jpg"
            }
            response = self.session.put(
                f"{API_BASE_URL}/profile",
                json=profile_update,
                headers=headers
            )
            print(f"Update profile status: {response.status_code}")
            
            if response.status_code == 200:
                updated_profile = response.json()
                print(f"Profile updated successfully!")
                print(f"College: {updated_profile.get('college')}")
                print(f"Branch: {updated_profile.get('branch')}")
                
                # Test LinkedIn data import
                linkedin_data = {
                    "headline": "Computer Science Engineering Student | Full Stack Developer",
                    "summary": "Passionate about technology and innovation. Experienced in MERN stack development.",
                    "experience": [
                        {
                            "title": "Software Development Intern",
                            "company": "TechStart Solutions",
                            "duration": "Jun 2023 - Aug 2023"
                        }
                    ],
                    "skills": ["Python", "JavaScript", "React", "Node.js", "MongoDB", "Machine Learning"]
                }
                response = self.session.post(
                    f"{API_BASE_URL}/profile/linkedin",
                    json=linkedin_data,
                    headers=headers
                )
                print(f"LinkedIn import status: {response.status_code}")
                
                if response.status_code == 200:
                    print("LinkedIn data imported successfully!")
                    return True
                else:
                    print(f"LinkedIn import failed: {response.text}")
                    return False
            else:
                print(f"Profile update failed: {response.text}")
                return False
        except Exception as e:
            print(f"Profile management error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("ENGINEERING STUDENT SUCCESS PLATFORM - BACKEND API TESTS")
        print("=" * 60)
        
        test_results = {}
        
        # Test sequence based on priority
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("Protected Route (JWT)", self.test_protected_route),
            ("Project Creation", self.test_create_project),
            ("Get User Projects", self.test_get_user_projects),
            ("Project Update", self.test_update_project),
            ("Task Creation", self.test_create_task),
            ("Task Status Updates", self.test_update_task_status),
            ("Quiz System", self.test_quiz_system),
            ("Mock Interview System", self.test_mock_interview_system),
            ("Company Information", self.test_company_information),
            ("Dashboard", self.test_dashboard),
            ("Profile Management", self.test_profile_management)
        ]
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results[test_name] = result
            except Exception as e:
                print(f"Test {test_name} crashed: {str(e)}")
                test_results[test_name] = False
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<30} {status}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print(f"\nTotal Tests: {len(test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(test_results)*100):.1f}%")
        
        return test_results

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()