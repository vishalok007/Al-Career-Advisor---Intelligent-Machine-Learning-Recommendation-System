JOB_REQUIRED_SKILLS = {
    #AI & Data Science
    "Data Scientist": [
        "Python", "Machine Learning", "Statistics", "Pandas", "NumPy",
        "Scikit-learn", "SQL", "Jupyter", "R",
        "Deep Learning", "PyTorch", "TensorFlow",
    ],
    "Machine Learning Engineer": [
        "Python", "Machine Learning", "Deep Learning", "PyTorch",
        "TensorFlow", "Scikit-learn", "MLOps", "Statistics", "Docker",
        "Kubernetes", "AWS",
    ],
    "AI Engineer": [
        "Python", "Machine Learning", "Deep Learning", "PyTorch",
        "TensorFlow", "Artificial Intelligence", "Computer Vision", "NLP",
        "Statistics", "MLOps",
    ],
    "Artificial Intelligence Engineer": [
        "Python", "Artificial Intelligence", "Machine Learning",
        "Deep Learning", "Statistics", "Pandas", "NumPy",
    ],
    "Data Analyst": [
        "SQL", "Python", "Statistics", "Reporting", "Data Analysis",
        "R", "Pandas", "Database", "Problem Solving", "Analysis",
        "Tableau", "Excel",
    ],
    "Business Intelligence Analyst": [
        "SQL", "Reporting", "Statistics", "Data Analysis", "Database",
        "Analysis", "Tableau", "Business Intelligence", "Problem Solving",
        "Management",
    ],
    "Data Engineer": [
        "SQL", "Python", "Database", "Pandas", "Data Structures",
        "Statistics", "Analysis", "ETL", "MySQL", "Problem Solving",
    ],
    "Big Data Engineer": [
        "Python", "SQL", "Big Data", "Hadoop", "Spark", "AWS",
        "Database", "Pandas", "Cloud", "Statistics", "Docker",
    ],
    "AI Research Scientist": [
        "Python", "Machine Learning", "Deep Learning", "PyTorch",
        "TensorFlow", "Statistics", "Artificial Intelligence", "R",
    ],
    "Computer Vision Engineer": [
        "Python", "Computer Vision", "Deep Learning", "PyTorch",
        "TensorFlow", "Machine Learning", "Artificial Intelligence",
    ],
    "NLP Engineer": [
        "Python", "NLP", "Machine Learning", "Deep Learning",
        "Artificial Intelligence", "PyTorch", "TensorFlow",
    ],
    "Deep Learning Engineer": [
        "Python", "Deep Learning", "Machine Learning", "PyTorch",
        "TensorFlow", "Statistics", "Artificial Intelligence",
        "Pandas", "NumPy",
    ],
    "MLOps Engineer": [
        "Python", "MLOps", "Machine Learning", "AWS", "Docker",
        "Kubernetes", "SQL", "Statistics", "Cloud",
    ],

    #Software Development
    "Software Engineer": [
        "Python", "Java", "C++", "SQL", "JavaScript", "Data Structures",
        "Problem Solving", "Database", "Git", "Design",
    ],
    "Backend Developer": [
        "Python", "Java", "SQL", "Database", "Data Structures",
        "Problem Solving", "JavaScript", "MySQL",
    ],
    "Frontend Developer": [
        "JavaScript", "Design", "Problem Solving", "Python", "SQL",
    ],
    "Full Stack Developer": [
        "Python", "JavaScript", "SQL", "Database", "Problem Solving",
        "Java", "Data Structures", "Design",
    ],
    "Python Developer": [
        "Python", "Pandas", "SQL", "Data Analysis", "Database",
        "Data Structures", "Problem Solving",
    ],
    "Java Developer": [
        "Java", "SQL", "Database", "Data Structures", "MySQL",
        "Problem Solving",
    ],
    "Java Backend Developer": [
        "Java", "SQL", "MySQL", "Database", "Data Structures",
        "Problem Solving",
    ],
    "Web Developer": [
        "JavaScript", "SQL", "Python", "Database", "Design",
        "Problem Solving",
    ],
    "Mobile App Developer": [
        "Java", "JavaScript", "Problem Solving", "Python", "Design",
    ],
    "Android Developer": [
        "Java", "Problem Solving", "Python", "Design",
    ],
    "iOS Developer": [
        "JavaScript", "Problem Solving", "Python", "Design",
    ],
    "Game Developer": [
        "C++", "C", "Java", "Problem Solving", "Design",
    ],

    # Cloud & DevOps
    "DevOps Engineer": [
        "Docker", "AWS", "Python", "Kubernetes", "SQL",
        "Networking", "Problem Solving", "Statistics",
    ],
    "Cloud Engineer": [
        "AWS", "Docker", "Python", "Kubernetes", "Networking",
        "SQL", "Problem Solving",
    ],
    "Cloud Architect": [
        "AWS", "Docker", "Kubernetes", "SQL", "Python", "Networking",
        "Design", "Problem Solving",
    ],
    "System Administrator": [
        "Linux", "Networking", "Problem Solving", "SQL", "Python",
    ],
    "Site Reliability Engineer": [
        "Docker", "Kubernetes", "Python", "SQL", "Networking",
        "Problem Solving",
    ],

    #Cyber Security 
    "Cybersecurity Analyst": [
        "Networking", "Python", "Database", "Problem Solving", "SQL",
        "Linux", "Analysis",
    ],
    "Security Engineer": [
        "Networking", "Python", "Database", "Problem Solving", "Analysis",
    ],
    "Network Engineer": [
        "Networking", "Problem Solving", "Python", "Analysis",
    ],

    #Database 
    "Database Administrator": [
        "SQL", "MySQL", "Database", "Problem Solving", "Analysis",
    ],
    "Database Engineer": [
        "SQL", "MySQL", "Database", "Python", "Problem Solving",
        "Data Structures",
    ],

    # QA & Testing
    "QA Engineer": [
        "Python", "Problem Solving", "Reporting", "Analysis", "SQL",
    ],
    "Automation Test Engineer": [
        "Python", "Java", "Problem Solving", "SQL",
    ],

    #Specialty
    "Embedded Systems Engineer": [
        "C++", "C", "Problem Solving", "Python",
    ],
    "IoT Engineer": [
        "Python", "C++", "Problem Solving", "Networking",
    ],
    "Blockchain Developer": [
        "Python", "Java", "C++", "JavaScript", "Problem Solving",
    ],
    "UI/UX Designer": [
        "Design", "Problem Solving", "JavaScript", "Analysis",
    ],
    "Product Manager": [
        "Management", "Analysis", "Problem Solving", "Reporting",
        "Design", "Statistics",
    ],
    "Solutions Architect": [
        "AWS", "Docker", "Python", "SQL", "Java", "Design",
        "Problem Solving",
    ],
    "Technical Support Engineer": [
        "Networking", "Problem Solving", "Python", "Analysis",
    ],
    "IT Consultant": [
        "Management", "Analysis", "Problem Solving", "Reporting",
        "Networking",
    ],
    "IT Project Manager": [
        "Management", "Analysis", "Reporting", "Problem Solving",
        "Statistics",
    ],
}
def required_skills_for(job):
    """Return the curated required-skill list for a job (case-insensitive lookup)."""
    if job in JOB_REQUIRED_SKILLS:
        return JOB_REQUIRED_SKILLS[job]
    for k, v in JOB_REQUIRED_SKILLS.items():
        if k.lower() == str(job).lower():
            return v
    return []
