"""
Curated skill lists, job-role mappings, mock market data, and suggestion templates.
"""

# ──────────────────────────────────────────────
# SKILL DATABASE (normalised lowercase)
# ──────────────────────────────────────────────
TECHNICAL_SKILLS = {
    # Programming
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c',
    'ruby', 'go', 'golang', 'rust', 'swift', 'kotlin', 'scala', 'r',
    'php', 'perl', 'matlab', 'dart', 'lua', 'haskell',
    # Web
    'html', 'css', 'react', 'reactjs', 'angular', 'vue', 'vuejs',
    'next.js', 'nextjs', 'node.js', 'nodejs', 'express', 'django',
    'flask', 'fastapi', 'spring', 'spring boot', 'asp.net', 'rails',
    'bootstrap', 'tailwindcss', 'jquery', 'webpack', 'vite',
    # Data / ML
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
    'machine learning', 'deep learning', 'nlp', 'natural language processing',
    'computer vision', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
    'pandas', 'numpy', 'matplotlib', 'seaborn', 'tableau', 'power bi',
    'spark', 'hadoop', 'airflow', 'kafka', 'etl', 'data pipeline',
    'data analysis', 'data visualization', 'statistics', 'big data',
    # Cloud / DevOps
    'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes',
    'terraform', 'ansible', 'jenkins', 'ci/cd', 'github actions',
    'linux', 'bash', 'shell scripting', 'nginx', 'apache',
    # Mobile
    'android', 'ios', 'react native', 'flutter',
    # Misc
    'git', 'github', 'bitbucket', 'jira', 'confluence', 'agile',
    'scrum', 'rest api', 'graphql', 'microservices', 'api design',
    'unit testing', 'selenium', 'cypress', 'figma', 'photoshop',
    'blockchain', 'solidity', 'cybersecurity', 'penetration testing',
}

SOFT_SKILLS = {
    'leadership', 'communication', 'teamwork', 'problem solving',
    'critical thinking', 'time management', 'project management',
    'presentation', 'negotiation', 'conflict resolution',
    'adaptability', 'creativity', 'attention to detail',
    'decision making', 'mentoring', 'strategic planning',
}

ALL_SKILLS = TECHNICAL_SKILLS | SOFT_SKILLS

