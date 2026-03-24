# 🤖 AI Resume Analyzer — Flask Backend

A fully local, ML-powered resume screening API.
Supports PDF/DOCX upload, CSV dataset ranking, skill extraction, and chart data generation.

---

## 📁 Project Structure

```
resume_analyzer/
│
├── app.py                  ← Flask API server (run this)
├── ml_engine.py            ← All ML logic (scoring, ranking, extraction)
├── generate_dataset.py     ← Generates 100-row fake resume dataset
├── requirements.txt        ← pip dependencies
│
├── dataset/
│   └── resume_dataset.csv  ← Generated after running generate_dataset.py
│
├── uploads/                ← Uploaded files stored here temporarily
├── static/                 ← (optional) static files
└── templates/              ← (optional) HTML templates
```

---

## ⚙️ Setup (VS Code)

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Generate the resume dataset
```bash
python generate_dataset.py
```
This creates `dataset/resume_dataset.csv` with **100 realistic fake resumes**.

### Step 3 — Start the Flask server
```bash
python app.py
```
Server runs at: **http://127.0.0.1:5000**

---

## 🌐 API Endpoints

### Health Check
```
GET /health
```

---

### 1. Analyze a Single Resume (File Upload)
```
POST /api/analyze
Content-Type: multipart/form-data

Fields:
  file   — resume file (.pdf / .docx / .txt)
```

**Example (curl):**
```bash
curl -X POST http://127.0.0.1:5000/api/analyze \
  -F "file=@my_resume.pdf"
```

**Returns:**
```json
{
  "status": "success",
  "analysis": {
    "filename": "my_resume.pdf",
    "contact": { "email": "...", "phone": "..." },
    "experience_years": 4,
    "education": { "highest": "MASTER", "score": 4 },
    "skills": {
      "by_category": { "Programming Languages": ["python", "java"], ... },
      "flat": ["python", "java", "sql", ...]
    },
    "scores": {
      "ats_score": 82,
      "readability": 79,
      "complexity": 67
    },
    "section_quality": {
      "Summary/Objective": 90,
      "Experience": 85,
      "Education": 90,
      "Skills": 95,
      "Projects": 80,
      "Certifications": 75
    },
    "sentiment": { "positive": 72, "neutral": 20, "negative": 8 },
    "word_count": 423
  },
  "charts": {
    "skills_by_category": { "labels": [...], "data": [...] },
    "section_quality":    { "labels": [...], "data": [...] },
    "sentiment":          { "labels": [...], "data": [...] }
  }
}
```

---

### 2. Analyze Resume from Text
```
POST /api/analyze/text
Content-Type: application/json

Body:
{
  "text": "John Doe... Python developer with 5 years experience...",
  "filename": "john_doe.txt"
}
```

---

### 3. Rank Multiple Uploaded Resumes
```
POST /api/rank
Content-Type: multipart/form-data

Fields:
  files[]          — multiple resume files
  job_description  — plain text job description
  top_n            — (optional) number of results, default 10
```

**Example (curl):**
```bash
curl -X POST http://127.0.0.1:5000/api/rank \
  -F "files[]=@resume1.pdf" \
  -F "files[]=@resume2.docx" \
  -F "files[]=@resume3.pdf" \
  -F "job_description=Python developer with machine learning and SQL" \
  -F "top_n=5"
```

**Returns:**
```json
{
  "status": "success",
  "total_processed": 3,
  "ranked": [
    {
      "filename": "resume1.pdf",
      "match_score": 78,
      "keyword_score": 35,
      "skill_score": 38,
      "skills": ["python", "sql", "tensorflow"],
      "matched_keywords": ["python", "machine", "learning", "sql"],
      "matched_skills": ["python", "sql"]
    }, ...
  ],
  "charts": {
    "ranking": { "labels": [...], "match_scores": [...] },
    "skill_distribution": { "labels": [...], "data": [...] }
  }
}
```

---

### 4. Rank from CSV Dataset
```
POST /api/rank/dataset
Content-Type: application/json

Body:
{
  "job_description": "Data Scientist with Python, TensorFlow, and SQL",
  "top_n": 10
}
```

**Example (curl):**
```bash
curl -X POST http://127.0.0.1:5000/api/rank/dataset \
  -H "Content-Type: application/json" \
  -d '{"job_description": "Python Machine Learning engineer with TensorFlow", "top_n": 5}'
```

---

### 5. List Dataset Candidates
```
GET /api/dataset/list?role=data+scientist&limit=10&offset=0
```

---

### 6. Dataset Statistics
```
GET /api/dataset/stats
```

Returns role distribution, education breakdown, top skills, average experience.

---

### 7. Get Single Candidate
```
GET /api/candidate/CAND001
```

---

### 8. Extract Skills from Text
```
POST /api/skills/extract
Content-Type: application/json

Body: { "text": "I know Python, React, Docker and Kubernetes" }
```

---

### 9. List All Supported Skills
```
GET /api/skills/list
```

---

## 📊 Chart Data Format

All chart endpoints return ready-to-plot data:

```json
"charts": {
  "ranking": {
    "labels":         ["resume1.pdf", "resume2.pdf"],
    "match_scores":   [78, 65],
    "skill_scores":   [38, 30],
    "keyword_scores": [35, 28]
  },
  "skill_distribution": {
    "labels": ["python", "sql", "react"],
    "data":   [5, 4, 3]
  }
}
```

You can feed these directly into Chart.js, Matplotlib, Plotly, etc.

---

## 🔧 Testing with Python requests

```python
import requests

# Analyze a resume
with open("my_resume.pdf", "rb") as f:
    r = requests.post("http://127.0.0.1:5000/api/analyze", files={"file": f})
print(r.json())

# Rank from dataset
r = requests.post("http://127.0.0.1:5000/api/rank/dataset", json={
    "job_description": "Senior Python developer with AWS and Docker",
    "top_n": 5
})
print(r.json())
```

---

## 📋 CSV Dataset Columns

| Column           | Description                          |
|------------------|--------------------------------------|
| candidate_id     | Unique ID (CAND001 … CAND100)        |
| name             | Candidate full name                  |
| role             | Job role / title                     |
| experience_years | Years of work experience             |
| skills           | Semicolon-separated skill list       |
| education        | Highest degree                       |
| certifications   | Certifications (semicolon-separated) |
| last_company     | Last employer                        |
| ats_score        | Pre-assigned ATS score               |
| summary          | Short professional summary           |

---

## 💡 Tips

- Run `python generate_dataset.py` first — required for `/api/rank/dataset`
- Upload `.txt` files if you don't have PDF/DOCX libraries installed
- Use `GET /health` to check which backends are active
- All endpoints return `{"status": "success"|"error", ...}`
