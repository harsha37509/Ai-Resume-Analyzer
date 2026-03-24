"""
generate_dataset.py
-------------------
Generates a realistic Resume Screening Dataset (resume_dataset.csv)
Run once: python generate_dataset.py
"""

import csv
import random

random.seed(42)

NAMES = [
    "Alice Johnson","Bob Smith","Carol Williams","David Brown","Emma Davis",
    "Frank Miller","Grace Wilson","Henry Moore","Isabella Taylor","James Anderson",
    "Karen Thomas","Liam Jackson","Mia Harris","Noah Martin","Olivia Lee",
    "Paul Garcia","Quinn Martinez","Rachel Robinson","Sam Clark","Tina Lewis",
    "Uma Walker","Victor Hall","Wendy Allen","Xander Young","Yara King",
    "Zoe Wright","Aaron Scott","Bella Green","Carlos Adams","Diana Baker",
    "Ethan Nelson","Fiona Carter","George Mitchell","Hannah Perez","Ian Roberts",
    "Julia Turner","Kevin Phillips","Laura Campbell","Mark Parker","Nancy Evans",
    "Oscar Edwards","Patricia Collins","Quincy Stewart","Rita Sanchez","Steve Morris",
    "Teresa Rogers","Ulysses Reed","Vivian Cook","William Morgan","Xena Bell",
    "Yusuf Murphy","Zara Bailey","Aiden Rivera","Bella Cooper","Carlos Richardson",
    "Diana Cox","Eli Howard","Faith Ward","Gabriel Torres","Hannah Peterson",
    "Ivan Gray","Julia Ramirez","Kyle James","Luna Watson","Marcus Brooks",
    "Nora Kelly","Omar Sanders","Priya Price","Quinn Bennett","Rosa Wood",
    "Samuel Barnes","Tara Ross","Umar Henderson","Violet Coleman","Will Jenkins",
    "Xena Perry","Yara Powell","Zach Long","Amy Patterson","Brian Hughes",
    "Chloe Flores","Derek Washington","Ella Butler","Frank Foster","Grace Foster",
    "Hector Gonzales","Isabella Bryant","Jake Alexander","Kira Russell","Leo Griffin",
    "Maya Diaz","Nate Hayes","Opal Myers","Patrick Ford","Quinn Hamilton",
    "Rosa Graham","Seth Sullivan","Tina Wallace","Uma West","Victor Cole",
]

ROLES = [
    "Data Scientist","Machine Learning Engineer","Software Engineer",
    "Backend Developer","Frontend Developer","Full Stack Developer",
    "Data Analyst","DevOps Engineer","Cloud Architect","NLP Engineer",
    "AI Research Engineer","Business Intelligence Analyst",
]