# ──────────────────────────────────────────────
# JOB ROLE → REQUIRED SKILLS MAPPING
# ──────────────────────────────────────────────
JOB_ROLE_SKILLS = {
    'Data Scientist': {
        'required': ['python', 'machine learning', 'statistics', 'sql',
                     'pandas', 'numpy', 'deep learning', 'data visualization',
                     'scikit-learn', 'tensorflow'],
        'nice_to_have': ['pytorch', 'nlp', 'spark', 'tableau', 'r',
                         'computer vision', 'big data'],
        'description': 'Analyse complex data sets, build ML models, and derive actionable insights.',
        'category': 'Data & AI',
    },
    'Machine Learning Engineer': {
        'required': ['python', 'machine learning', 'deep learning',
                     'tensorflow', 'pytorch', 'docker', 'sql', 'numpy',
                     'scikit-learn', 'linux'],
        'nice_to_have': ['kubernetes', 'aws', 'spark', 'mlops', 'ci/cd',
                         'nlp', 'computer vision'],
        'description': 'Design, develop and deploy ML models at scale.',
        'category': 'Data & AI',
    },
    'Full Stack Developer': {
        'required': ['javascript', 'html', 'css', 'react', 'node.js',
                     'sql', 'git', 'rest api', 'python', 'mongodb'],
        'nice_to_have': ['typescript', 'docker', 'aws', 'graphql',
                         'next.js', 'redis', 'ci/cd'],
        'description': 'Build end-to-end web applications covering frontend and backend.',
        'category': 'Software Engineering',
    },
    'Backend Developer': {
        'required': ['python', 'django', 'sql', 'rest api', 'git',
                     'linux', 'docker', 'postgresql', 'redis'],
        'nice_to_have': ['aws', 'kubernetes', 'microservices', 'kafka',
                         'graphql', 'ci/cd', 'elasticsearch'],
        'description': 'Design and maintain server-side logic, APIs, and databases.',
        'category': 'Software Engineering',
    },
    'Frontend Developer': {
        'required': ['javascript', 'html', 'css', 'react', 'typescript',
                     'git', 'rest api', 'webpack'],
        'nice_to_have': ['next.js', 'vue', 'angular', 'figma',
                         'tailwindcss', 'cypress', 'graphql'],
        'description': 'Build responsive, accessible user interfaces for web applications.',
        'category': 'Software Engineering',
    },
    'DevOps Engineer': {
        'required': ['linux', 'docker', 'kubernetes', 'aws', 'ci/cd',
                     'terraform', 'bash', 'git', 'jenkins', 'nginx'],
        'nice_to_have': ['ansible', 'gcp', 'azure', 'kafka',
                         'elasticsearch', 'python', 'shell scripting'],
        'description': 'Automate infrastructure, CI/CD pipelines, and cloud deployments.',
        'category': 'Infrastructure',
    },
    'Data Analyst': {
        'required': ['sql', 'python', 'data analysis', 'data visualization',
                     'tableau', 'statistics', 'excel', 'pandas'],
        'nice_to_have': ['power bi', 'r', 'spark', 'etl', 'big data',
                         'machine learning'],
        'description': 'Interpret data, create dashboards, and support data-driven decisions.',
        'category': 'Data & AI',
    },
    'Cloud Architect': {
        'required': ['aws', 'azure', 'gcp', 'docker', 'kubernetes',
                     'terraform', 'microservices', 'linux', 'networking'],
        'nice_to_have': ['ansible', 'ci/cd', 'security', 'python',
                         'cost optimization'],
        'description': 'Design and oversee cloud infrastructure strategies.',
        'category': 'Infrastructure',
    },
    'Product Manager': {
        'required': ['product management', 'agile', 'scrum', 'jira',
                     'communication', 'strategic planning', 'data analysis',
                     'presentation'],
        'nice_to_have': ['sql', 'figma', 'a/b testing', 'roadmapping',
                         'leadership', 'negotiation'],
        'description': 'Define product vision, prioritise features, and work with engineering teams.',
        'category': 'Management',
    },
    'Cybersecurity Analyst': {
        'required': ['cybersecurity', 'linux', 'networking', 'python',
                     'penetration testing', 'bash', 'firewalls'],
        'nice_to_have': ['aws', 'docker', 'siem', 'incident response',
                         'compliance', 'encryption'],
        'description': 'Protect organisational systems from cyber threats and vulnerabilities.',
        'category': 'Security',
    },
    'Mobile Developer': {
        'required': ['android', 'ios', 'flutter', 'dart', 'git',
                     'rest api', 'firebase'],
        'nice_to_have': ['react native', 'kotlin', 'swift', 'ci/cd',
                         'figma', 'graphql'],
        'description': 'Build and maintain mobile applications for Android and iOS.',
        'category': 'Software Engineering',
    },
    'AI Engineer': {
        'required': ['python', 'deep learning', 'tensorflow', 'pytorch',
                     'nlp', 'machine learning', 'docker', 'linux'],
        'nice_to_have': ['computer vision', 'kubernetes', 'aws',
                         'transformers', 'langchain', 'mlops'],
        'description': 'Build and deploy AI-powered systems and applications.',
        'category': 'Data & AI',
    },
}

