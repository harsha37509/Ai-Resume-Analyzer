# 🤖 AI Resume Analyzer - Implementation & Architecture Guide

## 📁 Project File Structure

```
resume analyzer/
│
├── 📄 app.py                    ← FLASK BACKEND (Web Server)
├── 📄 ml_engine.py              ← ML MODEL (AI Logic)
├── 📄 generate_dataset.py       ← Dataset Generator
├── 📄 requirements.txt           ← Python Dependencies
├── 📄 frontend.html              ← WEBSITE (User Interface)
├── 📄 README.md                  ← Documentation
│
├── 📁 dataset/
│   └── resume_dataset.csv       ← 100 Resume Records
│
├── 📁 uploads/                  ← Temporary File Storage
├── 📁 static/                   ← Static Files (empty)
└── 📁 templates/                ← Templates (empty)
```

---

## 🏗️ How Everything Works Together

### **Architecture Flow:**

```
User Opens Website (frontend.html)
           ↓
User Enters Resume Text / Job Description
           ↓
JavaScript in Website Sends HTTP Request
           ↓
Flask API Server (app.py) Receives Request
           ↓
Flask Calls ML Model (ml_engine.py)
           ↓
ML Model Analyzes Resume / Ranks Candidates
           ↓
Results Sent Back to Website
           ↓
Website Displays Results with Charts & Data
```

---

## 🎯 What Each File Does

### **1️⃣ `ml_engine.py` - THE ML MODEL**
**Location:** `c:\Users\hp\OneDrive\Desktop\resume analyzer\ml_engine.py`

**What it contains:**
```python
✅ SKILL_CATEGORIES - 9 categories of 50+ skills
✅ extract_skills() - Detects skills in text
✅ extract_experience() - Calculates years of experience
✅ extract_education() - Identifies education level
✅ calculate_match_score() - Matches resume to job description
✅ extract_contact_info() - Finds email/phone
✅ analyze_resume() - Complete resume analysis
✅ rank_dataset_by_jd() - Ranks candidates by job fit
✅ Chart builders - Creates data for visualizations
```

**ML Features:**
- Regular expression pattern matching for skills
- Keyword extraction and matching
- Score calculation (0-100)
- Experience estimation
- Education level detection
- Sentiment analysis (positive/negative words)
- Multi-candidate ranking

---

### **2️⃣ `app.py` - THE BACKEND SERVER**
**Location:** `c:\Users\hp\OneDrive\Desktop\resume analyzer\app.py`

**What it does:**
- Runs Flask web server on `http://127.0.0.1:5000`
- Provides 11 API endpoints
- Receives requests from website
- Calls ml_engine functions
- Returns JSON responses

**11 API Endpoints:**
```
GET  /                          → API documentation
GET  /health                    → Server status
POST /api/analyze/text          → Analyze resume text
POST /api/rank/dataset          → Rank candidates
GET  /api/dataset/list          → List candidates
GET  /api/dataset/stats         → Dataset statistics
GET  /api/candidate/<id>        → Get single candidate
POST /api/skills/extract        → Extract skills
GET  /api/skills/list           → List all skills
```

---

### **3️⃣ `frontend.html` - THE WEBSITE**
**Location:** `c:\Users\hp\OneDrive\Desktop\resume analyzer\frontend.html`

**What it does:**
- Beautiful responsive website
- 5 tabs (Analyze, Rank, Dataset, Skills, Health)
- JavaScript code that calls API endpoints
- Displays results with charts

**JavaScript Functions in Website:**
```javascript
✅ analyzeResume()        → Calls /api/analyze/text
✅ rankDataset()          → Calls /api/rank/dataset
✅ getDatasetStats()      → Calls /api/dataset/stats
✅ listDatasetCandidates()→ Calls /api/dataset/list
✅ extractSkills()        → Calls /api/skills/extract
✅ drawChart()            → Draws Chart.js visualizations
✅ checkHealth()          → Calls /health
```

---

### **4️⃣ `dataset/resume_dataset.csv` - DATA**
**Location:** `c:\Users\hp\OneDrive\Desktop\resume analyzer\dataset\resume_dataset.csv`

**Contains:**
- 100 realistic fake resume records
- Columns: candidate_id, name, role, experience_years, skills, education, certifications, last_company, ats_score, summary
- Used for ranking candidates

---

## 📊 Data Flow Example: Analyzing a Resume

### **Step-by-Step:**

#### **1. User Types Resume Text in Website**
```
Resume: "John Doe, Python developer with 5 years AWS and Docker"
```

#### **2. Website JavaScript Sends HTTP Request**
```javascript
// In frontend.html
fetch('http://127.0.0.1:5000/api/analyze/text', {
    method: 'POST',
    body: JSON.stringify({
        text: "John Doe, Python developer with 5 years AWS and Docker",
        filename: 'resume.txt'
    })
})
```

#### **3. Flask Server (app.py) Receives Request**
```python
@app.route("/api/analyze/text", methods=["POST"])
def analyze_text_endpoint():
    body = request.get_json()
    text = body["text"]
```

#### **4. Flask Calls ML Model (ml_engine.py)**
```python
result = analyze_resume(text, filename)
```

#### **5. ML Model Processes Text**
```python
# ml_engine.py
def analyze_resume(text):
    # Extract skills
    skills = extract_skills(text)
    # Skills found: ["python", "aws", "docker"]
    
    # Calculate experience
    experience = extract_experience(text)
    # Returns: 5 years
    
    # Calculate scores
    ats = compute_ats_score(text, skills)
    # Returns: 75/100
    
    # Return complete analysis
    return {
        "skills": {"flat": ["python", "aws", "docker"], ...},
        "experience_years": 5,
        "scores": {"ats_score": 75, ...},
        ...
    }
```

