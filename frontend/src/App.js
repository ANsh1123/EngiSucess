import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';
import axios from 'axios';
import Companies from './Companies';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { token, user } = response.data;
      
      localStorage.setItem('token', token);
      setToken(token);
      setUser(user);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/auth/register`, userData);
      const { token, user } = response.data;
      
      localStorage.setItem('token', token);
      setToken(token);
      setUser(user);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Components
const LoadingSpinner = () => (
  <div className="loading-container">
    <div className="loading-spinner"></div>
    <p>Loading...</p>
  </div>
);

const Navigation = ({ currentView, setCurrentView }) => {
  const { user, logout } = useAuth();

  return (
    <nav className="navigation">
      <div className="nav-brand">
        <h2>EngineersHub</h2>
      </div>
      <div className="nav-links">
        <button 
          className={currentView === 'dashboard' ? 'nav-link active' : 'nav-link'}
          onClick={() => setCurrentView('dashboard')}
        >
          Dashboard
        </button>
        <button 
          className={currentView === 'projects' ? 'nav-link active' : 'nav-link'}
          onClick={() => setCurrentView('projects')}
        >
          Projects
        </button>
        <button 
          className={currentView === 'preparation' ? 'nav-link active' : 'nav-link'}
          onClick={() => setCurrentView('preparation')}
        >
          Prep Zone
        </button>
        <button 
          className={currentView === 'interviews' ? 'nav-link active' : 'nav-link'}
          onClick={() => setCurrentView('interviews')}
        >
          Mock Interviews
        </button>
        <button 
          className={currentView === 'companies' ? 'nav-link active' : 'nav-link'}
          onClick={() => setCurrentView('companies')}
        >
          Companies
        </button>
        <button 
          className={currentView === 'profile' ? 'nav-link active' : 'nav-link'}
          onClick={() => setCurrentView('profile')}
        >
          Profile
        </button>
      </div>
      <div className="nav-user">
        <span>Welcome, {user?.name}</span>
        <button className="btn-secondary" onClick={logout}>Logout</button>
      </div>
    </nav>
  );
};

const AuthForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    college: '',
    branch: '',
    year: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = isLogin 
      ? await login(formData.email, formData.password)
      : await register(formData);

    if (!result.success) {
      setError(result.error);
    }
    setLoading(false);
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>{isLogin ? 'Login' : 'Sign Up'}</h2>
        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="error-message">{error}</div>}
          
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            required
          />
          
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleChange}
            required
          />
          
          {!isLogin && (
            <>
              <input
                type="text"
                name="name"
                placeholder="Full Name"
                value={formData.name}
                onChange={handleChange}
                required
              />
              <input
                type="text"
                name="college"
                placeholder="College Name"
                value={formData.college}
                onChange={handleChange}
              />
              <select
                name="branch"
                value={formData.branch}
                onChange={handleChange}
              >
                <option value="">Select Branch</option>
                <option value="Computer Science">Computer Science</option>
                <option value="Information Technology">Information Technology</option>
                <option value="Electronics">Electronics & Communication</option>
                <option value="Mechanical">Mechanical Engineering</option>
                <option value="Electrical">Electrical Engineering</option>
                <option value="Civil">Civil Engineering</option>
                <option value="Other">Other</option>
              </select>
              <select
                name="year"
                value={formData.year}
                onChange={handleChange}
              >
                <option value="">Select Year</option>
                <option value="1st Year">1st Year</option>
                <option value="2nd Year">2nd Year</option>
                <option value="3rd Year">3rd Year</option>
                <option value="4th Year">4th Year</option>
              </select>
            </>
          )}
          
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Please wait...' : (isLogin ? 'Login' : 'Sign Up')}
          </button>
        </form>
        
        <p className="auth-switch">
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button 
            type="button" 
            className="link-button"
            onClick={() => setIsLogin(!isLogin)}
          >
            {isLogin ? 'Sign Up' : 'Login'}
          </button>
        </p>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>
      
      <div className="dashboard-grid">
        <div className="dashboard-card">
          <h3>Recent Projects</h3>
          {dashboardData?.recent_projects?.length > 0 ? (
            <ul>
              {dashboardData.recent_projects.map(project => (
                <li key={project.id}>{project.title}</li>
              ))}
            </ul>
          ) : (
            <p>No projects yet. <a href="#" onClick={() => {}}>Create your first project!</a></p>
          )}
        </div>
        
        <div className="dashboard-card">
          <h3>Pending Tasks</h3>
          {dashboardData?.recent_tasks?.length > 0 ? (
            <ul>
              {dashboardData.recent_tasks.slice(0, 5).map(task => (
                <li key={task.id}>{task.title}</li>
              ))}
            </ul>
          ) : (
            <p>No tasks pending</p>
          )}
        </div>
        
        <div className="dashboard-card">
          <h3>Quiz Progress</h3>
          <p>Sessions Completed: {dashboardData?.quiz_stats?.total_sessions || 0}</p>
          <p>Average Score: {Math.round(dashboardData?.quiz_stats?.average_score || 0)}%</p>
        </div>
        
        <div className="dashboard-card">
          <h3>Quick Actions</h3>
          <div className="quick-actions">
            <button className="btn-primary">Start Quiz</button>
            <button className="btn-secondary">New Project</button>
            <button className="btn-secondary">Mock Interview</button>
          </div>
        </div>
      </div>
    </div>
  );
};

const Projects = () => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await axios.get(`${API}/projects`);
      setProjects(response.data);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTasks = async (projectId) => {
    try {
      const response = await axios.get(`${API}/projects/${projectId}/tasks`);
      setTasks(response.data);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    }
  };

  const selectProject = (project) => {
    setSelectedProject(project);
    fetchTasks(project.id);
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="projects">
      <div className="projects-header">
        <h1>Project Management</h1>
        <button 
          className="btn-primary"
          onClick={() => setShowCreateForm(!showCreateForm)}
        >
          {showCreateForm ? 'Cancel' : 'New Project'}
        </button>
      </div>

      {showCreateForm && <ProjectCreateForm onSuccess={fetchProjects} onCancel={() => setShowCreateForm(false)} />}

      <div className="projects-layout">
        <div className="projects-sidebar">
          <h3>Your Projects</h3>
          {projects.length > 0 ? (
            <div className="projects-list">
              {projects.map(project => (
                <div 
                  key={project.id} 
                  className={`project-item ${selectedProject?.id === project.id ? 'active' : ''}`}
                  onClick={() => selectProject(project)}
                >
                  <h4>{project.title}</h4>
                  <p>{project.status}</p>
                </div>
              ))}
            </div>
          ) : (
            <p>No projects found. Create your first project!</p>
          )}
        </div>

        <div className="projects-main">
          {selectedProject ? (
            <ProjectDetails project={selectedProject} tasks={tasks} onTaskUpdate={() => fetchTasks(selectedProject.id)} />
          ) : (
            <div className="no-selection">
              <h3>Select a project to view details</h3>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ProjectCreateForm = ({ onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    deadline: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/projects`, {
        ...formData,
        deadline: formData.deadline ? new Date(formData.deadline).toISOString() : null
      });
      onSuccess();
      onCancel();
    } catch (error) {
      console.error('Failed to create project:', error);
    }
  };

  return (
    <div className="create-form">
      <h3>Create New Project</h3>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Project Title"
          value={formData.title}
          onChange={(e) => setFormData({...formData, title: e.target.value})}
          required
        />
        <textarea
          placeholder="Project Description"
          value={formData.description}
          onChange={(e) => setFormData({...formData, description: e.target.value})}
          rows={3}
        />
        <input
          type="date"
          value={formData.deadline}
          onChange={(e) => setFormData({...formData, deadline: e.target.value})}
        />
        <div className="form-actions">
          <button type="submit" className="btn-primary">Create Project</button>
          <button type="button" className="btn-secondary" onClick={onCancel}>Cancel</button>
        </div>
      </form>
    </div>
  );
};