# ──────────────────────────────────────────────
# MOCK MARKET DATA
# ──────────────────────────────────────────────
MARKET_DATA = {
    'Data Scientist': {
        'avg_salary': '$95,000 – $155,000',
        'demand_growth': '+28%',
        'top_skills': ['Python', 'Machine Learning', 'SQL', 'TensorFlow', 'Statistics'],
        'hiring_trend': [65, 70, 72, 78, 82, 88, 92, 95, 98, 100, 105, 110],
        'months': ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
    },
    'Machine Learning Engineer': {
        'avg_salary': '$110,000 – $170,000',
        'demand_growth': '+35%',
        'top_skills': ['Python', 'PyTorch', 'TensorFlow', 'Docker', 'MLOps'],
        'hiring_trend': [50, 55, 60, 68, 72, 80, 85, 88, 92, 96, 102, 108],
        'months': ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
    },
    'Full Stack Developer': {
        'avg_salary': '$85,000 – $140,000',
        'demand_growth': '+22%',
        'top_skills': ['JavaScript', 'React', 'Node.js', 'SQL', 'Docker'],
        'hiring_trend': [80, 82, 85, 88, 90, 92, 95, 97, 100, 103, 106, 110],
        'months': ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
    },
    'Backend Developer': {
        'avg_salary': '$80,000 – $135,000',
        'demand_growth': '+20%',
        'top_skills': ['Python', 'Django', 'SQL', 'Docker', 'REST API'],
        'hiring_trend': [75, 78, 80, 83, 85, 88, 90, 93, 95, 98, 100, 104],
        'months': ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
    },
    'Frontend Developer': {
        'avg_salary': '$75,000 – $130,000',
        'demand_growth': '+18%',
        'top_skills': ['JavaScript', 'React', 'TypeScript', 'CSS', 'Next.js'],
        'hiring_trend': [70, 72, 75, 78, 80, 83, 85, 88, 90, 92, 95, 98],
        'months': ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
    },
    'DevOps Engineer': {
        'avg_salary': '$100,000 – $160,000',
        'demand_growth': '+30%',
        'top_skills': ['Docker', 'Kubernetes', 'AWS', 'Terraform', 'CI/CD'],
        'hiring_trend': [60, 65, 68, 72, 76, 80, 85, 90, 94, 98, 102, 108],
        'months': ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
    },
    'Data Analyst': {
        'avg_salary': '$65,000 – $110,000',
        'demand_growth': '+15%',
        'top_skills': ['SQL', 'Python', 'Tableau', 'Statistics', 'Excel'],
        'hiring_trend': [72, 74, 76, 78, 80, 82, 84, 86, 88, 90, 93, 96],
        'months': ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
    },
    'Cloud Architect': {
        'avg_salary': '$120,000 – $180,000',
        'demand_growth': '+32%',
        'top_skills': ['AWS', 'Azure', 'Kubernetes', 'Terraform', 'Microservices'],
        'hiring_trend': [55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 106, 112],
        'months': ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
    },
    'Product Manager': {
        'avg_salary': '$90,000 – $150,000',
        'demand_growth': '+12%',
        'top_skills': ['Agile', 'JIRA', 'Data Analysis', 'Communication', 'Strategy'],
        'hiring_trend': [68, 69, 70, 72, 73, 75, 77, 79, 81, 83, 85, 88],
        'months': ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
    },
    'Cybersecurity Analyst': {
        'avg_salary': '$85,000 – $145,000',
        'demand_growth': '+33%',
        'top_skills': ['Cybersecurity', 'Linux', 'Python', 'Networking', 'Penetration Testing'],
        'hiring_trend': [52, 58, 63, 68, 73, 78, 84, 89, 94, 99, 105, 112],
        'months': ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
    },
    'Mobile Developer': {
        'avg_salary': '$80,000 – $140,000',
        'demand_growth': '+20%',
        'top_skills': ['Flutter', 'React Native', 'Kotlin', 'Swift', 'Firebase'],
        'hiring_trend': [65, 68, 70, 73, 76, 79, 82, 85, 88, 91, 94, 98],
        'months': ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
    },
    'AI Engineer': {
        'avg_salary': '$115,000 – $175,000',
        'demand_growth': '+40%',
        'top_skills': ['Python', 'PyTorch', 'NLP', 'Deep Learning', 'LLMs'],
        'hiring_trend': [45, 52, 58, 65, 72, 80, 87, 94, 100, 108, 115, 124],
        'months': ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
    },
}