#### **6. Flask Returns JSON Response**
```json
{
    "status": "success",
    "analysis": {
        "skills": ["python", "aws", "docker"],
        "experience_years": 5,
        "scores": {
            "ats_score": 75,
            "readability": 82,
            "complexity": 58
        },
        ...
    },
    "charts": {
        "skills_by_category": {...},
        "section_quality": {...},
        ...
    }
}
```

#### **7. Website Receives Data**
```javascript
const data = await response.json();
```

#### **8. Website Displays Results**
```
✅ Resume analyzed successfully!

ATS Score: 75/100
Readability: 82/100
Complexity: 58/100

Skills Found:
• python
• aws
• docker

[Chart visualization appears]
```

---

## 🎬 Data Flow Example: Ranking Candidates

### **User Enters Job Description**
```
"Senior Python engineer with Docker and Kubernetes"
```

### **Website Calls API**
```javascript
fetch('http://127.0.0.1:5000/api/rank/dataset', {
    method: 'POST',
    body: JSON.stringify({
        job_description: "Senior Python engineer with Docker and Kubernetes",
        top_n: 10
    })
})
```

### **Flask Calls ML Model**
```python
# app.py
ranked = rank_dataset_by_jd(dataset, jd, top_n=10)
```

### **ML Model Processes Each Candidate**
```python
# ml_engine.py - For each of 100 candidates
for candidate in dataset:
    # Get candidate data
    combined_text = candidate['role'] + candidate['skills'] + ...
    
    # Calculate match score
    match = calculate_match_score(combined_text, job_description, skills)
    
    # Extract matched skills
    matched_skills = ["python", "docker"]
    matched_keywords = ["senior", "engineer", "python"]
    
    # Save result with score
    results.append({
        "name": "Omar Sanders",
        "match_score": 85,
        "matched_skills": ["python", "docker"],
        "matched_keywords": ["senior", "engineer"]
    })

# Sort by score
results.sort(by=match_score, reverse=True)
# Return top 10
```

### **Website Displays Ranked Results**
```
#1 - Omar Sanders
Score: 85/100
Matched Skills: python, docker
Matched Keywords: senior, engineer, python

#2 - Frank Miller
Score: 78/100
...
```

---

## 🔍 Where is the ML Model Used?

### **On Website - 5 Tabs:**

#### **Tab 1: 📄 Analyze Resume**
```
ML Model Used: ✅ analyze_resume()
- Extract skills
- Calculate ATS score
- Detect experience
- Analyze sections
- Sentiment analysis
```

#### **Tab 2: 🏆 Rank Resumes**
```
ML Model Used: ✅ rank_dataset_by_jd()
- Match resume to job description
- Calculate match scores
- Extract matched skills
- Rank candidates
```

#### **Tab 3: 📊 Dataset**
```
ML Model Used: ✅ load_dataset()
- Load 100 candidates
- Calculate statistics
```

#### **Tab 4: 🔍 Skills**
```
ML Model Used: ✅ extract_skills()
- Detect skills in text
- Categorize by type
```

#### **Tab 5: 💚 Health**
```
No ML Used - just checks API status
```

---

## 🚀 How to Run Everything

### **Terminal 1: Start Flask API**
```bash
cd "c:\Users\hp\OneDrive\Desktop\resume analyzer"
python app.py
```

Output:
```
🤖  AI Resume Analyzer — Flask API
═══════════════════════════════════════════════════
🚀  Server starting at http://127.0.0.1:5000
```

### **Terminal 2: Open Website**
```
Double-click: frontend.html
OR
Right-click → Open with → Chrome/Firefox
```

### **Use the Website**
Window will open showing 5 tabs with full functionality

---

## 📋 ML Model Algorithms Used

### **Skill Extraction**
```python
Pattern: Regular Expression word boundary matching
Example: r'\bpython\b' matches "python" but not "pythonic"
```

### **Experience Calculation**
```python
Patterns:
1. "5 years of experience"
2. "2019 to 2024 (5 years)"
3. Count "senior", "lead", "manager" indicators
```

### **Match Scoring (0-100)**
```
Formula: keyword_score (45) + skill_score (45) + experience_bonus (10)

Keyword Score: Count JD keywords found in resume
Skill Score: Count matched skills
Experience Bonus: Bonus for matching years required
```

### **ATS Score**
```
Base: 40 points
+ Skills (up to 25): +2 per skill
+ Sections (up to 21): +3 per section found
+ Length (up to 5): +5 if 200-1500 words
= Total (max 100)
```

---

## 🎯 Summary

| Component | Location | Purpose | ML Used |
|-----------|----------|---------|---------|
| **ML Model** | `ml_engine.py` | Extract & analyze data | ✅ Yes |
| **Backend** | `app.py` | Serve API endpoints | ❌ No |
| **Frontend** | `frontend.html` | User interface | ❌ No |
| **Data** | `resume_dataset.csv` | 100 candidates | ❌ No |

---

## 📞 Questions?

**Q: Is the ML model running on the website?**
A: No, the ML model runs on the **backend server (Flask)**. The website is just a user interface that sends requests to the backend.

**Q: Where does analysis happen?**
A: All analysis happens in `ml_engine.py` when Flask calls its functions.

**Q: Can I see the ML code?**
A: Yes, open `ml_engine.py` to see all skill extraction, matching, and scoring functions.

**Q: Can I modify the ML model?**
A: Yes! Edit `ml_engine.py` and restart Flask to see changes.

**Q: Are the 100 candidates real?**
A: No, they're fake data generated by `generate_dataset.py` for testing.
