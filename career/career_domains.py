CAREER_DOMAINS = {
    "AI & Data Science": [
        "AI Engineer",
        "Artificial Intelligence Engineer",
        "Machine Learning Engineer",
        "Deep Learning Engineer",
        "Data Scientist",
        "Data Analyst",
        "Business Intelligence Analyst",
        "Data Engineer",
        "Big Data Engineer",
        "NLP Engineer",
        "Computer Vision Engineer",
        "AI Research Scientist",
        "MLOps Engineer"
    ],

    "Software Development": [
        "Software Engineer",
        "Backend Developer",
        "Frontend Developer",
        "Full Stack Developer",
        "Python Developer",
        "Java Developer",
        "Java Backend Developer",
        "Web Developer",
        "Mobile App Developer",
        "Android Developer",
        "iOS Developer",
        "Game Developer"
    ],

    "Cloud & DevOps": [
        "Cloud Engineer",
        "Cloud Architect",
        "DevOps Engineer",
        "Site Reliability Engineer",
        "System Administrator"
    ],

    "Cyber Security": [
        "Cybersecurity Analyst",
        "Security Engineer",
        "Network Engineer",
        "IT Consultant"
    ]
}

def detect_domain(skills):

    skills = {s.lower() for s in skills}

    ai_keywords = {
        "machine learning",
        "deep learning",
        "tensorflow",
        "pytorch",
        "keras",
        "pandas",
        "numpy",
        "scikit-learn",
        "xgboost",
        "llama",
        "rag",
        "chromadb",
        "sentence transformers",
        "groq api",
        "power bi",
        "statistics"
    }

    software_keywords = {
        "python",
        "java",
        "javascript",
        "react",
        "fastapi",
        "flask",
        "django",
        "html",
        "css",
        "git",
        "github",
        "sql"
    }

    cloud_keywords = {
        "docker",
        "kubernetes",
        "aws",
        "azure",
        "gcp",
        "terraform",
        "jenkins"
    }

    security_keywords = {
        "penetration testing",
        "network security",
        "ethical hacking",
        "cybersecurity"
    }

    scores = {
        "AI & Data Science": len(skills & ai_keywords),
        "Software Development": len(skills & software_keywords),
        "Cloud & DevOps": len(skills & cloud_keywords),
        "Cyber Security": len(skills & security_keywords),
    }

    return max(scores, key=scores.get)

AI_PRIORITY_JOBS = {
    "AI Engineer",
    "Artificial Intelligence Engineer",
    "Machine Learning Engineer",
    "Deep Learning Engineer",
    "Data Scientist",
    "NLP Engineer",
    "Computer Vision Engineer",
    "AI Research Scientist",
    "MLOps Engineer"
}

AI_PRIORITY_SKILLS = {
    "machine learning",
    "deep learning",
    "tensorflow",
    "pytorch",
    "keras",
    "llama",
    "rag",
    "langchain",
    "chromadb",
    "sentence transformers",
    "hugging face",
    "scikit-learn",
    "xgboost",
    "computer vision",
    "nlp",
    "natural language processing"
}