SKILLS_POOL = {
    "Data Scientist": ["Python","R","Machine Learning","Deep Learning","TensorFlow","PyTorch","Pandas","NumPy","Scikit-learn","SQL","Statistics","Data Visualization","Tableau","Power BI","Matplotlib","Seaborn","Jupyter","NLP","Computer Vision","AWS"],
    "Machine Learning Engineer": ["Python","TensorFlow","PyTorch","Keras","Scikit-learn","MLflow","Docker","Kubernetes","AWS","Azure","GCP","Spark","Hadoop","SQL","NoSQL","REST API","Git","Linux","Deep Learning","Feature Engineering"],
    "Software Engineer": ["Java","Python","C++","C#","JavaScript","TypeScript","Spring Boot","Django","Flask","React","Node.js","SQL","MongoDB","Docker","Kubernetes","AWS","Git","CI/CD","Agile","REST API"],
    "Backend Developer": ["Python","Java","Node.js","Express","Django","Flask","Spring Boot","SQL","PostgreSQL","MySQL","MongoDB","Redis","Docker","Kubernetes","AWS","REST API","GraphQL","Microservices","Git","Linux"],
    "Frontend Developer": ["JavaScript","TypeScript","React","Angular","Vue.js","HTML","CSS","SASS","Webpack","Redux","Next.js","Jest","Git","REST API","Figma","Bootstrap","Tailwind","Node.js","npm","Agile"],
    "Full Stack Developer": ["JavaScript","TypeScript","React","Node.js","Express","Python","Django","PostgreSQL","MongoDB","Docker","AWS","Git","REST API","GraphQL","HTML","CSS","Redis","Nginx","CI/CD","Agile"],
    "Data Analyst": ["SQL","Python","Excel","Tableau","Power BI","R","Pandas","Statistics","Data Cleaning","ETL","Google Analytics","BigQuery","Looker","SAS","SPSS","Storytelling","Visualization","Reporting","KPI","Business Intelligence"],
    "DevOps Engineer": ["Docker","Kubernetes","Jenkins","Terraform","Ansible","AWS","Azure","GCP","Linux","Bash","Python","CI/CD","Helm","Prometheus","Grafana","ELK Stack","Git","Nginx","Networking","Security"],
    "Cloud Architect": ["AWS","Azure","GCP","Terraform","Docker","Kubernetes","Microservices","Networking","Security","IAM","Serverless","Lambda","CloudFormation","CDK","Cost Optimization","CI/CD","Linux","Python","Architecture","Compliance"],
    "NLP Engineer": ["Python","NLP","BERT","GPT","HuggingFace","SpaCy","NLTK","TensorFlow","PyTorch","Transformers","Text Classification","Named Entity Recognition","Sentiment Analysis","Word2Vec","FastText","SQL","Docker","REST API","Git","Research"],
    "AI Research Engineer": ["Python","PyTorch","TensorFlow","Research","Deep Learning","Reinforcement Learning","Computer Vision","NLP","Mathematics","Statistics","CUDA","GPU","C++","LaTeX","Docker","AWS","Git","Optimization","Algorithms","Paper Writing"],
    "Business Intelligence Analyst": ["SQL","Tableau","Power BI","Excel","Python","R","Data Modeling","ETL","Reporting","KPI","SSRS","SSAS","Oracle","SAP","Business Analysis","Dashboards","Statistics","Communication","Stakeholder Management","Agile"],
}

EDUCATION_LEVELS = [
    "B.Tech in Computer Science","B.Sc in Data Science","M.Tech in AI & ML",
    "MBA with Data Analytics","M.Sc in Computer Science","B.E in Information Technology",
    "Ph.D in Machine Learning","B.Tech in Electronics","M.Sc in Statistics","B.Sc in Mathematics",
]

CERTIFICATIONS = [
    "AWS Certified Solutions Architect","Google Professional Data Engineer",
    "Microsoft Azure Data Scientist","TensorFlow Developer Certificate",
    "Coursera Machine Learning","Udemy Python Bootcamp","IBM Data Science Professional",
    "PMP Certified","Oracle SQL Expert","Docker Certified Associate",
    "Certified Kubernetes Administrator","HashiCorp Terraform Associate",
    "Deep Learning Specialization - Coursera","Data Science Nanodegree - Udacity",
]

COMPANIES = [
    "Google","Amazon","Microsoft","TCS","Infosys","Wipro","Accenture",
    "Deloitte","IBM","HCL Technologies","Cognizant","Capgemini","Oracle","SAP",
    "Flipkart","Swiggy","Zomato","Ola","Paytm","PhonePe","Razorpay","Freshworks",
]

def generate_summary(name, role, exp, top_skills):
    s3 = top_skills[:3]
    return (
        f"{name} is a {role} with {exp} years of experience specializing in "
        f"{', '.join(s3)}. Passionate about delivering scalable solutions and "
        f"collaborating in cross-functional teams."
    )

rows = []
for i, name in enumerate(NAMES[:100]):
    role = random.choice(ROLES)
    exp = random.randint(0, 15)
    pool = SKILLS_POOL[role]
    num_skills = random.randint(6, len(pool))
    skills = random.sample(pool, num_skills)
    education = random.choice(EDUCATION_LEVELS)
    certs = random.sample(CERTIFICATIONS, random.randint(0, 3))
    company = random.choice(COMPANIES)
    ats_score = random.randint(55, 99)
    summary = generate_summary(name, role, exp, skills)

    rows.append({
        "candidate_id": f"CAND{i+1:03d}",
        "name": name,
        "role": role,
        "experience_years": exp,
        "skills": "; ".join(skills),
        "education": education,
        "certifications": "; ".join(certs) if certs else "None",
        "last_company": company,
        "ats_score": ats_score,
        "summary": summary,
    })

# Write CSV
fieldnames = ["candidate_id","name","role","experience_years","skills","education","certifications","last_company","ats_score","summary"]
output_path = "dataset/resume_dataset.csv"

with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Dataset generated: {output_path} ({len(rows)} records)")