const ProjectDetails = ({ project, tasks, onTaskUpdate }) => {
  const [showTaskForm, setShowTaskForm] = useState(false);

  const updateTaskStatus = async (taskId, status) => {
    try {
      await axios.put(`${API}/tasks/${taskId}`, { status });
      onTaskUpdate();
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  return (
    <div className="project-details">
      <div className="project-header">
        <h2>{project.title}</h2>
        <span className={`status ${project.status}`}>{project.status}</span>
      </div>
      
      <p>{project.description}</p>
      
      {project.deadline && (
        <p>Deadline: {new Date(project.deadline).toLocaleDateString()}</p>
      )}

      <div className="tasks-section">
        <div className="tasks-header">
          <h3>Tasks</h3>
          <button 
            className="btn-primary"
            onClick={() => setShowTaskForm(!showTaskForm)}
          >
            Add Task
          </button>
        </div>

        {showTaskForm && (
          <TaskCreateForm 
            projectId={project.id} 
            onSuccess={() => {
              onTaskUpdate();
              setShowTaskForm(false);
            }}
            onCancel={() => setShowTaskForm(false)}
          />
        )}

        <div className="kanban-board">
          <div className="kanban-column">
            <h4>To Do</h4>
            {tasks.filter(task => task.status === 'todo').map(task => (
              <TaskCard 
                key={task.id} 
                task={task} 
                onStatusChange={updateTaskStatus}
              />
            ))}
          </div>
          
          <div className="kanban-column">
            <h4>In Progress</h4>
            {tasks.filter(task => task.status === 'in_progress').map(task => (
              <TaskCard 
                key={task.id} 
                task={task} 
                onStatusChange={updateTaskStatus}
              />
            ))}
          </div>
          
          <div className="kanban-column">
            <h4>Completed</h4>
            {tasks.filter(task => task.status === 'completed').map(task => (
              <TaskCard 
                key={task.id} 
                task={task} 
                onStatusChange={updateTaskStatus}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const TaskCreateForm = ({ projectId, onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    due_date: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/projects/${projectId}/tasks`, {
        ...formData,
        due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null
      });
      onSuccess();
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  return (
    <div className="create-form">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Task Title"
          value={formData.title}
          onChange={(e) => setFormData({...formData, title: e.target.value})}
          required
        />
        <textarea
          placeholder="Task Description"
          value={formData.description}
          onChange={(e) => setFormData({...formData, description: e.target.value})}
          rows={2}
        />
        <select
          value={formData.priority}
          onChange={(e) => setFormData({...formData, priority: e.target.value})}
        >
          <option value="low">Low Priority</option>
          <option value="medium">Medium Priority</option>
          <option value="high">High Priority</option>
        </select>
        <input
          type="date"
          value={formData.due_date}
          onChange={(e) => setFormData({...formData, due_date: e.target.value})}
        />
        <div className="form-actions">
          <button type="submit" className="btn-primary">Add Task</button>
          <button type="button" className="btn-secondary" onClick={onCancel}>Cancel</button>
        </div>
      </form>
    </div>
  );
};

const TaskCard = ({ task, onStatusChange }) => {
  return (
    <div className={`task-card priority-${task.priority}`}>
      <h5>{task.title}</h5>
      {task.description && <p>{task.description}</p>}
      <div className="task-actions">
        {task.status !== 'completed' && (
          <button 
            className="btn-small"
            onClick={() => onStatusChange(task.id, task.status === 'todo' ? 'in_progress' : 'completed')}
          >
            {task.status === 'todo' ? 'Start' : 'Complete'}
          </button>
        )}
      </div>
    </div>
  );
};

const Preparation = () => {
  const [activeTab, setActiveTab] = useState('aptitude');
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [score, setScore] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const [loading, setLoading] = useState(false);

  const startQuiz = async (category) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/quiz/questions/${category}`);
      setQuestions(response.data);
      setCurrentQuestionIndex(0);
      setScore(0);
      setShowResults(false);
      setSelectedAnswer('');
    } catch (error) {
      console.error('Failed to fetch questions:', error);
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = () => {
    const currentQuestion = questions[currentQuestionIndex];
    const isCorrect = selectedAnswer === currentQuestion.correct_answer;
    
    if (isCorrect) {
      setScore(score + 1);
    }

    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setSelectedAnswer('');
    } else {
      setShowResults(true);
    }
  };

  const resetQuiz = () => {
    setQuestions([]);
    setCurrentQuestionIndex(0);
    setSelectedAnswer('');
    setScore(0);
    setShowResults(false);
  };

  const currentQuestion = questions[currentQuestionIndex];

  return (
    <div className="preparation">
      <h1>Placement Preparation</h1>
      
      <div className="prep-tabs">
        <button 
          className={activeTab === 'aptitude' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('aptitude')}
        >
          Aptitude Test
        </button>
        <button 
          className={activeTab === 'coding' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('coding')}
        >
          Coding Practice
        </button>
      </div>

      <div className="prep-content">
        {questions.length === 0 && !showResults ? (
          <div className="quiz-start">
            <h2>{activeTab === 'aptitude' ? 'Aptitude Test' : 'Coding Practice'}</h2>
            <p>
              {activeTab === 'aptitude' 
                ? 'Test your quantitative, logical, and verbal reasoning skills'
                : 'Practice coding problems in Python, Java, and C++'
              }
            </p>
            <button 
              className="btn-primary"
              onClick={() => startQuiz(activeTab)}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Start Quiz'}
            </button>
          </div>
        ) : showResults ? (
          <div className="quiz-results">
            <h2>Quiz Complete!</h2>
            <p>Your Score: {score} / {questions.length}</p>
            <p>Percentage: {Math.round((score / questions.length) * 100)}%</p>
            <div className="results-actions">
              <button className="btn-primary" onClick={() => startQuiz(activeTab)}>Try Again</button>
              <button className="btn-secondary" onClick={resetQuiz}>Back to Menu</button>
            </div>
          </div>
        ) : (
          <div className="quiz-question">
            <div className="question-header">
              <span>Question {currentQuestionIndex + 1} of {questions.length}</span>
              <span>Score: {score}</span>
            </div>
            
            <h3>{currentQuestion?.question}</h3>
            
            {activeTab === 'aptitude' ? (
              <div className="question-options">
                {currentQuestion?.options?.map((option, index) => (
                  <label key={index} className="option-label">
                    <input
                      type="radio"
                      value={option}
                      checked={selectedAnswer === option}
                      onChange={(e) => setSelectedAnswer(e.target.value)}
                    />
                    {option}
                  </label>
                ))}
              </div>
            ) : (
              <div className="coding-question">
                <div className="question-info">
                  <p>Language: {currentQuestion?.language}</p>
                  <p>Difficulty: {currentQuestion?.difficulty}</p>
                </div>
                <textarea
                  placeholder="Write your solution here..."
                  value={selectedAnswer}
                  onChange={(e) => setSelectedAnswer(e.target.value)}
                  rows={10}
                />
                {currentQuestion?.sample_answer && (
                  <details className="sample-answer">
                    <summary>View Sample Answer</summary>
                    <pre>{currentQuestion.sample_answer}</pre>
                  </details>
                )}
              </div>
            )}
            
            <button 
              className="btn-primary"
              onClick={submitAnswer}
              disabled={!selectedAnswer.trim()}
            >
              {currentQuestionIndex < questions.length - 1 ? 'Next Question' : 'Finish Quiz'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const Interviews = () => {
  const [interviewType, setInterviewType] = useState('hr');
  const [session, setSession] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answer, setAnswer] = useState('');
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(false);

  const startInterview = async (type) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/interview/session?interview_type=${type}`);
      setSession(response.data);
      setCurrentQuestionIndex(0);
      setResponses([]);
      setAnswer('');
    } catch (error) {
      console.error('Failed to start interview:', error);
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    const currentQuestion = session.questions[currentQuestionIndex];
    const response = {
      question_id: currentQuestion.id,
      question: currentQuestion.question,
      answer: answer
    };

    try {
      await axios.post(`${API}/interview/${session.id}/response`, response);
      setResponses([...responses, response]);
      
      if (currentQuestionIndex < session.questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
        setAnswer('');
      } else {
        // Interview completed
        setSession({ ...session, completed: true });
      }
    } catch (error) {
      console.error('Failed to submit response:', error);
    }
  };

  const resetInterview = () => {
    setSession(null);
    setCurrentQuestionIndex(0);
    setAnswer('');
    setResponses([]);
  };

  const currentQuestion = session?.questions[currentQuestionIndex];

  return (
    <div className="interviews">
      <h1>Mock Interviews</h1>
      
      {!session ? (
        <div className="interview-types">
          <div className="interview-card">
            <h3>HR Interview</h3>
            <p>Practice common HR questions and improve your communication skills</p>
            <button 
              className="btn-primary"
              onClick={() => startInterview('hr')}
              disabled={loading}
            >
              Start HR Interview
            </button>
          </div>
          
          <div className="interview-card">
            <h3>Technical Interview</h3>
            <p>Test your technical knowledge and problem-solving abilities</p>
            <button 
              className="btn-primary"
              onClick={() => startInterview('technical')}
              disabled={loading}
            >
              Start Technical Interview
            </button>
          </div>
        </div>
      ) : session.completed ? (
        <div className="interview-results">
          <h2>Interview Complete!</h2>
          <p>Thank you for completing the {session.type} interview.</p>
          <div className="interview-summary">
            <h3>Your Responses:</h3>
            {responses.map((response, index) => (
              <div key={index} className="response-summary">
                <h4>Q{index + 1}: {response.question}</h4>
                <p>{response.answer}</p>
              </div>
            ))}
          </div>
          <div className="interview-actions">
            <button className="btn-primary" onClick={() => startInterview(session.type)}>
              Try Again
            </button>
            <button className="btn-secondary" onClick={resetInterview}>
              Back to Menu
            </button>
          </div>
        </div>
      ) : (
        <div className="interview-question">
          <div className="interview-header">
            <h2>{session.type === 'hr' ? 'HR' : 'Technical'} Interview</h2>
            <span>Question {currentQuestionIndex + 1} of {session.questions.length}</span>
          </div>
          
          <div className="question-content">
            <h3>{currentQuestion?.question}</h3>
            <textarea
              placeholder="Type your answer here..."
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={6}
            />
          </div>
          
          <div className="interview-actions">
            <button 
              className="btn-primary"
              onClick={submitAnswer}
              disabled={!answer.trim()}
            >
              {currentQuestionIndex < session.questions.length - 1 ? 'Next Question' : 'Complete Interview'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const Profile = () => {
  const { user } = useAuth();
  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    college: user?.college || '',
    branch: user?.branch || '',
    year: user?.year || '',
    skills: '',
    experience: '',
    projects: ''
  });
  const [linkedinData, setLinkedinData] = useState('');
  const [message, setMessage] = useState('');

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/profile`, profileData);
      setMessage('Profile updated successfully!');
    } catch (error) {
      console.error('Failed to update profile:', error);
      setMessage('Failed to update profile');
    }
  };

  const handleLinkedinImport = async () => {
    if (!linkedinData.trim()) return;
    
    try {
      const parsedData = JSON.parse(linkedinData);
      await axios.post(`${API}/profile/linkedin`, parsedData);
      setMessage('LinkedIn data imported successfully!');
      setLinkedinData('');
    } catch (error) {
      console.error('Failed to import LinkedIn data:', error);
      setMessage('Failed to import LinkedIn data. Please check the format.');
    }
  };

  const generateSampleLinkedinData = () => {
    const sampleData = {
      headline: "Final Year Engineering Student",
      summary: "Passionate about technology and innovation",
      skills: ["JavaScript", "Python", "React", "Node.js"],
      education: [{
        institution: profileData.college,
        degree: "B.Tech in " + profileData.branch,
        year: profileData.year
      }],
      projects: [{
        title: "Sample Project",
        description: "Description of your project",
        technologies: ["React", "Node.js", "MongoDB"]
      }]
    };
    
    setLinkedinData(JSON.stringify(sampleData, null, 2));
  };

  return (
    <div className="profile">
      <h1>Profile Management</h1>
      
      {message && (
        <div className={`message ${message.includes('success') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}
      
      <div className="profile-sections">
        <div className="profile-section">
          <h2>Personal Information</h2>
          <form onSubmit={handleProfileUpdate}>
            <input
              type="text"
              placeholder="Full Name"
              value={profileData.name}
              onChange={(e) => setProfileData({...profileData, name: e.target.value})}
            />
            <input
              type="text"
              placeholder="College Name"
              value={profileData.college}
              onChange={(e) => setProfileData({...profileData, college: e.target.value})}
            />
            <input
              type="text"
              placeholder="Branch"
              value={profileData.branch}
              onChange={(e) => setProfileData({...profileData, branch: e.target.value})}
            />
            <input
              type="text"
              placeholder="Year"
              value={profileData.year}
              onChange={(e) => setProfileData({...profileData, year: e.target.value})}
            />
            <textarea
              placeholder="Skills (comma separated)"
              value={profileData.skills}
              onChange={(e) => setProfileData({...profileData, skills: e.target.value})}
              rows={3}
            />
            <button type="submit" className="btn-primary">Update Profile</button>
          </form>
        </div>
        
        <div className="profile-section">
          <h2>LinkedIn Integration</h2>
          <p>Import your LinkedIn data to auto-generate your resume.</p>
          <div className="linkedin-import">
            <button 
              className="btn-secondary"
              onClick={generateSampleLinkedinData}
            >
              Generate Sample Data
            </button>
            <textarea
              placeholder="Paste your LinkedIn data as JSON here..."
              value={linkedinData}
              onChange={(e) => setLinkedinData(e.target.value)}
              rows={10}
            />
            <button 
              className="btn-primary"
              onClick={handleLinkedinImport}
              disabled={!linkedinData.trim()}
            >
              Import LinkedIn Data
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const App = () => {
  const { user, loading } = useAuth();
  const [currentView, setCurrentView] = useState('dashboard');

  if (loading) return <LoadingSpinner />;

  if (!user) {
    return (
      <div className="App">
        <AuthForm />
      </div>
    );
  }

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'projects':
        return <Projects />;
      case 'preparation':
        return <Preparation />;
      case 'interviews':
        return <Interviews />;
      case 'companies':
        return <Companies />;
      case 'profile':
        return <Profile />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="App">
      <Navigation currentView={currentView} setCurrentView={setCurrentView} />
      <main className="main-content">
        {renderView()}
      </main>
    </div>
  );
};

function AppWrapper() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

export default AppWrapper;