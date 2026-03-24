"""
ml_engine.py
ML-powered resume analysis engine.
Handles: skill extraction, scoring, ranking, CSV dataset loading.
"""

import re
import csv
import math
import os
import random
from collections import Counter

# ML libraries
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# ─── Skill Taxonomy ──────────────────────────────────────────────────────────

SKILL_CATEGORIES = {
    "Programming Languages": [
        "python","java","javascript","typescript","c++","c#","c","ruby","php",
        "swift","kotlin","go","rust","scala","r","matlab","bash","perl","lua",
    ],
    "Web & Frontend": [
        "react","angular","vue","vuejs","html","css","sass","less","bootstrap",
        "tailwind","webpack","nextjs","nuxtjs","jquery","redux","graphql","rest api",
    ],
    "Backend & Frameworks": [
        "node","express","django","flask","spring","fastapi","rails","laravel",
        ".net","asp.net","nestjs","microservices","rest","soap","grpc",
    ],
    "Databases": [
        "sql","mysql","postgresql","mongodb","redis","cassandra","oracle",
        "sqlite","firebase","dynamodb","elasticsearch","neo4j","bigquery",
    ],
    "Cloud & DevOps": [
        "aws","azure","gcp","docker","kubernetes","jenkins","terraform","ansible",
        "ci/cd","linux","nginx","helm","prometheus","grafana","elk","serverless",
    ],
    "Data Science & ML": [
        "machine learning","deep learning","scikit-learn","tensorflow","pytorch",
        "keras","pandas","numpy","matplotlib","seaborn","nlp","computer vision",
        "reinforcement learning","feature engineering","data visualization",
        "statistics","tableau","power bi","spark","hadoop","mlflow",
    ],
    "AI & NLP": [
        "bert","gpt","huggingface","transformers","spacy","nltk","word2vec",
        "fasttext","sentiment analysis","text classification","named entity recognition",
        "llm","langchain","openai","generative ai",
    ],
    "Tools & Platforms": [
        "git","github","gitlab","jira","confluence","slack","figma","postman",
        "vs code","linux","windows","macos","jupyter","google colab",
    ],
    "Soft Skills": [
        "leadership","communication","problem solving","teamwork","agile","scrum",
        "management","mentoring","collaboration","analytical","critical thinking",
    ],
}

ALL_SKILLS = []
for skills in SKILL_CATEGORIES.values():
    ALL_SKILLS.extend(skills)
ALL_SKILLS = list(set(ALL_SKILLS))

EDUCATION_KEYWORDS = {
    "phd": 5, "doctorate": 5, "ph.d": 5,
    "master": 4, "mtech": 4, "msc": 4, "m.tech": 4, "m.sc": 4, "mba": 4,
    "bachelor": 3, "btech": 3, "bsc": 3, "b.tech": 3, "b.sc": 3, "b.e": 3,
    "diploma": 2, "associate": 2,
    "university": 2, "college": 1, "institute": 1,
}

# ─── Text Extraction ──────────────────────────────────────────────────────────

def extract_skills(text: str) -> dict:
    """Returns {category: [skills]} and flat list of skills found."""
    lower = text.lower()
    found_by_cat = {}
    flat = []
    for category, skills in SKILL_CATEGORIES.items():
        hits = []
        for skill in skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, lower):
                hits.append(skill)
                flat.append(skill)
        if hits:
            found_by_cat[category] = hits
    return {"by_category": found_by_cat, "flat": list(set(flat))}


def extract_experience(text: str) -> int:
    """Estimate years of experience from text."""
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:professional\s*)?experience',
        r'experience\s*[:\-]?\s*(\d+)\+?\s*years?',
        r'(\d+)\s*(?:to|-)\s*\d+\s*years?\s*(?:of\s*)?experience',
        r'over\s+(\d+)\s*years?',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return min(int(m.group(1)), 30)
    # Heuristic: count senior/lead/manager indicators
    indicators = ["senior","lead","principal","staff","manager","architect","director"]
    count = sum(1 for kw in indicators if kw in text.lower())
    return min(count * 2, 10)


def extract_education(text: str) -> dict:
    """Returns highest education level found and raw keywords."""
    lower = text.lower()
    found = {}
    max_score = 0
    highest = "Not Specified"
    for kw, score in EDUCATION_KEYWORDS.items():
        if kw in lower:
            found[kw] = score
            if score > max_score:
                max_score = score
                highest = kw.upper()
    return {"highest": highest, "keywords": list(found.keys()), "score": max_score}


def extract_contact_info(text: str) -> dict:
    """Extract email, phone from text."""
    email = re.findall(r'[\w.\-+]+@[\w.\-]+\.\w+', text)
    phone = re.findall(r'[\+\(]?[0-9][0-9\s\-\(\)]{8,}[0-9]', text)
    return {
        "email": email[0] if email else "Not found",
        "phone": phone[0].strip() if phone else "Not found",
    }


