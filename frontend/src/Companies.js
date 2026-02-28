import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Companies = ({ user }) => {
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [showMatching, setShowMatching] = useState(false);
  const [matchingResults, setMatchingResults] = useState(null);
  const [linkedinData, setLinkedinData] = useState('');
  const [showEditProfile, setShowEditProfile] = useState(false);
  const [loading, setLoading] = useState(true);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [youtubeRecommendations, setYoutubeRecommendations] = useState(null);
  const [showLearningResources, setShowLearningResources] = useState(false);
  const [myApplications, setMyApplications] = useState([]);
  const [showApplications, setShowApplications] = useState(false);
  const [showResumeEvaluator, setShowResumeEvaluator] = useState(false);
  const [resumeEvaluation, setResumeEvaluation] = useState(null);
  const [resumeEvaluating, setResumeEvaluating] = useState(false);

  useEffect(() => {
    fetchCompanies();
    fetchUserMatches();
    fetchYoutubeRecommendations();
    fetchMyApplications();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await axios.get(`${API}/companies`);
      setCompanies(response.data);
    } catch (error) {
      console.error('Failed to fetch companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserMatches = async () => {
    try {
      const response = await axios.get(`${API}/companies/my-matches`);
      if (response.data.results) {
        setMatchingResults(response.data.results);
      }
    } catch (error) {
      console.log('No previous matches found');
    }
  };

  const fetchYoutubeRecommendations = async () => {
    try {
      const response = await axios.get(`${API}/learning/youtube-recommendations`);
      setYoutubeRecommendations(response.data);
    } catch (error) {
      console.log('Failed to fetch YouTube recommendations');
    }
  };

  const fetchMyApplications = async () => {
    try {
      const response = await axios.get(`${API}/applications/my-applications`);
      setMyApplications(response.data.applications);
    } catch (error) {
      console.log('Failed to fetch applications');
    }
  };

  const handleJobApplication = async (company, jobLink, platform) => {
    try {
      const applicationData = {
        position: "Software Developer",
        application_link: jobLink,
        platform: platform,
        notes: `Applied through ${platform}`
      };
      
      await axios.post(`${API}/companies/${company.id}/apply`, applicationData);
      
      // Open job link in new tab
      window.open(jobLink, '_blank');
      
      // Refresh applications
      fetchMyApplications();
      
      alert(`Application tracked! Opening ${platform} job page...`);
    } catch (error) {
      console.error('Failed to track application:', error);
      // Still open the job link even if tracking fails
      window.open(jobLink, '_blank');
    }
  };

  const handleResumeUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type)) {
      alert('Please upload only PDF, DOC, or DOCX files');
      return;
    }

    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('File size must be less than 5MB');
      return;
    }

    setResumeEvaluating(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/resume/evaluate`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResumeEvaluation(response.data.analysis);
    } catch (error) {
      console.error('Failed to evaluate resume:', error);
      alert('Failed to evaluate resume. Please try again.');
    } finally {
      setResumeEvaluating(false);
      // Reset file input
      event.target.value = '';
    }
  };

  const analyzeProfile = async () => {
    if (!linkedinData.trim()) {
      alert('Please generate your profile first');
      return;
    }

    setAnalysisLoading(true);
    try {
      const parsedData = JSON.parse(linkedinData);
      const response = await axios.post(`${API}/companies/match-profile`, parsedData);
      setMatchingResults(response.data.results);
      setShowMatching(false);
      setLinkedinData('');
    } catch (error) {
      console.error('Failed to analyze profile:', error);
      alert('Failed to analyze profile. Please try again.');
    } finally {
      setAnalysisLoading(false);
    }
  };

  const generatePersonalizedProfile = () => {
    // Branch-specific skills mapping
    const branchSkills = {
      "Computer Science": ["JavaScript", "Python", "Java", "React", "Node.js", "Machine Learning", "Data Structures", "Algorithms", "MongoDB", "SQL"],
      "Information Technology": ["JavaScript", "Python", "React", "Node.js", "Database Management", "System Administration", "Network Security", "Cloud Computing"],
      "Electronics": ["C++", "Python", "MATLAB", "Embedded Systems", "IoT", "Signal Processing", "PCB Design", "Microcontrollers", "VLSI"],
      "Mechanical": ["CAD", "SolidWorks", "AutoCAD", "Python", "MATLAB", "Thermodynamics", "Fluid Mechanics", "Manufacturing", "3D Modeling"],
      "Electrical": ["MATLAB", "Python", "C++", "Power Systems", "Control Systems", "Embedded Systems", "PLC Programming", "Circuit Design"],
      "Civil": ["AutoCAD", "STAAD Pro", "Python", "Project Management", "Structural Design", "Construction Management", "GIS", "Surveying"]
    };

    // Branch-specific project ideas
    const branchProjects = {
      "Computer Science": [
        { title: "AI-Powered Student Management System", technologies: ["React", "Node.js", "MongoDB", "Machine Learning"] },
        { title: "Real-time Chat Application", technologies: ["JavaScript", "Socket.io", "React", "Express"] }
      ],
      "Information Technology": [
        { title: "Cloud-based File Storage System", technologies: ["React", "Node.js", "AWS", "MongoDB"] },
        { title: "Network Security Monitor", technologies: ["Python", "Flask", "Network Tools", "Dashboard"] }
      ],
      "Electronics": [
        { title: "IoT Home Automation System", technologies: ["Arduino", "Raspberry Pi", "Sensors", "Mobile App"] },
        { title: "Smart Health Monitoring Device", technologies: ["Embedded C", "Sensors", "Bluetooth", "Android"] }
      ],
      "Mechanical": [
        { title: "Automated Manufacturing System", technologies: ["SolidWorks", "PLC", "Sensors", "Control Systems"] },
        { title: "Solar Panel Tracking System", technologies: ["CAD Design", "Arduino", "Servo Motors", "Programming"] }
      ],
      "Electrical": [
        { title: "Smart Grid Management System", technologies: ["MATLAB", "Power Systems", "IoT", "Data Analytics"] },
        { title: "Renewable Energy Controller", technologies: ["Embedded Systems", "Power Electronics", "SCADA"] }
      ],
      "Civil": [
        { title: "Smart City Planning System", technologies: ["GIS", "AutoCAD", "Data Analysis", "3D Modeling"] },
        { title: "Earthquake Resistant Building Design", technologies: ["STAAD Pro", "Structural Analysis", "CAD"] }
      ]
    };

    const getRandomLocation = () => {
      const locations = ["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Pune", "Chennai", "Kolkata", "Ahmedabad"];
      return locations[Math.floor(Math.random() * locations.length)];
    };

    const generatePersonalizedSummary = (branch, year) => {
      const yearText = year === "Final Year" ? "final year" : year?.toLowerCase() || "final year";
      const branchSummaries = {
        "Computer Science": `Passionate ${yearText} Computer Science student with strong foundation in software development, algorithms, and emerging technologies. Experienced in full-stack development and machine learning. Eager to contribute to innovative projects and grow in a dynamic tech environment.`,
        "Information Technology": `Dedicated ${yearText} IT student with expertise in system administration, network security, and database management. Strong problem-solving skills and experience in cloud technologies. Looking for opportunities to apply technical knowledge in real-world IT solutions.`,
        "Electronics": `Innovative ${yearText} Electronics student specializing in embedded systems, IoT, and signal processing. Hands-on experience with microcontrollers and circuit design. Passionate about creating smart solutions that bridge hardware and software.`,
        "Mechanical": `Driven ${yearText} Mechanical Engineering student with expertise in design, manufacturing, and automation. Proficient in CAD software and modern manufacturing techniques. Interested in sustainable engineering and Industry 4.0 technologies.`,
        "Electrical": `Ambitious ${yearText} Electrical Engineering student focused on power systems, control engineering, and renewable energy. Experience with embedded systems and automation. Committed to developing efficient and sustainable electrical solutions.`,
        "Civil": `Motivated ${yearText} Civil Engineering student with knowledge in structural design, construction management, and smart city planning. Skilled in modern design software and project management. Passionate about sustainable infrastructure development.`
      };
      return branchSummaries[branch] || branchSummaries["Computer Science"];
    };

    const generateExperience = (branch, year) => {
      const isExperienced = year === "Final Year" || year === "4th Year";
      if (!isExperienced) {
        return [
          {
            title: "Technical Team Member",
            company: "College Technical Society",
            duration: "6 months",
            description: `Active member contributing to technical projects and organizing workshops. Gained hands-on experience in ${branch.toLowerCase()} concepts and teamwork.`
          }
        ];
      }

      const experiences = {
        "Computer Science": [
          {
            title: "Software Development Intern",
            company: "Tech Startup",
            duration: "3 months",
            description: "Developed web applications using React and Node.js. Worked on machine learning projects using Python and TensorFlow. Collaborated with cross-functional teams to deliver user-friendly solutions."
          }
        ],
        "Information Technology": [
          {
            title: "IT Support Intern",
            company: "Local IT Company",
            duration: "2 months", 
            description: "Provided technical support, managed network systems, and implemented security protocols. Gained experience in cloud services and database administration."
          }
        ],
        "Electronics": [
          {
            title: "Hardware Development Intern",
            company: "Electronics Firm",
            duration: "2 months",
            description: "Assisted in PCB design and testing. Worked on IoT projects and embedded system programming. Gained practical experience in circuit analysis and debugging."
          }
        ]
      };

      return experiences[branch] || experiences["Computer Science"];
    };

    const generateCertifications = (branch) => {
      const certifications = {
        "Computer Science": ["Python Programming", "Machine Learning Basics", "AWS Cloud Practitioner", "React Development"],
        "Information Technology": ["CompTIA Network+", "Cisco CCNA", "Microsoft Azure Fundamentals", "Cybersecurity Basics"],
        "Electronics": ["Arduino Programming", "PCB Design", "IoT Fundamentals", "Embedded C Programming"],
        "Mechanical": ["SolidWorks Certification", "AutoCAD Professional", "Lean Manufacturing", "3D Printing Technology"],
        "Electrical": ["MATLAB Certification", "PLC Programming", "Power System Analysis", "Renewable Energy Systems"],
        "Civil": ["AutoCAD Civil 3D", "STAAD Pro", "Project Management Professional (PMP)", "GIS Fundamentals"]
      };
      return certifications[branch]?.slice(0, 3) || certifications["Computer Science"].slice(0, 3);
    };

    const generateInterests = (branch) => {
      const interests = {
        "Computer Science": ["Artificial Intelligence", "Open Source", "Startups", "Innovation", "Problem Solving"],
        "Information Technology": ["Cybersecurity", "Cloud Computing", "Network Administration", "Technology Trends"],
        "Electronics": ["IoT", "Robotics", "Innovation", "Hardware Design", "Smart Systems"],
        "Mechanical": ["Automation", "Sustainable Engineering", "Manufacturing", "CAD Design", "Innovation"],
        "Electrical": ["Renewable Energy", "Smart Grids", "Automation", "Power Systems", "Green Technology"],
        "Civil": ["Sustainable Construction", "Smart Cities", "Infrastructure", "Project Management", "Green Building"]
      };
      return interests[branch] || interests["Computer Science"];
    };

    const userBranch = user?.branch || "Computer Science";
    const skills = branchSkills[userBranch] || branchSkills["Computer Science"];
    const projects = branchProjects[userBranch] || branchProjects["Computer Science"];

    const personalizedData = {
      name: user?.name || "Engineering Student",
      location: getRandomLocation(),
      headline: `${user?.year || "Final Year"} ${userBranch} Student at ${user?.college || "Engineering College"}`,
      summary: generatePersonalizedSummary(userBranch, user?.year),
      skills: skills.slice(0, 8), // Top 8 skills
      experience: generateExperience(userBranch, user?.year),
      education: [
        {
          institution: user?.college || "Engineering College",
          degree: `B.Tech in ${userBranch}`,
          year: user?.year || "Final Year",
          activities: "Technical Society Member, Project Leader, Academic Excellence"
        }
      ],
      projects: projects,
      certifications: generateCertifications(userBranch),
      interests: generateInterests(userBranch),
      languages: ["English", "Hindi"],
      achievements: [
        "Dean's List for Academic Excellence",
        "Best Project Award in College Tech Fest",
        "Active contributor to open-source projects"
      ]
    };
    
    setLinkedinData(JSON.stringify(personalizedData, null, 2));
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#10b981'; // green
    if (score >= 60) return '#f59e0b'; // orange  
    return '#ef4444'; // red
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Excellent Match';
    if (score >= 60) return 'Good Match';
    return 'Fair Match';
  };

  if (loading) return (
    <div className="loading-container">
      <div className="loading-spinner"></div>
      <p>Loading...</p>
    </div>
  );

  return (
    <div className="companies">
      <div className="companies-header">
        <h1>🎯 Smart Company Matching</h1>
        <div className="header-actions">
          <button 
            className="btn-secondary"
            onClick={() => setShowResumeEvaluator(!showResumeEvaluator)}
          >
            📄 Resume Evaluator
          </button>
          <button 
            className="btn-secondary"
            onClick={() => setShowApplications(!showApplications)}
          >
            📋 My Applications ({myApplications.length})
          </button>
          <button 
            className="btn-secondary"
            onClick={() => setShowLearningResources(!showLearningResources)}
          >
            📚 Learning Resources
          </button>
          {!matchingResults ? (
            <button 
              className="btn-primary"
              onClick={() => setShowMatching(!showMatching)}
            >
              {showMatching ? 'Cancel' : '🚀 Analyze My Profile'}
            </button>
          ) : (
            <div className="matching-status">
              <span>✅ Profile Analyzed - {matchingResults.total_matches} matches found</span>
              <button 
                className="btn-secondary"
                onClick={() => setShowMatching(!showMatching)}
              >
                Update Analysis
              </button>
            </div>
          )}
        </div>
      </div>

      {showMatching && (
        <div className="glass-card matching-interface">
          <h3>🧠 AI-Powered Profile Analysis</h3>
          <p>Generate a personalized profile based on your registration details and get AI-powered company matches.</p>
          
          <div className="linkedin-input">
            <div className="profile-generator">
              <h4>🎯 Smart Profile Generation</h4>
              <p>We'll create a personalized LinkedIn-style profile based on your registration details and branch expertise.</p>
              
              <div className="generator-actions">
                <button 
                  className="btn-primary profile-gen-btn"
                  onClick={generatePersonalizedProfile}
                >
                  🚀 Generate My Profile
                </button>
                <span className="generator-note">
                  Based on: {user?.name} • {user?.branch} • {user?.college}
                </span>
              </div>
            </div>

            {linkedinData && (
              <div className="profile-preview">
                <div className="preview-header">
                  <span>Generated Profile Preview</span>
                  <button 
                    className="btn-small"
                    onClick={() => setShowEditProfile(!showEditProfile)}
                  >
                    {showEditProfile ? 'Hide Editor' : 'Edit Profile'}
                  </button>
                </div>
                
                {showEditProfile ? (
                  <textarea
                    className="linkedin-textarea"
                    value={linkedinData}
                    onChange={(e) => setLinkedinData(e.target.value)}
                    rows={15}
                  />
                ) : (
                  <div className="profile-summary-card">
                    {(() => {
                      try {
                        const profile = JSON.parse(linkedinData);
                        return (
                          <div className="profile-overview">
                            <div className="profile-header-info">
                              <h4>{profile.name}</h4>
                              <p className="profile-headline">{profile.headline}</p>
                              <p className="profile-location">📍 {profile.location}</p>
                            </div>
                            
                            <div className="profile-highlights">
                              <div className="highlight">
                                <span className="highlight-label">🛠️ Skills:</span>
                                <span className="highlight-value">{profile.skills?.slice(0, 4).join(', ')}</span>
                              </div>
                              <div className="highlight">
                                <span className="highlight-label">🎓 Education:</span>
                                <span className="highlight-value">{profile.education?.[0]?.degree}</span>
                              </div>
                              <div className="highlight">
                                <span className="highlight-label">📋 Projects:</span>
                                <span className="highlight-value">{profile.projects?.length || 0} projects</span>
                              </div>
                            </div>
                          </div>
                        );
                      } catch (e) {
                        return <p className="error-text">Profile preview unavailable</p>;
                      }
                    })()}
                  </div>
                )}
              </div>
            )}
            
            <div className="analysis-actions">
              <button 
                className="btn-primary"
                onClick={analyzeProfile}
                disabled={analysisLoading || !linkedinData.trim()}
              >
                {analysisLoading ? '🔍 Analyzing Profile...' : '🎯 Find My Perfect Matches'}
              </button>
              <button 
                className="btn-secondary"
                onClick={() => setShowMatching(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {matchingResults ? (
        <div className="matching-results">
          <div className="results-header">
            <h2>🎯 Your Personalized Company Matches</h2>
            <div className="profile-summary">
              <div className="summary-item">
                <span className="summary-label">Skills:</span>
                <span className="summary-value">{matchingResults.user_profile_summary.skills.slice(0, 5).join(', ')}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Experience:</span>
                <span className="summary-value">{matchingResults.user_profile_summary.experience_count} positions</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Location:</span>
                <span className="summary-value">{matchingResults.user_profile_summary.location || 'Not specified'}</span>
              </div>
            </div>
          </div>

          <div className="matched-companies">
            {matchingResults.matched_companies.map((company, index) => (
              <div key={company.id} className={`company-match-card ${index < 3 ? 'top-match' : ''}`}>
                <div className="match-header">
                  <div className="company-info">
                    <h3>{company.name}</h3>
                    <p className="company-subtitle">{company.industry} • {company.type}</p>
                    {index < 3 && <span className="top-match-badge">🏆 Top Match</span>}
                  </div>
                  <div className="match-score">
                    <div 
                      className="score-circle"
                      style={{ background: `conic-gradient(${getScoreColor(company.match_score.overall)} ${company.match_score.overall}%, #374151 0)` }}
                    >
                      <span className="score-text">{company.match_score.overall}%</span>
                    </div>
                    <span className="score-label" style={{ color: getScoreColor(company.match_score.overall) }}>
                      {getScoreLabel(company.match_score.overall)}
                    </span>
                  </div>
                </div>

                <div className="match-details">
                  <div className="score-breakdown">
                    <div className="score-item">
                      <span>🛠️ Skills</span>
                      <div className="score-bar">
                        <div 
                          className="score-fill" 
                          style={{ 
                            width: `${company.match_score.skill_match}%`,
                            backgroundColor: getScoreColor(company.match_score.skill_match)
                          }}
                        ></div>
                        <span>{company.match_score.skill_match}%</span>
                      </div>
                    </div>
                    
                    <div className="score-item">
                      <span>🎨 Culture</span>
                      <div className="score-bar">
                        <div 
                          className="score-fill" 
                          style={{ 
                            width: `${company.match_score.culture_match}%`,
                            backgroundColor: getScoreColor(company.match_score.culture_match)
                          }}
                        ></div>
                        <span>{company.match_score.culture_match}%</span>
                      </div>
                    </div>
                    
                    <div className="score-item">
                      <span>📍 Location</span>
                      <div className="score-bar">
                        <div 
                          className="score-fill" 
                          style={{ 
                            width: `${company.match_score.location_match}%`,
                            backgroundColor: getScoreColor(company.match_score.location_match)
                          }}
                        ></div>
                        <span>{company.match_score.location_match}%</span>
                      </div>
                    </div>
                  </div>

                  <div className="match-highlights">
                    <h4>🎯 Why This is a Great Match:</h4>
                    <ul>
                      {company.match_explanations.map((explanation, idx) => (
                        <li key={idx}>{explanation}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="matching-skills">
                    <h4>💡 Matching Skills:</h4>
                    <div className="skills-tags">
                      {company.matching_skills.slice(0, 6).map((skill, idx) => (
                        <span key={idx} className="skill-tag">{skill}</span>
                      ))}
                    </div>
                  </div>

                  <div className="company-highlights">
                    <div className="highlight-row">
                      <div className="highlight-item">
                        <span className="highlight-label">💰 Salary</span>
                        <span className="highlight-value">{company.salary_range}</span>
                      </div>
                      <div className="highlight-item">
                        <span className="highlight-label">📍 Locations</span>
                        <span className="highlight-value">{company.locations.join(', ')}</span>
                      </div>
                      <div className="highlight-item">
                        <span className="highlight-label">🏢 Work Style</span>
                        <span className="highlight-value">{company.work_environment}</span>
                      </div>
                    </div>
                  </div>

                  <div className="recommended-roles">
                    <h4>🚀 Recommended Roles:</h4>
                    <div className="roles-tags">
                      {company.recommended_roles.map((role, idx) => (
                        <span key={idx} className="role-tag">{role}</span>
                      ))}
                    </div>
                  </div>

                  <div className="card-actions">
                    <button 
                      className="btn-primary"
                      onClick={() => setSelectedCompany(company)}
                    >
                      View Full Details
                    </button>
                    
                    {company.job_links && (
                      <div className="job-application-buttons">
                        <button 
                          className="btn-job-apply linkedin"
                          onClick={() => handleJobApplication(company, company.job_links.linkedin, 'LinkedIn')}
                        >
                          Apply on LinkedIn
                        </button>
                        <button 
                          className="btn-job-apply indeed"
                          onClick={() => handleJobApplication(company, company.job_links.indeed, 'Indeed')}
                        >
                          Apply on Indeed
                        </button>
                        <button 
                          className="btn-job-apply naukri"
                          onClick={() => handleJobApplication(company, company.job_links.naukri, 'Naukri')}
                        >
                          Apply on Naukri
                        </button>
                      </div>
                    )}
                    
                    <button className="btn-secondary">
                      Save for Later
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="no-matches">
          <div className="companies-grid">
            {companies.map(company => (
              <div key={company.id} className="company-card">
                <h3>{company.name}</h3>
                <p>{company.industry}</p>
                <p className="salary-range">{company.salary_range}</p>
                <p>Locations: {company.locations.join(', ')}</p>
                <button 
                  className="btn-primary"
                  onClick={() => setSelectedCompany(company)}
                >
                  View Details
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {showResumeEvaluator && (
        <div className="glass-card resume-evaluator">
          <h3>📄 AI-Powered Resume Evaluator</h3>
          <p>Upload your resume to get comprehensive AI-powered analysis and scoring for FREE!</p>
          
          <div className="upload-section">
            <div className="upload-area">
              <input
                type="file"
                id="resume-upload"
                accept=".pdf,.doc,.docx"
                onChange={handleResumeUpload}
                disabled={resumeEvaluating}
                style={{ display: 'none' }}
              />
              <label htmlFor="resume-upload" className="upload-label">
                <div className="upload-content">
                  <span className="upload-icon">📎</span>
                  <h4>Upload Your Resume</h4>
                  <p>Supported formats: PDF, DOC, DOCX (Max 5MB)</p>
                  <button className="btn-primary" disabled={resumeEvaluating}>
                    {resumeEvaluating ? 'Evaluating...' : 'Choose File'}
                  </button>
                </div>
              </label>
            </div>
          </div>

          {resumeEvaluation && (
            <div className="evaluation-results">
              <div className="evaluation-header">
                <h3>📊 Resume Evaluation Results</h3>
                <div className="overall-score">
                  <div 
                    className="score-circle-large"
                    style={{ 
                      background: `conic-gradient(${getScoreColor(resumeEvaluation.overall_score)} ${resumeEvaluation.overall_score}%, #374151 0)` 
                    }}
                  >
                    <span className="score-text-large">{resumeEvaluation.overall_score}%</span>
                  </div>
                  <span className="overall-label">Overall Score</span>
                </div>
              </div>

              <div className="section-scores">
                <h4>📈 Section-wise Analysis</h4>
                <div className="scores-grid">
                  {Object.entries(resumeEvaluation.section_scores).map(([section, score]) => (
                    <div key={section} className="score-section">
                      <div className="section-info">
                        <span className="section-name">{section.replace('_', ' ').toUpperCase()}</span>
                        <span className="section-score" style={{ color: getScoreColor(score) }}>
                          {score}%
                        </span>
                      </div>
                      <div className="section-bar">
                        <div 
                          className="section-fill"
                          style={{ 
                            width: `${score}%`,
                            backgroundColor: getScoreColor(score)
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="feedback-sections">
                <div className="feedback-grid">
                  <div className="feedback-section strengths">
                    <h4>💪 Strengths</h4>
                    <ul>
                      {resumeEvaluation.strengths.map((strength, index) => (
                        <li key={index}>{strength}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="feedback-section improvements">
                    <h4>🎯 Areas for Improvement</h4>
                    <ul>
                      {resumeEvaluation.improvements.map((improvement, index) => (
                        <li key={index}>{improvement}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {resumeEvaluation.missing_sections.length > 0 && (
                  <div className="feedback-section missing">
                    <h4>❗ Missing Sections</h4>
                    <div className="missing-tags">
                      {resumeEvaluation.missing_sections.map((section, index) => (
                        <span key={index} className="missing-tag">{section}</span>
                      ))}
                    </div>
                  </div>
                )}

                {resumeEvaluation.recommended_additions.length > 0 && (
                  <div className="feedback-section recommendations">
                    <h4>💡 Recommended Additions</h4>
                    <div className="recommendation-tags">
                      {resumeEvaluation.recommended_additions.map((addition, index) => (
                        <span key={index} className="recommendation-tag">{addition}</span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="ats-score">
                  <h4>🤖 ATS Compatibility Score</h4>
                  <div className="ats-info">
                    <div className="ats-score-display">
                      <span className="ats-percentage" style={{ color: getScoreColor(resumeEvaluation.ats_score) }}>
                        {resumeEvaluation.ats_score}%
                      </span>
                      <span className="ats-label">ATS Friendly</span>
                    </div>
                    <p className="ats-description">
                      {resumeEvaluation.ats_score >= 80 
                        ? "Excellent! Your resume is highly compatible with Applicant Tracking Systems."
                        : resumeEvaluation.ats_score >= 60
                        ? "Good ATS compatibility. Minor improvements recommended."
                        : "Needs improvement for better ATS compatibility."
                      }
                    </p>
                  </div>
                </div>
              </div>

              <div className="evaluation-actions">
                <button 
                  className="btn-primary"
                  onClick={() => setResumeEvaluation(null)}
                >
                  Evaluate Another Resume
                </button>
                <button className="btn-secondary">
                  Download Detailed Report
                </button>
              </div>
            </div>
          )}
        </div>
      )}
        <div className="glass-card applications-section">
          <h3>📋 My Job Applications</h3>
          {myApplications.length > 0 ? (
            <div className="applications-list">
              {myApplications.map((app, index) => (
                <div key={app.id} className="application-item">
                  <div className="application-header">
                    <h4>{app.position} at {app.company_name}</h4>
                    <span className={`status-badge ${app.status.toLowerCase()}`}>
                      {app.status}
                    </span>
                  </div>
                  <div className="application-details">
                    <p>Platform: {app.platform}</p>
                    <p>Applied: {new Date(app.applied_date).toLocaleDateString()}</p>
                    {app.notes && <p>Notes: {app.notes}</p>}
                    {app.application_link && (
                      <a href={app.application_link} target="_blank" rel="noopener noreferrer" className="btn-small">
                        View Application
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-applications">
              <p>No applications yet. Start applying to companies to track them here!</p>
            </div>
          )}
        </div>
      )}

      {showLearningResources && youtubeRecommendations && (
        <div className="glass-card learning-resources">
          <h3>📚 Personalized Learning Resources</h3>
          <div className="user-analysis">
            <p><strong>Your Branch:</strong> {youtubeRecommendations.user_profile.branch}</p>
            <p><strong>Skills:</strong> {youtubeRecommendations.user_profile.skills.join(', ')}</p>
            {youtubeRecommendations.user_profile.identified_weak_areas.length > 0 && (
              <p><strong>Areas for Improvement:</strong> {youtubeRecommendations.user_profile.identified_weak_areas.join(', ')}</p>
            )}
          </div>
          
          <div className="recommendations-grid">
            {youtubeRecommendations.recommendations.map((category, index) => (
              <div key={index} className={`recommendation-category ${category.priority}`}>
                <h4>{category.category}</h4>
                <div className="resources-list">
                  {category.resources.map((resource, resIndex) => (
                    <div key={resIndex} className="resource-item">
                      <a 
                        href={resource.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="resource-link"
                      >
                        <span className="resource-title">{resource.title || resource.name}</span>
                        {resource.duration && <span className="resource-duration">{resource.duration}</span>}
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedCompany && (
        <CompanyDetailsModal 
          company={selectedCompany} 
          onClose={() => setSelectedCompany(null)} 
        />
      )}
    </div>
  );
};

const CompanyDetailsModal = ({ company, onClose }) => {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content company-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{company.name}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          <div className="company-overview">
            <p className="company-description">{company.description}</p>
            
            <div className="company-stats">
              <div className="stat-item">
                <span className="stat-label">Industry:</span>
                <span className="stat-value">{company.industry}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Company Size:</span>
                <span className="stat-value">{company.size} employees</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Founded:</span>
                <span className="stat-value">{company.founded_year}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Funding:</span>
                <span className="stat-value">{company.funding_stage}</span>
              </div>
            </div>
          </div>

          <div className="details-grid">
            <div className="detail-section">
              <h3>🛠️ Tech Stack</h3>
              <div className="tech-tags">
                {company.tech_stack.map((tech, idx) => (
                  <span key={idx} className="tech-tag">{tech}</span>
                ))}
              </div>
            </div>

            <div className="detail-section">
              <h3>💼 Benefits</h3>
              <ul>
                {company.benefits.map((benefit, idx) => (
                  <li key={idx}>{benefit}</li>
                ))}
              </ul>
            </div>

            <div className="detail-section">
              <h3>🎯 Company Culture</h3>
              <div className="culture-tags">
                {company.culture.map((item, idx) => (
                  <span key={idx} className="culture-tag">{item}</span>
                ))}
              </div>
            </div>

            <div className="detail-section">
              <h3>📋 Hiring Process</h3>
              <ol>
                {company.hiring_process.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            </div>

            <div className="detail-section">
              <h3>📈 Growth Opportunities</h3>
              <ul>
                {company.growth_opportunities.map((opportunity, idx) => (
                  <li key={idx}>{opportunity}</li>
                ))}
              </ul>
            </div>

            <div className="detail-section">
              <h3>📍 Office Locations</h3>
              <ul>
                {company.locations.map((location, idx) => (
                  <li key={idx}>{location}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="salary-info">
            <h3>💰 Compensation</h3>
            <div className="salary-highlight">
              <span className="salary-amount">{company.salary_range}</span>
              <span className="work-style">• {company.work_environment} Work</span>
              {company.remote_friendly && <span className="remote-badge">🏠 Remote Friendly</span>}
            </div>
          </div>
        </div>

        <div className="modal-actions">
          <button className="btn-primary">Apply Now</button>
          <button className="btn-secondary">Save for Later</button>
          <button className="btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
};

export default Companies;