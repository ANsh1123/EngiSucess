from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
import re
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import json
import base64
from bson import ObjectId

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Engineering Student Success Platform API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-this')
JWT_ALGORITHM = "HS256"

# Helper functions
def prepare_for_mongo(data):
    """Prepare data for MongoDB storage"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, list):
                result[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, dict):
                result[key] = prepare_for_mongo(value)
            else:
                result[key] = value
        return result
    return data

def parse_from_mongo(item):
    """Parse data from MongoDB"""
    if isinstance(item, dict):
        result = {}
        for key, value in item.items():
            if key == '_id':
                continue  # Skip MongoDB's _id field
            elif isinstance(value, str) and 'T' in value and value.count('-') == 2:
                try:
                    result[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    result[key] = value
            elif isinstance(value, list):
                result[key] = [parse_from_mongo(item) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, dict):
                result[key] = parse_from_mongo(value)
            else:
                result[key] = value
        return result
    return item

def create_jwt_token(user_id: str) -> str:
    """Create JWT token for user authentication"""
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return parse_from_mongo(user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    college: str = ""
    branch: str = ""
    year: str = ""
    profile_picture: str = ""
    linkedin_data: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    college: str = ""
    branch: str = ""
    year: str = ""

class UserLogin(BaseModel):
    email: str
    password: str

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    user_id: str
    team_members: List[str] = []
    status: str = "active"  # active, completed, paused
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    progress: int = 0  # 0-100

class ProjectCreate(BaseModel):
    title: str
    description: str = ""
    team_members: List[str] = []
    deadline: Optional[datetime] = None

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    project_id: str
    assigned_to: str = ""
    status: str = "todo"  # todo, in_progress, completed
    priority: str = "medium"  # low, medium, high
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    assigned_to: str = ""
    priority: str = "medium"
    due_date: Optional[datetime] = None

class QuizSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    category: str  # aptitude, coding, technical
    score: int = 0
    total_questions: int = 0
    completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QuizAnswer(BaseModel):
    session_id: str
    question_id: str
    selected_answer: str
    is_correct: bool

class InterviewSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # hr, technical
    questions: List[Dict[str, Any]] = []
    responses: List[Dict[str, Any]] = []
    feedback: str = ""
    score: int = 0
    completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Sample data for questions
APTITUDE_QUESTIONS = [
    {
        "id": "apt_1",
        "question": "If a train travels at 60 km/hr and covers a distance in 2 hours, what is the distance?",
        "options": ["100 km", "120 km", "140 km", "160 km"],
        "correct_answer": "120 km",
        "category": "quantitative"
    },
    {
        "id": "apt_2", 
        "question": "What comes next in the series: 2, 4, 8, 16, ?",
        "options": ["24", "32", "30", "28"],
        "correct_answer": "32",
        "category": "logical"
    },
    {
        "id": "apt_3",
        "question": "Choose the synonym of 'Abundant':",
        "options": ["Scarce", "Plentiful", "Rare", "Limited"],
        "correct_answer": "Plentiful",
        "category": "verbal"
    }
]

CODING_QUESTIONS = [
    {
        "id": "code_1",
        "question": "Write a function to reverse a string in Python",
        "language": "python",
        "difficulty": "easy",
        "sample_answer": "def reverse_string(s):\n    return s[::-1]"
    },
    {
        "id": "code_2",
        "question": "Implement binary search algorithm",
        "language": "python",
        "difficulty": "medium",
        "sample_answer": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1"
    }
]

INTERVIEW_QUESTIONS = {
    "hr": [
        "Tell me about yourself",
        "What are your strengths and weaknesses?",
        "Why do you want to work here?",
        "Where do you see yourself in 5 years?",
        "Describe a challenging situation you faced and how you handled it"
    ],
    "technical": [
        "Explain the difference between stack and queue",
        "What is the time complexity of quicksort?",
        "Explain polymorphism in OOP",
        "What is a deadlock in operating systems?",
        "How does TCP differ from UDP?"
    ]
}

# Comprehensive Company Database for AI Matching
COMPANY_DATA = [
    {
        "id": "comp_1",
        "name": "TechCorp Solutions",
        "industry": "Software Development",
        "type": "Product Company",
        "size": "1000-5000",
        "salary_range": "₹6-15 LPA",
        "locations": ["Bangalore", "Hyderabad", "Pune"],
        "remote_friendly": True,
        "hiring_process": ["Online Test", "Technical Interview", "HR Interview"],
        "requirements": ["B.Tech/B.E in CS/IT", "Good programming skills", "Problem-solving ability"],
        "tech_stack": ["JavaScript", "React", "Node.js", "Python", "AWS", "MongoDB"],
        "culture": ["Innovation", "Work-life balance", "Learning", "Collaboration"],
        "benefits": ["Health Insurance", "Flexible Hours", "Learning Budget", "Stock Options"],
        "growth_opportunities": ["Tech Lead", "Senior Developer", "Architect", "Product Manager"],
        "company_values": ["Innovation", "Quality", "Customer Focus", "Team Spirit"],
        "work_environment": "Hybrid",
        "founded_year": 2015,
        "funding_stage": "Series B",
        "description": "Leading software development company building innovative solutions for global clients",
        "job_links": {
            "linkedin": "https://www.linkedin.com/jobs/search/?keywords=software%20developer&location=bangalore",
            "indeed": "https://www.indeed.co.in/jobs?q=software+developer&l=bangalore",
            "naukri": "https://www.naukri.com/software-developer-jobs-in-bangalore",
            "company_careers": "https://techcorp.com/careers"
        },
        "active_openings": [
            {
                "title": "Software Developer - React/Node.js",
                "experience": "0-2 years",
                "apply_link": "https://www.linkedin.com/jobs/view/react-nodejs-developer",
                "posted": "2 days ago"
            },
            {
                "title": "Full Stack Developer Intern",
                "experience": "Fresher",
                "apply_link": "https://www.indeed.co.in/viewjob?jk=fullstack-intern",
                "posted": "1 week ago"
            }
        ]
    },
    {
        "id": "comp_2", 
        "name": "InnovateIT Services",
        "industry": "IT Services & Consulting",
        "type": "Service Company",
        "size": "5000+",
        "salary_range": "₹4-12 LPA",
        "locations": ["Chennai", "Mumbai", "Noida", "Pune"],
        "remote_friendly": False,
        "hiring_process": ["Aptitude Test", "Group Discussion", "Technical Round", "HR Round"],
        "requirements": ["Engineering degree", "Communication skills", "Team player"],
        "tech_stack": ["Java", ".NET", "Angular", "Spring", "Oracle", "Azure"],
        "culture": ["Process Excellence", "Client Focus", "Professional Growth", "Diversity"],
        "benefits": ["Health Insurance", "Transport", "Cafeteria", "Training Programs"],
        "growth_opportunities": ["Senior Consultant", "Team Lead", "Project Manager", "Delivery Manager"],
        "company_values": ["Excellence", "Integrity", "Innovation", "Respect"],
        "work_environment": "Office",
        "founded_year": 2008,
        "funding_stage": "Public",
        "description": "Global IT services provider delivering digital transformation solutions",
        "job_links": {
            "linkedin": "https://www.linkedin.com/jobs/search/?keywords=software%20engineer&location=chennai",
            "indeed": "https://www.indeed.co.in/jobs?q=software+engineer&l=chennai",
            "naukri": "https://www.naukri.com/software-engineer-jobs-in-chennai",
            "company_careers": "https://innovateit.com/careers"
        },
        "active_openings": [
            {
                "title": "Associate Software Engineer",
                "experience": "0-1 years",
                "apply_link": "https://www.naukri.com/job-listings/associate-software-engineer",
                "posted": "3 days ago"
            },
            {
                "title": "Graduate Trainee - IT",
                "experience": "Fresher",
                "apply_link": "https://www.linkedin.com/jobs/view/graduate-trainee-it",
                "posted": "5 days ago"
            }
        ]
    },
    {
        "id": "comp_3",
        "name": "DataFlow Analytics",
        "industry": "Data Science & AI",
        "type": "Product Company",
        "size": "200-1000",
        "salary_range": "₹8-20 LPA",
        "locations": ["Bangalore", "Delhi", "Mumbai"],
        "remote_friendly": True,
        "hiring_process": ["Technical Assessment", "Data Challenge", "Technical Interview", "Cultural Fit"],
        "requirements": ["Strong in Python/R", "Machine Learning", "Statistics", "SQL"],
        "tech_stack": ["Python", "TensorFlow", "PyTorch", "Apache Spark", "Kubernetes", "GCP"],
        "culture": ["Data-driven", "Research", "Innovation", "Continuous Learning"],
        "benefits": ["Stock Options", "Conference Budget", "Latest Hardware", "Flexible PTO"],
        "growth_opportunities": ["Senior Data Scientist", "ML Engineer", "Research Scientist", "Head of AI"],
        "company_values": ["Excellence", "Innovation", "Transparency", "Growth"],
        "work_environment": "Remote-First",
        "founded_year": 2018,
        "funding_stage": "Series A",
        "description": "AI-first company building next-generation analytics and machine learning platforms"
    },
    {
        "id": "comp_4",
        "name": "FinTech Innovations",
        "industry": "Financial Technology",
        "type": "Startup",
        "size": "50-200",
        "salary_range": "₹10-25 LPA",
        "locations": ["Mumbai", "Bangalore"],
        "remote_friendly": True,
        "hiring_process": ["Coding Challenge", "System Design", "Cultural Interview", "Final Round"],
        "requirements": ["Full-stack development", "Financial domain knowledge", "Problem solving"],
        "tech_stack": ["React", "Node.js", "PostgreSQL", "Docker", "Kubernetes", "Blockchain"],
        "culture": ["Fast-paced", "Innovation", "Ownership", "Results-oriented"],
        "benefits": ["Equity", "Performance Bonus", "Health & Wellness", "Learning Budget"],
        "growth_opportunities": ["Tech Lead", "Principal Engineer", "CTO Track", "Product Owner"],
        "company_values": ["Innovation", "Trust", "Speed", "Customer First"],
        "work_environment": "Hybrid",
        "founded_year": 2020,
        "funding_stage": "Seed",
        "description": "Revolutionary fintech startup disrupting traditional banking with AI and blockchain"
    },
    {
        "id": "comp_5",
        "name": "CloudScale Systems",
        "industry": "Cloud Infrastructure",
        "type": "Product Company",
        "size": "500-1000",
        "salary_range": "₹12-22 LPA",
        "locations": ["Bangalore", "Hyderabad"],
        "remote_friendly": True,
        "hiring_process": ["System Design", "Technical Deep Dive", "Architecture Discussion", "Leadership Chat"],
        "requirements": ["Distributed systems", "Cloud platforms", "DevOps", "Microservices"],
        "tech_stack": ["Go", "Kubernetes", "Docker", "AWS", "Terraform", "Prometheus"],
        "culture": ["Technical Excellence", "Scale", "Reliability", "Innovation"],
        "benefits": ["Stock Options", "Tech Conference", "Top-tier Hardware", "Sabbatical"],
        "growth_opportunities": ["Staff Engineer", "Principal Engineer", "Architect", "Engineering Manager"],
        "company_values": ["Excellence", "Scale", "Reliability", "Collaboration"],
        "work_environment": "Remote-First",
        "founded_year": 2016,
        "funding_stage": "Series C",
        "description": "Building the future of cloud infrastructure with cutting-edge distributed systems"
    },
    {
        "id": "comp_6",
        "name": "EduTech Learning",
        "industry": "Education Technology",
        "type": "Product Company",
        "size": "200-500",
        "salary_range": "₹7-18 LPA",
        "locations": ["Delhi", "Bangalore", "Kolkata"],
        "remote_friendly": True,
        "hiring_process": ["Portfolio Review", "Technical Round", "Product Thinking", "Culture Fit"],
        "requirements": ["Full-stack development", "UI/UX understanding", "Educational domain interest"],
        "tech_stack": ["React", "Django", "PostgreSQL", "Redis", "WebRTC", "ML/AI"],
        "culture": ["Impact-driven", "Learning", "Empathy", "Innovation"],
        "benefits": ["Course Allowance", "Flexible Hours", "Impact Bonus", "Health Coverage"],
        "growth_opportunities": ["Senior Developer", "Product Engineer", "Tech Lead", "Head of Engineering"],
        "company_values": ["Education", "Accessibility", "Quality", "Innovation"],
        "work_environment": "Hybrid",
        "founded_year": 2017,
        "funding_stage": "Series B",
        "description": "Democratizing quality education through innovative technology and AI-powered learning"
    },
    {
        "id": "comp_7",
        "name": "HealthCare Digital",
        "industry": "Healthcare Technology",
        "type": "Product Company",
        "size": "300-800",
        "salary_range": "₹9-20 LPA",
        "locations": ["Mumbai", "Chennai", "Pune"],
        "remote_friendly": False,
        "hiring_process": ["Technical Assessment", "Healthcare Domain Round", "System Design", "Final Interview"],
        "requirements": ["Healthcare domain knowledge", "Data security", "Compliance understanding"],
        "tech_stack": ["Java", "Spring Boot", "Angular", "MySQL", "Docker", "FHIR"],
        "culture": ["Patient-first", "Compliance", "Quality", "Innovation"],
        "benefits": ["Health Insurance", "Medical Checkups", "Wellness Programs", "Training"],
        "growth_opportunities": ["Senior Engineer", "Solution Architect", "Product Manager", "Domain Expert"],
        "company_values": ["Care", "Quality", "Trust", "Innovation"],
        "work_environment": "Office",
        "founded_year": 2014,
        "funding_stage": "Series B",
        "description": "Transforming healthcare delivery through secure, compliant digital health solutions"
    },
    {
        "id": "comp_8",
        "name": "GameStudio Interactive",
        "industry": "Gaming & Entertainment",
        "type": "Product Company",
        "size": "100-300",
        "salary_range": "₹6-16 LPA",
        "locations": ["Bangalore", "Hyderabad"],
        "remote_friendly": True,
        "hiring_process": ["Portfolio Review", "Technical Challenge", "Game Design Discussion", "Team Fit"],
        "requirements": ["Game development", "Unity/Unreal", "3D graphics", "Performance optimization"],
        "tech_stack": ["Unity", "C#", "Unreal Engine", "C++", "WebGL", "Mobile Platforms"],
        "culture": ["Creativity", "Fun", "Innovation", "Passion"],
        "benefits": ["Game Library", "Flexible Hours", "Creative Time", "Team Events"],
        "growth_opportunities": ["Senior Game Developer", "Tech Lead", "Game Designer", "Studio Head"],
        "company_values": ["Creativity", "Quality", "Fun", "Innovation"],
        "work_environment": "Hybrid",
        "founded_year": 2019,
        "funding_stage": "Bootstrap",
        "description": "Creating immersive gaming experiences with cutting-edge technology and creative storytelling"
    },
    {
        "id": "comp_9",
        "name": "RetailTech Solutions",
        "industry": "E-commerce & Retail",
        "type": "Product Company",
        "size": "1000-2000",
        "salary_range": "₹8-18 LPA",
        "locations": ["Mumbai", "Delhi", "Bangalore"],
        "remote_friendly": True,
        "hiring_process": ["Online Test", "System Design", "Technical Interview", "Bar Raiser"],
        "requirements": ["Scalable systems", "E-commerce domain", "Performance optimization"],
        "tech_stack": ["Java", "Spring", "React", "Elasticsearch", "Apache Kafka", "AWS"],
        "culture": ["Customer obsession", "Scale", "Innovation", "Ownership"],
        "benefits": ["Stock Options", "Performance Bonus", "Shopping Credits", "Comprehensive Insurance"],
        "growth_opportunities": ["Senior SDE", "Principal Engineer", "Engineering Manager", "Director Engineering"],
        "company_values": ["Customer First", "Innovation", "Excellence", "Trust"],
        "work_environment": "Hybrid",
        "founded_year": 2012,
        "funding_stage": "Public",
        "description": "India's leading e-commerce platform serving millions of customers with innovative retail solutions"
    },
    {
        "id": "comp_10",
        "name": "CyberSec Guard",
        "industry": "Cybersecurity",
        "type": "Product Company",
        "size": "200-500",
        "salary_range": "₹10-25 LPA",
        "locations": ["Delhi", "Pune", "Chennai"],
        "remote_friendly": False,
        "hiring_process": ["Security Assessment", "Penetration Test", "Technical Deep Dive", "Clearance Check"],
        "requirements": ["Cybersecurity expertise", "Ethical hacking", "Compliance knowledge", "Risk assessment"],
        "tech_stack": ["Python", "Kali Linux", "Wireshark", "Metasploit", "Splunk", "SIEM Tools"],
        "culture": ["Security-first", "Continuous Learning", "Vigilance", "Excellence"],
        "benefits": ["Security Clearance", "Training Certifications", "Conference Budget", "Top Hardware"],
        "growth_opportunities": ["Senior Security Engineer", "Security Architect", "CISO Track", "Consultant"],
        "company_values": ["Security", "Trust", "Excellence", "Innovation"],
        "work_environment": "Office",
        "founded_year": 2013,
        "funding_stage": "Series A",
        "description": "Leading cybersecurity firm protecting enterprises from advanced threats and vulnerabilities"
    }
]

# Authentication Routes
@api_router.post("/auth/register")
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    user = User(
        email=user_data.email,
        name=user_data.name,
        college=user_data.college,
        branch=user_data.branch,
        year=user_data.year
    )
    
    user_dict = prepare_for_mongo(user.dict())
    user_dict["password"] = hashed_password.decode('utf-8')
    
    await db.users.insert_one(user_dict)
    
    # Create JWT token
    token = create_jwt_token(user.id)
    
    return {"token": token, "user": user.dict()}

@api_router.post("/auth/login")
async def login_user(login_data: UserLogin):
    # Find user
    user = await db.users.find_one({"email": login_data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check password
    if not bcrypt.checkpw(login_data.password.encode('utf-8'), user["password"].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    token = create_jwt_token(user["id"])
    
    user_data = parse_from_mongo(user)
    user_data.pop("password", None)  # Remove password from response
    
    return {"token": token, "user": user_data}

@api_router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return current_user

# Project Management Routes
@api_router.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate, current_user: dict = Depends(get_current_user)):
    project = Project(
        title=project_data.title,
        description=project_data.description,
        user_id=current_user["id"],
        team_members=project_data.team_members,
        deadline=project_data.deadline
    )
    
    project_dict = prepare_for_mongo(project.dict())
    await db.projects.insert_one(project_dict)
    
    return project

@api_router.get("/projects", response_model=List[Project])
async def get_user_projects(current_user: dict = Depends(get_current_user)):
    projects = await db.projects.find({"user_id": current_user["id"]}).to_list(100)
    return [Project(**parse_from_mongo(project)) for project in projects]

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return Project(**parse_from_mongo(project))

@api_router.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, project_data: ProjectCreate, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = prepare_for_mongo(project_data.dict(exclude_unset=True))
    await db.projects.update_one({"id": project_id}, {"$set": update_data})
    
    updated_project = await db.projects.find_one({"id": project_id})
    return Project(**parse_from_mongo(updated_project))

# Task Management Routes
@api_router.post("/projects/{project_id}/tasks", response_model=Task)
async def create_task(project_id: str, task_data: TaskCreate, current_user: dict = Depends(get_current_user)):
    # Verify project ownership
    project = await db.projects.find_one({"id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    task = Task(
        title=task_data.title,
        description=task_data.description,
        project_id=project_id,
        assigned_to=task_data.assigned_to,
        priority=task_data.priority,
        due_date=task_data.due_date
    )
    
    task_dict = prepare_for_mongo(task.dict())
    await db.tasks.insert_one(task_dict)
    
    return task

@api_router.get("/projects/{project_id}/tasks", response_model=List[Task])
async def get_project_tasks(project_id: str, current_user: dict = Depends(get_current_user)):
    # Verify project ownership
    project = await db.projects.find_one({"id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    tasks = await db.tasks.find({"project_id": project_id}).to_list(100)
    return [Task(**parse_from_mongo(task)) for task in tasks]

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_data: dict, current_user: dict = Depends(get_current_user)):
    task = await db.tasks.find_one({"id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Verify project ownership
    project = await db.projects.find_one({"id": task["project_id"], "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = prepare_for_mongo(task_data)
    await db.tasks.update_one({"id": task_id}, {"$set": update_data})
    
    updated_task = await db.tasks.find_one({"id": task_id})
    return Task(**parse_from_mongo(updated_task))

# Quiz Routes
@api_router.get("/quiz/questions/{category}")
async def get_quiz_questions(category: str):
    if category == "aptitude":
        return APTITUDE_QUESTIONS
    elif category == "coding":
        return CODING_QUESTIONS
    else:
        raise HTTPException(status_code=400, detail="Invalid category")

@api_router.post("/quiz/session", response_model=QuizSession)
async def create_quiz_session(category: str, current_user: dict = Depends(get_current_user)):
    session = QuizSession(
        user_id=current_user["id"],
        category=category,
        total_questions=len(APTITUDE_QUESTIONS if category == "aptitude" else CODING_QUESTIONS)
    )
    
    session_dict = prepare_for_mongo(session.dict())
    await db.quiz_sessions.insert_one(session_dict)
    
    return session

@api_router.post("/quiz/answer")
async def submit_quiz_answer(answer: QuizAnswer, current_user: dict = Depends(get_current_user)):
    # Verify session ownership
    session = await db.quiz_sessions.find_one({"id": answer.session_id, "user_id": current_user["id"]})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    answer_dict = prepare_for_mongo(answer.dict())
    await db.quiz_answers.insert_one(answer_dict)
    
    # Update session score
    if answer.is_correct:
        await db.quiz_sessions.update_one(
            {"id": answer.session_id},
            {"$inc": {"score": 1}}
        )
    
    return {"message": "Answer submitted"}

# Interview Routes
@api_router.post("/interview/session", response_model=InterviewSession)
async def create_interview_session(interview_type: str, current_user: dict = Depends(get_current_user)):
    if interview_type not in ["hr", "technical"]:
        raise HTTPException(status_code=400, detail="Invalid interview type")
    
    questions = INTERVIEW_QUESTIONS[interview_type]
    session = InterviewSession(
        user_id=current_user["id"],
        type=interview_type,
        questions=[{"id": f"{interview_type}_{i}", "question": q} for i, q in enumerate(questions)]
    )
    
    session_dict = prepare_for_mongo(session.dict())
    await db.interview_sessions.insert_one(session_dict)
    
    return session

@api_router.post("/interview/{session_id}/response")
async def submit_interview_response(session_id: str, response_data: dict, current_user: dict = Depends(get_current_user)):
    # Verify session ownership
    session = await db.interview_sessions.find_one({"id": session_id, "user_id": current_user["id"]})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Add response
    await db.interview_sessions.update_one(
        {"id": session_id},
        {"$push": {"responses": response_data}}
    )
    
    return {"message": "Response submitted"}

# AI-Powered Interview Feedback and YouTube Resource Recommendations

def analyze_interview_response(question, answer, interview_type):
    """
    Analyze interview response and provide detailed feedback
    """
    feedback = {
        "overall_score": 0,
        "strengths": [],
        "improvements": [],
        "detailed_feedback": "",
        "communication_score": 0,
        "content_score": 0,
        "confidence_score": 0
    }
    
    if not answer or len(answer.strip()) < 10:
        feedback.update({
            "overall_score": 20,
            "detailed_feedback": "Response too brief. Provide more detailed answers with examples.",
            "improvements": ["Elaborate more on your answer", "Include specific examples", "Show enthusiasm"],
            "communication_score": 20,
            "content_score": 10,
            "confidence_score": 30
        })
        return feedback
    
    answer_lower = answer.lower()
    word_count = len(answer.split())
    
    # Content Analysis
    content_score = 50  # Base score
    
    # Check for specific keywords based on interview type
    if interview_type == "hr":
        positive_keywords = [
            "experience", "team", "project", "challenge", "learn", "growth", 
            "passion", "goal", "achievement", "collaboration", "leadership",
            "problem-solving", "dedication", "opportunity", "contribute"
        ]
        technical_keywords = ["skills", "technical", "programming", "development"]
        
        # Boost score for HR-relevant content
        for keyword in positive_keywords:
            if keyword in answer_lower:
                content_score += 5
                
    elif interview_type == "technical":
        technical_keywords = [
            "algorithm", "data structure", "programming", "code", "development",
            "framework", "database", "api", "testing", "optimization", "design pattern",
            "architecture", "scalability", "performance", "debugging", "version control"
        ]
        
        # Boost score for technical content
        for keyword in technical_keywords:
            if keyword in answer_lower:
                content_score += 6
    
    # Communication Analysis
    communication_score = 60  # Base score
    
    # Word count analysis
    if 50 <= word_count <= 200:
        communication_score += 20
    elif 20 <= word_count < 50:
        communication_score += 10
    elif word_count > 200:
        communication_score += 5
    
    # Check for structured response
    structure_indicators = ["first", "second", "finally", "because", "however", "therefore", "for example"]
    for indicator in structure_indicators:
        if indicator in answer_lower:
            communication_score += 5
            break
    
    # Confidence Analysis
    confidence_score = 55  # Base score
    
    # Positive confidence indicators
    confidence_boosters = ["confident", "believe", "experienced", "skilled", "capable", "successful"]
    uncertainty_words = ["maybe", "perhaps", "not sure", "i think", "probably", "might"]
    
    for booster in confidence_boosters:
        if booster in answer_lower:
            confidence_score += 8
    
    for uncertainty in uncertainty_words:
        if uncertainty in answer_lower:
            confidence_score -= 5
    
    # Calculate overall score
    overall_score = (content_score + communication_score + confidence_score) / 3
    
    # Generate feedback
    strengths = []
    improvements = []
    
    if content_score >= 70:
        strengths.append("Strong domain knowledge demonstrated")
    if communication_score >= 70:
        strengths.append("Clear and well-structured communication")
    if confidence_score >= 70:
        strengths.append("Shows confidence and conviction")
    if word_count >= 50:
        strengths.append("Detailed and comprehensive response")
    
    if content_score < 60:
        improvements.append("Include more specific examples and technical details")
    if communication_score < 60:
        improvements.append("Structure your response better with clear points")
    if confidence_score < 60:
        improvements.append("Express more confidence in your abilities")
    if word_count < 30:
        improvements.append("Provide more elaborate answers")
    
    # Generate detailed feedback
    if overall_score >= 80:
        detailed_feedback = "Excellent response! You demonstrated strong knowledge and communication skills."
    elif overall_score >= 65:
        detailed_feedback = "Good response with room for improvement. Focus on the areas mentioned below."
    elif overall_score >= 50:
        detailed_feedback = "Average response. Work on providing more detailed and confident answers."
    else:
        detailed_feedback = "Response needs significant improvement. Practice more structured and detailed answers."
    
    feedback.update({
        "overall_score": min(95, max(15, round(overall_score))),
        "content_score": min(95, max(15, content_score)),
        "communication_score": min(95, max(15, communication_score)),
        "confidence_score": min(95, max(15, confidence_score)),
        "strengths": strengths,
        "improvements": improvements,
        "detailed_feedback": detailed_feedback
    })
    
    return feedback

def generate_youtube_recommendations(user_skills, user_branch, weak_areas=None):
    """
    Generate personalized YouTube learning resources based on user profile
    """
    recommendations = []
    
    # Branch-specific YouTube channels and topics
    branch_resources = {
        "Computer Science": {
            "channels": [
                {"name": "freeCodeCamp.org", "url": "https://www.youtube.com/c/Freecodecamp"},
                {"name": "Traversy Media", "url": "https://www.youtube.com/c/TraversyMedia"},
                {"name": "The Net Ninja", "url": "https://www.youtube.com/c/TheNetNinja"},
                {"name": "Coding Interview Pro", "url": "https://www.youtube.com/c/CodingInterviewPro"}
            ],
            "playlists": [
                {"title": "Data Structures and Algorithms", "url": "https://www.youtube.com/playlist?list=PLgUwDviBIf0p4ozDR_kJJkONnb1wdx2Ma"},
                {"title": "System Design Interview", "url": "https://www.youtube.com/playlist?list=PLMCXHnjXnTnvo6alSjVkgxV-VH6EPyvoX"},
                {"title": "React.js Complete Course", "url": "https://www.youtube.com/watch?v=w7ejDZ8SWv8"}
            ]
        },
        "Information Technology": {
            "channels": [
                {"name": "NetworkChuck", "url": "https://www.youtube.com/c/NetworkChuck"},
                {"name": "Professor Messer", "url": "https://www.youtube.com/c/professormesser"},
                {"name": "PowerCert Animated Videos", "url": "https://www.youtube.com/c/PowerCertAnimatedVideos"}
            ],
            "playlists": [
                {"title": "CompTIA Network+ Course", "url": "https://www.youtube.com/playlist?list=PLG49S3nxzAnmpdmX7RoTOyuNJQAb-r-gd"},
                {"title": "Cybersecurity Fundamentals", "url": "https://www.youtube.com/playlist?list=PLhfrWIlLOoKOc7f8weL0lJneygGF_C0Jf"}
            ]
        },
        "Electronics": {
            "channels": [
                {"name": "EEVblog", "url": "https://www.youtube.com/c/EevblogDave"},
                {"name": "GreatScott!", "url": "https://www.youtube.com/c/greatscottlab"},
                {"name": "ElectroBOOM", "url": "https://www.youtube.com/c/Electroboom"}
            ],
            "playlists": [
                {"title": "Arduino Tutorial Series", "url": "https://www.youtube.com/playlist?list=PLGs0VKk2DiYw-L-RibttcvK-WBZm8WLEP"},
                {"title": "PCB Design Basics", "url": "https://www.youtube.com/playlist?list=PLXSyc11qLa1YhVCZ5Skxrf8CehnKT_2SV"}
            ]
        },
        "Mechanical": {
            "channels": [
                {"name": "SolidWorks", "url": "https://www.youtube.com/c/SolidWorksOfficial"},
                {"name": "TITANS of CNC", "url": "https://www.youtube.com/c/TITANSofCNC"},
                {"name": "Learn Engineering", "url": "https://www.youtube.com/c/LearnEngineering"}
            ],
            "playlists": [
                {"title": "SolidWorks Tutorials", "url": "https://www.youtube.com/playlist?list=PLym8blx7B-xPgW9mKE2FWW_pI0SX-J8-j"},
                {"title": "Manufacturing Processes", "url": "https://www.youtube.com/playlist?list=PLuUdFsbOK_8pKOD8_xxjPN8eFJODNXBFV"}
            ]
        },
        "Electrical": {
            "channels": [
                {"name": "ElectricalEngineeringXYZ", "url": "https://www.youtube.com/c/ElectricalEngineeringXYZ"},
                {"name": "ALL ABOUT ELECTRONICS", "url": "https://www.youtube.com/c/ALLABOUTELECTRONICS"},
                {"name": "Power System Lectures", "url": "https://www.youtube.com/c/PowerSystemLectures"}
            ],
            "playlists": [
                {"title": "Power Systems Analysis", "url": "https://www.youtube.com/playlist?list=PLgMDNELGJ1CaXVfvR3n2CU41pKP8kxPKY"},
                {"title": "Control Systems", "url": "https://www.youtube.com/playlist?list=PLUMWjy5jgHK1NC52DXXrriwihVrYZKqjk"}
            ]
        },
        "Civil": {
            "channels": [
                {"name": "Civil Engineering X", "url": "https://www.youtube.com/c/CivilEngineeringX"},
                {"name": "The Constructor", "url": "https://www.youtube.com/c/TheConstructor"},
                {"name": "STAAD Pro Learning", "url": "https://www.youtube.com/c/STAADProLearning"}
            ],
            "playlists": [
                {"title": "Structural Engineering", "url": "https://www.youtube.com/playlist?list=PLOAuB8dR35oeF_DRSB-wVbbFXHVq-oOL-"},
                {"title": "AutoCAD Civil 3D", "url": "https://www.youtube.com/playlist?list=PLgMDNELGJ1CZe9XLpCgDMj_lVi7p5ACBh"}
            ]
        }
    }
    
    # Skill-specific recommendations
    skill_resources = {
        "python": [
            {"title": "Python Programming Tutorial", "url": "https://www.youtube.com/watch?v=_uQrJ0TkZlc", "duration": "6 hours"},
            {"title": "Python Projects for Beginners", "url": "https://www.youtube.com/watch?v=8ext9G7xspg", "duration": "5 hours"}
        ],
        "javascript": [
            {"title": "JavaScript Crash Course", "url": "https://www.youtube.com/watch?v=hdI2bqOjy3c", "duration": "1.5 hours"},
            {"title": "JavaScript Projects", "url": "https://www.youtube.com/watch?v=3PHXvlpOkf4", "duration": "8 hours"}
        ],
        "react": [
            {"title": "React Course for Beginners", "url": "https://www.youtube.com/watch?v=bMknfKXIFA8", "duration": "5 hours"},
            {"title": "React Projects Tutorial", "url": "https://www.youtube.com/watch?v=a_7Z7C_JCyo", "duration": "12 hours"}
        ],
        "machine learning": [
            {"title": "Machine Learning Course", "url": "https://www.youtube.com/watch?v=NWONeJKn6kc", "duration": "20 hours"},
            {"title": "Python for Machine Learning", "url": "https://www.youtube.com/watch?v=7eh4d6sabA0", "duration": "4 hours"}
        ]
    }
    
    # Interview preparation resources
    interview_prep = [
        {"title": "Software Engineering Interview Prep", "url": "https://www.youtube.com/watch?v=KdXAUst8bdo", "duration": "2 hours"},
        {"title": "HR Interview Questions and Answers", "url": "https://www.youtube.com/watch?v=naIkpQ_cIt0", "duration": "1 hour"},
        {"title": "System Design Interview Questions", "url": "https://www.youtube.com/watch?v=UzLMhqg3_Wc", "duration": "3 hours"}
    ]
    
    # Generate personalized recommendations
    if user_branch in branch_resources:
        recommendations.extend([
            {
                "category": f"{user_branch} Fundamentals",
                "resources": branch_resources[user_branch]["channels"][:2] + branch_resources[user_branch]["playlists"][:2],
                "priority": "high"
            }
        ])
    
    # Add skill-specific resources
    skill_recommendations = []
    for skill in user_skills[:5]:  # Top 5 skills
        skill_key = skill.lower()
        if skill_key in skill_resources:
            skill_recommendations.extend(skill_resources[skill_key])
    
    if skill_recommendations:
        recommendations.append({
            "category": "Skill Enhancement",
            "resources": skill_recommendations,
            "priority": "medium"
        })
    
    # Add interview preparation
    recommendations.append({
        "category": "Interview Preparation",
        "resources": interview_prep,
        "priority": "high"
    })
    
    # Add weak areas improvement (if provided)
    if weak_areas:
        weak_area_resources = []
        for area in weak_areas:
            area_key = area.lower().replace(" ", "")
            if area_key in skill_resources:
                weak_area_resources.extend(skill_resources[area_key])
        
        if weak_area_resources:
            recommendations.append({
                "category": "Areas for Improvement",
                "resources": weak_area_resources,
                "priority": "high"
            })
    
    return recommendations
def extract_skills_from_linkedin(linkedin_data):
    """Extract skills from LinkedIn data"""
    skills = set()
    
    # Extract from skills section
    if 'skills' in linkedin_data:
        if isinstance(linkedin_data['skills'], list):
            skills.update([skill.lower() for skill in linkedin_data['skills']])
        elif isinstance(linkedin_data['skills'], str):
            skills.update([skill.strip().lower() for skill in linkedin_data['skills'].split(',')])
    
    # Extract from experience descriptions
    if 'experience' in linkedin_data:
        for exp in linkedin_data.get('experience', []):
            description = exp.get('description', '').lower()
            # Look for common tech skills in descriptions
            tech_keywords = [
                'python', 'java', 'javascript', 'react', 'node.js', 'angular', 'vue',
                'spring', 'django', 'flask', 'aws', 'azure', 'gcp', 'docker', 'kubernetes',
                'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'tensorflow',
                'pytorch', 'machine learning', 'ai', 'blockchain', 'devops', 'ci/cd'
            ]
            for keyword in tech_keywords:
                if keyword in description:
                    skills.add(keyword)
    
    # Extract from projects
    if 'projects' in linkedin_data:
        for project in linkedin_data.get('projects', []):
            technologies = project.get('technologies', [])
            if isinstance(technologies, list):
                skills.update([tech.lower() for tech in technologies])
    
    return list(skills)

def calculate_skill_match_score(user_skills, company_tech_stack):
    """Calculate skill match percentage"""
    if not user_skills or not company_tech_stack:
        return 0
    
    user_skills_lower = [skill.lower() for skill in user_skills]
    company_skills_lower = [skill.lower() for skill in company_tech_stack]
    
    matches = 0
    for company_skill in company_skills_lower:
        for user_skill in user_skills_lower:
            if user_skill in company_skill or company_skill in user_skill:
                matches += 1
                break
    
    return (matches / len(company_skills_lower)) * 100

def calculate_location_match_score(user_location, company_locations):
    """Calculate location preference match"""
    if not user_location or not company_locations:
        return 50  # neutral score if no location data
    
    user_location_lower = user_location.lower()
    for location in company_locations:
        if user_location_lower in location.lower() or location.lower() in user_location_lower:
            return 100
    
    return 20  # low score if no location match

def calculate_experience_match_score(user_experience, company_size, company_type):
    """Calculate experience level match"""
    experience_years = 0
    
    # Try to extract years of experience
    if isinstance(user_experience, list):
        experience_years = len(user_experience)  # Count number of experiences
    elif isinstance(user_experience, str):
        # Look for years in experience description
        years_match = re.findall(r'(\d+)\s*(?:year|yr)', user_experience.lower())
        if years_match:
            experience_years = max([int(year) for year in years_match])
    
    # Match based on company type and size
    if company_type == "Startup" and experience_years <= 2:
        return 90  # Startups often hire fresh graduates
    elif company_type == "Product Company" and experience_years <= 3:
        return 85
    elif "Service" in company_type and experience_years >= 0:
        return 80  # Service companies hire at all levels
    elif company_size == "5000+" and experience_years >= 1:
        return 75  # Large companies prefer some experience
    
    return 60  # default score

def calculate_culture_match_score(user_interests, company_culture, company_values):
    """Calculate cultural fit based on interests and values"""
    if not user_interests:
        return 70  # neutral score
    
    user_interests_lower = [interest.lower() for interest in user_interests]
    culture_keywords = [item.lower() for item in company_culture + company_values]
    
    matches = 0
    for interest in user_interests_lower:
        for culture_item in culture_keywords:
            if interest in culture_item or culture_item in interest:
                matches += 1
                break
    
    if matches > 0:
        return min(90, 60 + (matches * 10))
    return 50

def calculate_salary_attractiveness(salary_range, user_experience_level):
    """Calculate how attractive the salary is"""
    # Extract salary numbers
    salary_match = re.findall(r'(\d+)-(\d+)', salary_range)
    if not salary_match:
        return 50
    
    min_salary, max_salary = map(int, salary_match[0])
    avg_salary = (min_salary + max_salary) / 2
    
    # Score based on salary range
    if avg_salary >= 15:
        return 95
    elif avg_salary >= 10:
        return 85
    elif avg_salary >= 7:
        return 75
    else:
        return 60

def get_match_explanation(user_skills, company_data, scores):
    """Generate explanation for the match"""
    explanations = []
    
    # Skill match explanation
    if scores['skill_match'] >= 70:
        matching_skills = []
        user_skills_lower = [skill.lower() for skill in user_skills]
        for skill in company_data['tech_stack']:
            if any(user_skill in skill.lower() or skill.lower() in user_skill for user_skill in user_skills_lower):
                matching_skills.append(skill)
        
        if matching_skills:
            explanations.append(f"Strong technical match with {', '.join(matching_skills[:3])}")
    
    # Culture match explanation
    if scores['culture_match'] >= 75:
        explanations.append(f"Great cultural alignment with company values")
    
    # Location match explanation
    if scores['location_match'] >= 80:
        explanations.append(f"Located in your preferred area")
    
    # Company type explanation
    if company_data['type'] == 'Startup':
        explanations.append("Fast-growing startup environment")
    elif company_data['type'] == 'Product Company':
        explanations.append("Product-focused company with innovation opportunities")
    
    return explanations

def analyze_linkedin_and_match_companies(linkedin_data):
    """Main function to analyze LinkedIn data and match with companies"""
    # Extract user profile information
    user_skills = extract_skills_from_linkedin(linkedin_data)
    user_location = linkedin_data.get('location', '')
    user_experience = linkedin_data.get('experience', [])
    user_interests = []
    
    # Extract interests from various fields
    if 'interests' in linkedin_data:
        user_interests = linkedin_data['interests']
    if 'summary' in linkedin_data:
        summary = linkedin_data['summary'].lower()
        interest_keywords = ['innovation', 'technology', 'ai', 'startup', 'learning', 'growth', 'leadership']
        user_interests.extend([keyword for keyword in interest_keywords if keyword in summary])
    
    matched_companies = []
    
    for company in COMPANY_DATA:
        # Calculate different matching scores
        skill_match = calculate_skill_match_score(user_skills, company['tech_stack'])
        location_match = calculate_location_match_score(user_location, company['locations'])
        experience_match = calculate_experience_match_score(user_experience, company['size'], company['type'])
        culture_match = calculate_culture_match_score(user_interests, company['culture'], company['company_values'])
        salary_score = calculate_salary_attractiveness(company['salary_range'], len(user_experience))
        
        # Calculate overall match score with weighted factors
        overall_score = (
            skill_match * 0.35 +           # Technical skills - most important
            culture_match * 0.25 +         # Cultural fit
            experience_match * 0.15 +      # Experience level
            location_match * 0.15 +        # Location preference  
            salary_score * 0.10            # Salary attractiveness
        )
        
        scores = {
            'overall': round(overall_score, 1),
            'skill_match': round(skill_match, 1),
            'culture_match': round(culture_match, 1),
            'location_match': round(location_match, 1),
            'experience_match': round(experience_match, 1),
            'salary_score': round(salary_score, 1)
        }
        
        # Generate match explanations
        explanations = get_match_explanation(user_skills, company, scores)
        
        matched_company = {
            **company,
            'match_score': scores,
            'match_explanations': explanations,
            'matching_skills': [skill for skill in company['tech_stack'] 
                              if any(user_skill.lower() in skill.lower() or skill.lower() in user_skill.lower() 
                                   for user_skill in user_skills)],
            'recommended_roles': company['growth_opportunities'][:3]  # Top 3 growth opportunities
        }
        
        matched_companies.append(matched_company)
    
    # Sort by overall match score
    matched_companies.sort(key=lambda x: x['match_score']['overall'], reverse=True)
    
    return {
        'user_profile_summary': {
            'skills': user_skills,
            'location': user_location,
            'experience_count': len(user_experience) if isinstance(user_experience, list) else 0,
            'interests': user_interests
        },
        'matched_companies': matched_companies,
        'total_matches': len(matched_companies),
        'top_matches': matched_companies[:5]  # Return top 5 matches
    }
@api_router.get("/companies")
async def get_companies():
    return COMPANY_DATA

@api_router.get("/companies/{company_id}")
async def get_company(company_id: str):
    company = next((c for c in COMPANY_DATA if c["id"] == company_id), None)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return company

@api_router.post("/companies/match-profile")
async def match_companies_with_profile(linkedin_data: dict, current_user: dict = Depends(get_current_user)):
    """
    AI-powered company matching based on LinkedIn profile data
    """
    try:
        # Analyze LinkedIn data and get matched companies
        matching_results = analyze_linkedin_and_match_companies(linkedin_data)
        
        # Store the matching results for the user
        await db.company_matches.delete_many({"user_id": current_user["id"]})  # Remove old matches
        
        match_record = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "linkedin_data": linkedin_data,
            "matching_results": matching_results,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.company_matches.insert_one(prepare_for_mongo(match_record))
        
        return {
            "message": "Profile analysis complete",
            "results": matching_results
        }
        
    except Exception as e:
        print(f"Error in company matching: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze profile and match companies")

@api_router.get("/companies/my-matches")
async def get_user_company_matches(current_user: dict = Depends(get_current_user)):
    """
    Get user's saved company matches
    """
    try:
        match_record = await db.company_matches.find_one({"user_id": current_user["id"]})
        
        if not match_record:
            return {
                "message": "No matches found. Please upload your LinkedIn profile first.",
                "results": None
            }
        
        parsed_record = parse_from_mongo(match_record)
        return {
            "message": "Matches retrieved successfully",
            "results": parsed_record.get("matching_results"),
            "last_updated": parsed_record.get("created_at")
        }
        
    except Exception as e:
        print(f"Error retrieving matches: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve company matches")

# Dashboard Routes
@api_router.get("/dashboard")
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    # Get recent projects
    projects = await db.projects.find({"user_id": current_user["id"]}).sort("created_at", -1).limit(5).to_list(5)
    
    # Get recent tasks
    project_ids = [p["id"] for p in projects]
    tasks = await db.tasks.find({"project_id": {"$in": project_ids}}).sort("created_at", -1).limit(10).to_list(10)
    
    # Get quiz progress
    quiz_sessions = await db.quiz_sessions.find({"user_id": current_user["id"]}).to_list(50)
    
    return {
        "recent_projects": [parse_from_mongo(p) for p in projects],
        "recent_tasks": [parse_from_mongo(t) for t in tasks],
        "quiz_stats": {
            "total_sessions": len(quiz_sessions),
            "average_score": sum(s.get("score", 0) for s in quiz_sessions) / len(quiz_sessions) if quiz_sessions else 0
        }
    }

# Profile Routes
@api_router.put("/profile")
async def update_profile(profile_data: dict, current_user: dict = Depends(get_current_user)):
    update_data = prepare_for_mongo(profile_data)
    await db.users.update_one({"id": current_user["id"]}, {"$set": update_data})
    
    updated_user = await db.users.find_one({"id": current_user["id"]})
    user_data = parse_from_mongo(updated_user)
    user_data.pop("password", None)
    
    return user_data

@api_router.post("/profile/linkedin")
async def import_linkedin_data(linkedin_data: dict, current_user: dict = Depends(get_current_user)):
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"linkedin_data": linkedin_data}}
    )
    
    return {"message": "LinkedIn data imported successfully"}

# Basic routes
@api_router.get("/")
async def root():
    return {"message": "Engineering Student Success Platform API"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()