def compute_ats_score(text: str, skills: list) -> int:
    """Estimate ATS score based on structure signals and skill count."""
    score = 40  # base
    # Skill presence
    score += min(len(skills) * 2, 25)
    # Section headers
    sections = ["experience","education","skills","projects","summary","objective","certifications"]
    for s in sections:
        if s in text.lower():
            score += 3
    # Reasonable length (200-1500 words ideal)
    words = len(text.split())
    if 200 <= words <= 1500:
        score += 5
    return min(score, 100)


def compute_readability(text: str) -> int:
    """Simple readability proxy based on sentence/word length."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    if not sentences:
        return 50
    avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
    # Ideal sentence length ~15-20 words
    if 10 <= avg_len <= 20:
        return random.randint(78, 92)
    elif avg_len < 10:
        return random.randint(65, 78)
    else:
        return random.randint(55, 70)


def compute_complexity(skills: list, experience: int, education_score: int) -> int:
    """Composite complexity score."""
    skill_score = min(len(skills) / 20 * 40, 40)
    exp_score = min(experience / 10 * 30, 30)
    edu_score = min(education_score / 5 * 30, 30)
    return int(skill_score + exp_score + edu_score)


# ─── Match Scoring ────────────────────────────────────────────────────────────

STOP_WORDS = {
    "and","the","for","with","from","this","that","have","has","are","was",
    "were","been","being","will","would","could","should","may","might","must",
    "shall","can","need","your","etc","also","any","all","more","our","their",
    "its","not","but","are","you","we","they","he","she","it","is","in","on",
    "at","to","of","a","an","as","by","be","do","if","or","so","up","out",
    "who","how","what","when","where","why","which","just","use","using",
}


def extract_jd_keywords(jd: str) -> list:
    words = re.findall(r'\b\w{3,}\b', jd.lower())
    return [w for w in words if w not in STOP_WORDS]


def calculate_match_score(resume_text: str, jd: str, resume_skills: list) -> dict:
    """Returns overall score and breakdown."""
    jd_keywords = extract_jd_keywords(jd)
    resume_lower = resume_text.lower()

    # Keyword match
    matched_kw = [w for w in jd_keywords if re.search(r'\b' + re.escape(w) + r'\b', resume_lower)]
    kw_score = (len(matched_kw) / max(len(jd_keywords), 1)) * 45

    # Skill match
    jd_skills = extract_skills(jd)["flat"]
    matched_skills = [s for s in jd_skills if s in resume_skills]
    skill_score = (len(matched_skills) / max(len(jd_skills), 1)) * 45 if jd_skills else 20

    # Experience bonus (up to 10 pts)
    exp_bonus = 0
    exp_match = re.search(r'(\d+)\+?\s*years?', jd, re.IGNORECASE)
    if exp_match:
        required_exp = int(exp_match.group(1))
        candidate_exp = extract_experience(resume_text)
        exp_bonus = min(10, max(0, 10 - abs(candidate_exp - required_exp)))
    else:
        exp_bonus = 5  # neutral

    total = round(kw_score + skill_score + exp_bonus)
    total = max(5, min(100, total))

    return {
        "total": total,
        "keyword_score": round(kw_score),
        "skill_score": round(skill_score),
        "exp_bonus": round(exp_bonus),
        "matched_keywords": list(set(matched_kw))[:12],
        "matched_skills": matched_skills,
    }


def calculate_semantic_similarity(resume_text: str, jd: str) -> float:
    """Calculate semantic similarity between resume and job description using TF-IDF."""
    if not ML_AVAILABLE:
        return 0.0
    
    try:
        vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
        texts = [resume_text, jd]
        tfidf_matrix = vectorizer.fit_transform(texts)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(float(similarity) * 100, 2)
    except Exception:
        return 0.0


# ─── Single Resume Full Analysis ─────────────────────────────────────────────

def analyze_resume(text: str, filename: str = "resume") -> dict:
    skills_data = extract_skills(text)
    flat_skills = skills_data["flat"]
    experience = extract_experience(text)
    education = extract_education(text)
    contact = extract_contact_info(text)
    ats = compute_ats_score(text, flat_skills)
    readability = compute_readability(text) + random.randint(-3, 3)
    complexity = compute_complexity(flat_skills, experience, education["score"])

    # Section quality scores
    sections = {
        "Summary/Objective": 90 if any(w in text.lower() for w in ["summary","objective","profile"]) else 40,
        "Experience": 85 if "experience" in text.lower() else 35,
        "Education": 90 if any(k in text.lower() for k in EDUCATION_KEYWORDS) else 30,
        "Skills": 95 if len(flat_skills) >= 5 else max(30, len(flat_skills) * 10),
        "Projects": 80 if "project" in text.lower() else 25,
        "Certifications": 75 if "certif" in text.lower() else 20,
    }

    # Sentiment proxy (positive action verbs)
    positive_verbs = ["developed","built","designed","led","improved","achieved",
                      "increased","managed","created","implemented","optimized","delivered"]
    neutral_verbs  = ["worked","assisted","helped","supported","participated"]
    neg_words      = ["lack","missing","no experience","unfamiliar","basic"]

    text_lower = text.lower()
    pos_count = sum(1 for v in positive_verbs if v in text_lower)
    neu_count = sum(1 for v in neutral_verbs if v in text_lower)
    neg_count = sum(1 for w in neg_words if w in text_lower)
    total_sentiment = pos_count + neu_count + neg_count + 1
    sentiment = {
        "positive": round(pos_count / total_sentiment * 100),
        "neutral":  round(neu_count / total_sentiment * 100),
        "negative": round(neg_count / total_sentiment * 100),
    }

    return {
        "filename": filename,
        "contact": contact,
        "experience_years": experience,
        "education": education,
        "skills": skills_data,
        "scores": {
            "ats_score": ats,
            "readability": max(0, min(100, readability)),
            "complexity": complexity,
        },
        "section_quality": sections,
        "sentiment": sentiment,
        "word_count": len(text.split()),
    }


# ─── Dataset (CSV) Loader ─────────────────────────────────────────────────────

def load_csv(csv_path: str) -> list:
    """Load resume_dataset.csv into list of dicts."""
    if not os.path.exists(csv_path):
        return []
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def rank_dataset(dataset: list, jd: str, top_n: int = 10) -> list:
    """
    Score every CSV row against a job description.
    Uses skills + summary + role as the 'resume text'.
    """
    results = []
    for row in dataset:
        combined_text = (
            f"{row.get('role','')} {row.get('category','')} "
            f"{row.get('skills','')} "
            f"{row.get('summary','')} "
            f"{row.get('education','')} "
            f"{row.get('certifications','')} "
            f"{row.get('experience_years','')} years experience"
        )
        skills_list = [s.strip().lower() for s in row.get("skills","").split(";")]
        match = calculate_match_score(combined_text, jd, skills_list)
        semantic_sim = calculate_semantic_similarity(combined_text, jd)

        results.append({
            "candidate_id": row.get("candidate_id",""),
            "name": row.get("name","Unknown"),
            "role": row.get("role",""),
            "category": row.get("category",""),
            "experience_years": row.get("experience_years","0"),
            "education": row.get("education",""),
            "certifications": row.get("certifications",""),
            "last_company": row.get("last_company",""),
            "original_ats": row.get("ats_score",""),
            "skills": skills_list,
            "match_score": match["total"],
            "keyword_score": match["keyword_score"],
            "skill_score": match["skill_score"],
            "semantic_similarity": semantic_sim,
            "matched_keywords": match["matched_keywords"],
            "matched_skills": match["matched_skills"],
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_n] if top_n > 0 else results


# ─── Chart Data Builders ──────────────────────────────────────────────────────

def chart_skills_by_category(skills_by_category: dict) -> dict:
    labels = list(skills_by_category.keys())
    counts = [len(v) for v in skills_by_category.values()]
    return {"labels": labels, "data": counts}


def chart_section_quality(section_quality: dict) -> dict:
    return {
        "labels": list(section_quality.keys()),
        "data": list(section_quality.values()),
    }


def chart_sentiment(sentiment: dict) -> dict:
    return {
        "labels": ["Positive", "Neutral", "Negative"],
        "data": [sentiment["positive"], sentiment["neutral"], sentiment["negative"]],
    }


def chart_ranking(ranked: list) -> dict:
    return {
        "labels": [r["name"] for r in ranked],
        "match_scores": [r["match_score"] for r in ranked],
        "skill_scores": [r["skill_score"] for r in ranked],
        "keyword_scores": [r["keyword_score"] for r in ranked],
    }


def chart_skill_distribution(ranked: list) -> dict:
    """Top 10 skills across all ranked candidates."""
    counter = Counter()
    for r in ranked:
        counter.update(r["skills"])
    top = counter.most_common(10)
    return {
        "labels": [t[0] for t in top],
        "data":   [t[1] for t in top],
    }

# ─── File Utilities ───────────────────────────────────────────────────────────

def extract_text_from_file(file_storage, pdfplumber=None, DOCX_AVAILABLE=False, DocxDocument=None) -> str:
    """Extract raw text from an uploaded FileStorage object."""
    filename = file_storage.filename
    ext = filename.rsplit(".", 1)[-1].lower()
    raw = file_storage.read()

    if ext == "txt":
        return raw.decode("utf-8", errors="ignore")

    if ext == "pdf":
        if pdfplumber:
            try:
                import io
                with pdfplumber.open(io.BytesIO(raw)) as pdf:
                    return "\n".join(page.extract_text() or "" for page in pdf.pages)
            except Exception:
                pass
        return f"[PDF text extraction unavailable — install pdfplumber]\nFilename: {filename}"

    if ext in ("docx", "doc"):
        if DOCX_AVAILABLE and DocxDocument:
            try:
                import io
                doc = DocxDocument(io.BytesIO(raw))
                return "\n".join(p.text for p in doc.paragraphs)
            except Exception:
                pass
        return f"[DOCX text extraction unavailable — install python-docx]\nFilename: {filename}"

    return f"[Unsupported file type: {ext}]"

# ─── ML Classification & Fake Detection ───────────────────────────────────────

import joblib

_ML_BASE = os.path.dirname(os.path.abspath(__file__))
_MODELS_DIR = os.path.join(_ML_BASE, "models")

def train_classifier(csv_path: str) -> dict:
    """Train a simple model to classify resumes by category/role."""
    if not ML_AVAILABLE:
        return {"error": "scikit-learn not available"}
    
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.pipeline import Pipeline
    import pandas as pd

    if not os.path.exists(csv_path):
        return {"error": f"Dataset not found at {csv_path}"}
        
    df = pd.read_csv(csv_path)
    if df.empty or ('category' not in df.columns and 'role' not in df.columns):
        return {"error": "CSV must have 'category' or 'role' column"}
        
    target_col = 'category' if 'category' in df.columns else 'role'
    
    # Text combining strategy
    df['text'] = df.get('skills', '').fillna('') + " " + df.get('summary', '').fillna('') + " " + df.get('education', '').fillna('')
    df = df.dropna(subset=[target_col, 'text'])
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=1000, stop_words='english')),
        ('clf', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    pipeline.fit(df['text'], df[target_col])
    
    os.makedirs(_MODELS_DIR, exist_ok=True)
    joblib.dump(pipeline, os.path.join(_MODELS_DIR, "classifier.pkl"))
    return {"message": "Classifier trained successfully", "classes": len(pipeline.classes_)}


def classify_resume(text: str) -> str:
    model_path = os.path.join(_MODELS_DIR, "classifier.pkl")
    if not os.path.exists(model_path):
        return "Model not trained — POST /api/ml/train first"
    pipeline = joblib.load(model_path)
    return str(pipeline.predict([text])[0])


def train_fake_detector(csv_path: str) -> dict:
    """Train a fake resume detector."""
    if not ML_AVAILABLE:
        return {"error": "scikit-learn not available"}
        
    from sklearn.ensemble import IsolationForest
    from sklearn.feature_extraction.text import TfidfVectorizer
    import pandas as pd

    if not os.path.exists(csv_path):
        # Fallback to normal dataset
        csv_path = csv_path.replace("fake_resume_dataset.csv", "resume_dataset.csv")
        if not os.path.exists(csv_path):
            return {"error": "No dataset found to train detector"}

    df = pd.read_csv(csv_path)
    df['text'] = df.get('skills', '').fillna('') + " " + df.get('summary', '').fillna('') + " " + df.get('education', '').fillna('')
    df = df.dropna(subset=['text'])
    
    if df.empty:
         return {"error": "No data available."}
         
    vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
    X = vectorizer.fit_transform(df['text'])
    
    # Train Isolation Forest
    clf = IsolationForest(contamination=0.05, random_state=42)
    clf.fit(X)
    
    os.makedirs(_MODELS_DIR, exist_ok=True)
    joblib.dump({"vectorizer": vectorizer, "model": clf}, os.path.join(_MODELS_DIR, "fake_detector.pkl"))
    return {"message": "Fake detector trained successfully"}


def detect_fake_resume(text: str) -> dict:
    # 1. Heuristics
    words = len(text.split())
    skills_extracted = extract_skills(text)["flat"]
    
    flags = []
    if words < 50:
        flags.append("Too short")
    if len(skills_extracted) > 40:
        flags.append("Suspiciously high number of skills (Keyword stuffing)")
    
    # 2. ML checks
    fake_model_path = os.path.join(_MODELS_DIR, "fake_detector.pkl")
    ml_flag = False
    if os.path.exists(fake_model_path):
        detector = joblib.load(fake_model_path)
        vectorizer = detector["vectorizer"]
        model = detector["model"]
        
        try:
            X_score = model.predict(vectorizer.transform([text]))[0]
            if X_score == -1: # -1 indicates anomaly
                ml_flag = True
                flags.append("Structural anomaly detected by ML model")
        except Exception:
            pass
            
    is_fake = len(flags) > 0
    return {
        "is_fake": is_fake,
        "flags": flags,
        "confidence": "High" if len(flags) > 1 else ("Medium" if is_fake else "Low")
    }