# ──────────────────────────────────────────────
# SUGGESTION TEMPLATES
# ──────────────────────────────────────────────
GENERAL_SUGGESTIONS = [
    "Add a professional summary at the top of your resume highlighting your core strengths.",
    "Include quantified achievements (e.g., 'Increased revenue by 25%') instead of generic descriptions.",
    "Add links to your GitHub profile, portfolio, or LinkedIn.",
    "Use action verbs (Designed, Built, Optimized, Led) to describe accomplishments.",
    "Keep your resume concise — ideally 1–2 pages.",
    "Ensure consistent formatting and font usage throughout.",
    "Add relevant certifications to boost credibility.",
    "Tailor your resume keywords to match the job description.",
]

SKILL_GAP_SUGGESTIONS = {
    'python': "Add Python projects or certifications (e.g., Google IT Automation with Python).",
    'machine learning': "Include ML projects — Kaggle competitions or end-to-end model deployments.",
    'sql': "Highlight SQL proficiency — mention complex queries, stored procedures, or database design.",
    'docker': "Add Docker experience — containerised deployments or Dockerfile creation.",
    'kubernetes': "Mention Kubernetes orchestration experience or CKA certification.",
    'aws': "Add AWS certifications (Solutions Architect, Developer) or cloud project experience.",
    'react': "Showcase React projects — SPAs, component libraries, or open-source contributions.",
    'tensorflow': "Include TensorFlow projects — model training, serving, or TFLite deployments.",
    'pytorch': "Highlight PyTorch experience — research papers, model implementations.",
    'nlp': "Add NLP projects — text classification, chatbots, or sentiment analysis.",
    'git': "Mention version control experience with Git — branching strategies, code reviews.",
    'ci/cd': "Highlight CI/CD pipeline setup — Jenkins, GitHub Actions, or GitLab CI.",
    'agile': "Mention Agile/Scrum experience — sprint planning, retrospectives, Kanban boards.",
    'deep learning': "Add deep learning projects — CNNs, RNNs, transformers, or GANs.",
    'data visualization': "Include data viz work — Tableau dashboards, D3.js, or Matplotlib reports.",
    'linux': "Mention Linux system administration or shell scripting experience.",
    'typescript': "Showcase TypeScript usage in production projects for type-safe development.",
    'graphql': "Highlight GraphQL API design or consumption experience.",
    'microservices': "Add microservices architecture experience — service decomposition, API gateways.",
    'flutter': "Include Flutter projects — cross-platform mobile apps published on app stores.",
}

# ──────────────────────────────────────────────
# EDUCATION LEVELS (ordered by weight)
# ──────────────────────────────────────────────
EDUCATION_KEYWORDS = {
    'phd': ('PhD / Doctorate', 100),
    'doctorate': ('PhD / Doctorate', 100),
    'ph.d': ('PhD / Doctorate', 100),
    'master': ("Master's Degree", 85),
    'mba': ("Master's Degree (MBA)", 85),
    'm.s.': ("Master's Degree", 85),
    'm.tech': ("Master's Degree", 85),
    'msc': ("Master's Degree", 85),
    'bachelor': ("Bachelor's Degree", 70),
    'b.tech': ("Bachelor's Degree", 70),
    'b.e.': ("Bachelor's Degree", 70),
    'b.s.': ("Bachelor's Degree", 70),
    'bsc': ("Bachelor's Degree", 70),
    'b.sc': ("Bachelor's Degree", 70),
    'diploma': ('Diploma', 50),
    'associate': ('Associate Degree', 45),
    'high school': ('High School', 30),
    'secondary': ('High School', 30),
}
