import csv
import random
import os
import tqdm

def generate_synthetic_resumes(output_path='ml_models/kaggle_data/massive_synthetic_resumes.csv', num_samples=10000):
    CATEGORIES = {
        'Data Science': ['Python', 'R', 'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'SQL', 'Data Analysis', 'Statistics', 'NLP', 'Computer Vision'],
        'HR': ['Recruitment', 'Employee Relations', 'Onboarding', 'Payroll', 'Performance Management', 'HRIS', 'Talent Acquisition', 'Labor Laws'],
        'Advocate': ['Litigation', 'Legal Research', 'Contract Law', 'Corporate Law', 'Drafting', 'Court Proceedings', 'Legal Writing', 'Negotiation'],
        'Arts': ['Graphic Design', 'Illustration', 'Adobe Creative Suite', 'Painting', 'Drawing', 'Sculpture', 'Typography', 'Visual Arts'],
        'Web Designing': ['HTML', 'CSS', 'JavaScript', 'UI/UX', 'Figma', 'Responsive Design', 'Bootstrap', 'Adobe XD', 'Web Accessibility'],
        'Mechanical Engineer': ['CAD', 'SolidWorks', 'Thermodynamics', 'AutoCAD', 'Manufacturing', 'Fluid Mechanics', 'ANSYS', 'Product Design'],
        'Sales': ['B2B', 'B2C', 'Account Management', 'CRM', 'Lead Generation', 'Cold Calling', 'Negotiation', 'Salesforce', 'Closing Deals'],
        'Health and fitness': ['Personal Training', 'Nutrition', 'Anatomy', 'Diet Planning', 'Yoga', 'Physical Therapy', 'CPR Certified', 'Fitness Assessment'],
        'Civil Engineer': ['AutoCAD Civil 3D', 'Structural Analysis', 'Project Management', 'Surveying', 'Construction Management', 'Concrete Design', 'STAAD.Pro'],
        'Java Developer': ['Java', 'Spring Boot', 'Hibernate', 'Microservices', 'REST APIs', 'SQL', 'Maven', 'Tomcat', 'JUnit'],
        'Business Analyst': ['Agile', 'Scrum', 'Requirements Gathering', 'Data Analysis', 'Tableau', 'Visio', 'SQL', 'Business Intelligence', 'Process Improvement'],
        'SAP Developer': ['ABAP', 'SAP ERP', 'Fiori', 'SAP HANA', 'OData', 'BAPI', 'SAP NetWeaver', 'IDoc'],
        'Automation Testing': ['Selenium', 'Appium', 'TestNG', 'Cucumber', 'JUnit', 'Jenkins', 'API Testing', 'Postman', 'Python', 'Java'],
        'Electrical Engineering': ['Circuit Design', 'MATLAB', 'Power Systems', 'PLC', 'AutoCAD Electrical', 'Control Systems', 'C/C++'],
        'Operations Manager': ['Supply Chain Management', 'Six Sigma', 'Lean Manufacturing', 'Process Optimization', 'Logistics', 'Budgeting', 'Vendor Management'],
        'Python Developer': ['Python', 'Django', 'Flask', 'FastAPI', 'Pandas', 'PostgreSQL', 'Docker', 'Celery', 'REST APIs'],
        'DevOps Engineer': ['AWS', 'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'Terraform', 'Linux', 'Ansible', 'Git'],
        'Network Security Engineer': ['Firewalls', 'VPN', 'Cisco', 'Network Architecture', 'Cybersecurity', 'TCP/IP', 'Penetration Testing', 'SIEM'],
        'PMO': ['Project Management', 'Prince2', 'PMP', 'Risk Management', 'Stakeholder Management', 'Budget Tracking', 'Resource Allocation', 'Agile'],
        'Database': ['SQL Server', 'Oracle', 'MySQL', 'MongoDB', 'Database Administration', 'Performance Tuning', 'ETL', 'Data Warehousing'],
        'Hadoop': ['Hadoop', 'Spark', 'Hive', 'Big Data', 'HBase', 'Kafka', 'Scala', 'MapReduce', 'HDFS'],
        'ETL Developer': ['Informatica', 'Talend', 'DataStage', 'SQL', 'Data Warehousing', 'Data Modeling', 'SSIS', 'Python'],
        'DotNet Developer': ['C#', '.NET Core', 'ASP.NET', 'MVC', 'Entity Framework', 'SQL Server', 'Web API', 'Azure'],
        'Blockchain': ['Solidity', 'Ethereum', 'Smart Contracts', 'Web3.js', 'Cryptography', 'Hyperledger', 'DApps', 'Rust'],
        'Testing': ['Manual Testing', 'JIRA', 'Bug Tracking', 'Test Cases', 'Regression Testing', 'Quality Assurance', 'UAT', 'Black Box Testing']
    }

    ACTION_VERBS = ['Developed', 'Managed', 'Designed', 'Implemented', 'Led', 'Created', 'Analyzed', 'Optimized', 'Improved', 'Maintained', 'Engineered']
    ADJECTIVES = ['innovative', 'scalable', 'efficient', 'robust', 'high-performance', 'complex', 'user-friendly', 'secure', 'dynamic']
    NOUNS = ['systems', 'applications', 'processes', 'solutions', 'frameworks', 'architectures', 'pipelines', 'models']

    print(f"Generating {num_samples} synthetic resumes across {len(CATEGORIES)} categories...")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Category', 'Resume']) # Kaggle format
        
        for _ in tqdm.tqdm(range(num_samples)):
            category = random.choice(list(CATEGORIES.keys()))
            skills = CATEGORIES[category]
            
            # Generate a synthetic resume text
            num_skills = min(random.randint(3, 8), len(skills))
            chosen_skills = random.sample(skills, num_skills)
            
            sentences = []
            
            # Education
            sentences.append(f"Education: Bachelor of Science in {category} related field from University of Technology.")
            
            # Skills section
            sentences.append(f"Skills: {', '.join(chosen_skills)}.")
            
            # Experience section
            for skill in chosen_skills:
                verb = random.choice(ACTION_VERBS)
                adj = random.choice(ADJECTIVES)
                noun = random.choice(NOUNS)
                sentences.append(f"{verb} {adj} {noun} using {skill}.")
                
            # Random fluff
            if random.random() > 0.5:
                sentences.append("Strong problem-solving skills and ability to work in a team.")
            if random.random() > 0.5:
                sentences.append("Excellent communication and leadership abilities.")
                
            random.shuffle(sentences)
            resume_text = " ".join(sentences)
            
            writer.writerow([category, resume_text])
            
    print(f"✅ Successfully generated {num_samples} records to {output_path}")

if __name__ == '__main__':
    # Generate 3,000 rows for faster execution
    generate_synthetic_resumes(num_samples=3000)
