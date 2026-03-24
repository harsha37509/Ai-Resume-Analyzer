"""
app.py — AI Resume Analyzer Flask Backend
Run: python app.py
API: http://127.0.0.1:5000
"""

import os, io, json
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# ── PDF / DOCX parsing ────────────────────────────────────────────────────────
try:
    import pdfplumber
    PDF_BACKEND = "pdfplumber"
except ImportError:
    pdfplumber = None
    PDF_BACKEND = None

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


from ml_engine import (
    extract_text_from_file, analyze_resume,
    calculate_match_score, extract_skills, extract_experience, extract_education,
    rank_dataset, load_csv,
    train_classifier, classify_resume,
    train_fake_detector, detect_fake_resume,
    chart_skills_by_category, chart_section_quality, chart_sentiment,
    chart_ranking, chart_skill_distribution,
    SKILL_CATEGORIES, compute_ats_score
)

# ─── Config ───────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATASET_PATH  = os.path.join(BASE_DIR, "dataset", "resume_dataset.csv")
FAKE_DS_PATH  = os.path.join(BASE_DIR, "dataset", "fake_resume_dataset.csv")
ALLOWED       = {"pdf","docx","doc","txt"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "models"), exist_ok=True)

app = Flask(__name__, static_folder=BASE_DIR)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

# ─── Manual CORS (no flask-cors needed) ──────────────────────────────────────
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>",              methods=["OPTIONS"])
def handle_options(path):
    return jsonify({}), 200

# ─── Helpers ─────────────────────────────────────────────────────────────────
def ok(data, status=200):
    return jsonify({"status":"success", **data}), status

def err(msg, status=400):
    return jsonify({"status":"error", "message": msg}), status

def allowed(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED

# ─── Serve HTML frontend ─────────────────────────────────────────────────────
@app.route("/app")
def serve_app():
    """Serve the HTML frontend."""
    return send_from_directory(BASE_DIR, "index.html")

# ─────────────────────────────────────────────────────────────────────────────
#  HEALTH + DOCS
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    dataset_count, fake_dataset_count = 0, 0
    if os.path.exists(DATASET_PATH):
        with open(DATASET_PATH) as f: dataset_count = sum(1 for _ in f) - 1
    if os.path.exists(FAKE_DS_PATH):
        with open(FAKE_DS_PATH) as f: fake_dataset_count = sum(1 for _ in f) - 1

    return ok({
        "name":    "AI Resume Analyzer API v3.0",
        "dataset": f"{dataset_count} candidates (25 job categories)",
        "fake_dataset": f"{fake_dataset_count} resumes (Real + Fake)",
        "endpoints": {
            "POST /api/analyze":              "Analyze single resume (file upload)",
            "POST /api/analyze/text":         "Analyze resume from raw text (JSON)",
            "POST /api/rank":                 "Rank multiple uploaded resumes vs JD",
            "POST /api/rank/dataset":         "Rank CSV dataset vs JD",
            "GET  /api/dataset/list":         "List all dataset candidates",
            "GET  /api/dataset/stats":        "Dataset statistics",
            "GET  /api/candidate/<id>":       "Get single candidate by ID",
            "POST /api/ml/train":             "Train classifier + fake detector",
            "POST /api/ml/classify":          "Classify resume job category (file)",
            "POST /api/ml/classify/text":     "Classify resume job category (text)",
            "POST /api/ml/fake-detect":       "Detect fake resume (file)",
            "POST /api/ml/fake-detect/text":  "Detect fake resume (text)",
            "GET  /api/skills/list":          "All supported skills by category",
            "POST /api/skills/extract":       "Extract skills from text",
        },
        "install": "pip install flask scikit-learn pandas numpy pdfplumber python-docx",
        "run":     "python app.py"
    })

@app.route("/health")
def health():
    import os as _os
    return ok({
        "healthy":         True,
        "dataset_loaded":  _os.path.exists(DATASET_PATH),
        "fake_ds_loaded":  _os.path.exists(FAKE_DS_PATH),
        "classifier_trained":     _os.path.exists("models/classifier.pkl"),
        "fake_detector_trained":  _os.path.exists("models/fake_detector.pkl"),
    })

# ─────────────────────────────────────────────────────────────────────────────
#  SINGLE RESUME ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/analyze", methods=["POST"])
def analyze_file():
    if "file" not in request.files:
        return err("No file. Use form-field: 'file'")
    f = request.files["file"]
    if not f.filename or not allowed(f.filename):
        return err(f"Unsupported type. Allowed: {ALLOWED}")

    text   = extract_text_from_file(f, pdfplumber, DOCX_AVAILABLE, DocxDocument)
    result = analyze_resume(text, f.filename)
    charts = {
        "skills_by_category": chart_skills_by_category(result["skills"]["by_category"]),
        "section_quality":    chart_section_quality(result["section_quality"]),
        "sentiment":          chart_sentiment(result["sentiment"]),
    }
    return ok({"analysis": result, "charts": charts})

@app.route("/api/analyze/text", methods=["POST"])
def analyze_text():
    body = request.get_json(silent=True)
    if not body or "text" not in body:
        return err("JSON body must have 'text' field")
    text   = body["text"]
    result = analyze_resume(text, body.get("filename","resume.txt"))
    charts = {
        "skills_by_category": chart_skills_by_category(result["skills"]["by_category"]),
        "section_quality":    chart_section_quality(result["section_quality"]),
        "sentiment":          chart_sentiment(result["sentiment"]),
    }
    return ok({"analysis": result, "charts": charts})

# ─────────────────────────────────────────────────────────────────────────────
#  RANKING — UPLOADED FILES
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/rank", methods=["POST"])
def rank_files():
    files = request.files.getlist("files[]")
    jd    = request.form.get("job_description","").strip()
    top_n = int(request.form.get("top_n", 10))

    if not jd:   return err("'job_description' required")
    if not files: return err("No files. Use form-field: 'files[]'")

    results, errors = [], []
    for f in files:
        if not f.filename or not allowed(f.filename):
            errors.append(f"Skipped: {f.filename}"); continue
        try:
            text   = extract_text_from_file(f, pdfplumber, DOCX_AVAILABLE, DocxDocument)
            skills = extract_skills(text)["flat"]
            match  = calculate_match_score(text, jd, skills)
            results.append({
                "filename":         f.filename,
                "match_score":      match["total"],
                "keyword_score":    match["keyword_score"],
                "skill_score":      match["skill_score"],
                "exp_bonus":        match["exp_bonus"],
                "experience_years": extract_experience(text),
                "education":        extract_education(text)["highest"],
                "skills":           skills,
                "skills_count":     len(skills),
                "matched_keywords": match["matched_keywords"],
                "matched_skills":   match["matched_skills"],
            })
        except Exception as e:
            errors.append(f"Error {f.filename}: {e}")

    results.sort(key=lambda x: x["match_score"], reverse=True)
    top    = results[:top_n]
    charts = {"ranking": chart_ranking(top), "skill_distribution": chart_skill_distribution(top)}
    return ok({"total_processed": len(results), "top_n": top_n, "ranked": top,
               "charts": charts, "errors": errors})

# ─────────────────────────────────────────────────────────────────────────────
#  RANKING — CSV DATASET
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/rank/dataset", methods=["POST"])
def rank_from_dataset():
    body  = request.get_json(silent=True) or {}
    jd    = (body.get("job_description") or request.form.get("job_description","")).strip()
    top_n = int(body.get("top_n") or request.form.get("top_n", 10))

    if not jd: return err("'job_description' required")

    dataset = load_csv(DATASET_PATH)
    if not dataset:
        return err(f"Dataset not found. Run: python generate_dataset.py")

    ranked = rank_dataset(dataset, jd, top_n)
    charts = {"ranking": chart_ranking(ranked), "skill_distribution": chart_skill_distribution(ranked)}
    return ok({"job_description": jd, "total_in_dataset": len(dataset),
               "top_n": top_n, "ranked": ranked, "charts": charts})

# ─────────────────────────────────────────────────────────────────────────────
#  DATASET UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/dataset/list")
def list_dataset():
    dataset = load_csv(DATASET_PATH)
    if not dataset: return err("Dataset not found. Run generate_dataset.py")

    role   = request.args.get("role","").strip().lower()
    limit  = int(request.args.get("limit", 20))
    offset = int(request.args.get("offset", 0))

    if role:
        dataset = [r for r in dataset if role in r.get("category","").lower() or role in r.get("role","").lower()]
    total = len(dataset)
    paged = dataset[offset:offset+limit]
    return ok({"total": total, "limit": limit, "offset": offset, "candidates": paged})

@app.route("/api/dataset/stats")
def dataset_stats():
    dataset = load_csv(DATASET_PATH)
    if not dataset: return err("Dataset not found")
    from collections import Counter
    cats  = Counter(r.get("category", r.get("role", "Unknown")) for r in dataset)
    edu   = Counter(r.get("education","") for r in dataset)
    exp_vals = [int(r["experience_years"]) for r in dataset if str(r.get("experience_years","")).isdigit()]
    avg_exp  = round(sum(exp_vals)/len(exp_vals),1) if exp_vals else 0
    sk = Counter()
    for r in dataset:
        for s in r.get("skills","").split(";"):
            if s.strip(): sk[s.strip().lower()] += 1
    return ok({"total": len(dataset), "avg_experience": avg_exp,
               "categories": dict(cats.most_common()),
               "education":  dict(edu.most_common()),
               "top_skills": dict(sk.most_common(20))})

@app.route("/api/candidate/<cid>")
def get_candidate(cid):
    for row in load_csv(DATASET_PATH):
        if row.get("candidate_id","").upper() == cid.upper():
            return ok({"candidate": row})
    return err(f"Candidate '{cid}' not found", 404)

# ─────────────────────────────────────────────────────────────────────────────
#  ML — TRAIN BOTH MODELS
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/ml/train", methods=["POST"])
def train_models():
    """Train classifier + fake detector from CSV datasets."""
    c_result = train_classifier(DATASET_PATH)
    f_result = train_fake_detector(FAKE_DS_PATH)
    return ok({"classifier": c_result, "fake_detector": f_result})

# ─────────────────────────────────────────────────────────────────────────────
#  ML — RESUME CLASSIFICATION
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/ml/classify", methods=["POST"])
def classify_file():
    if "file" not in request.files:
        return err("No file. Use form-field: 'file'")
    f = request.files["file"]
    if not allowed(f.filename): return err("Unsupported file type")
    text   = extract_text_from_file(f, pdfplumber, DOCX_AVAILABLE, DocxDocument)
    result = classify_resume(text)
    return ok({"filename": f.filename, "classification": result})

@app.route("/api/ml/classify/text", methods=["POST"])
def classify_text():
    body = request.get_json(silent=True)
    if not body or "text" not in body: return err("JSON body needs 'text'")
    return ok({"classification": classify_resume(body["text"])})

# ─────────────────────────────────────────────────────────────────────────────
#  ML — FAKE RESUME DETECTION
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/ml/fake-detect", methods=["POST"])
def fake_detect_file():
    if "file" not in request.files:
        return err("No file. Use form-field: 'file'")
    f = request.files["file"]
    if not allowed(f.filename): return err("Unsupported file type")
    text   = extract_text_from_file(f, pdfplumber, DOCX_AVAILABLE, DocxDocument)
    result = detect_fake_resume(text)
    return ok({"filename": f.filename, "fake_detection": result})

@app.route("/api/ml/fake-detect/text", methods=["POST"])
def fake_detect_text():
    body = request.get_json(silent=True)
    if not body or "text" not in body: return err("JSON body needs 'text'")
    return ok({"fake_detection": detect_fake_resume(body["text"])})

# ─────────────────────────────────────────────────────────────────────────────
#  SKILLS
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/skills/list")
def skills_list():
    total = sum(len(v) for v in SKILL_CATEGORIES.values())
    return ok({"total": total, "categories": SKILL_CATEGORIES})

@app.route("/api/skills/extract", methods=["POST"])
def skills_extract():
    body = request.get_json(silent=True)
    if not body or "text" not in body: return err("JSON body needs 'text'")
    result = extract_skills(body["text"])
    return ok({"by_category": result["by_category"], "all_skills": result["flat"],
               "total": len(result["flat"])})

# ─────────────────────────────────────────────────────────────────────────────
#  KAGGLE DATASET LOADER HELPER
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/kaggle/load", methods=["POST"])
def kaggle_load():
    """
    Load a real Kaggle resume dataset CSV uploaded by the user.
    Form field: file (CSV with columns: resume, category)
    The CSV is merged with the local dataset.
    """
    if "file" not in request.files:
        return err("No file. Upload a Kaggle CSV with form-field: 'file'")
    f       = request.files["file"]
    raw     = f.read().decode("utf-8", errors="ignore")
    import csv, io as _io
    reader  = csv.DictReader(_io.StringIO(raw))
    rows    = list(reader)
    if not rows:
        return err("CSV is empty or unreadable")

    # Detect columns
    cols = list(rows[0].keys())
    resume_col   = next((c for c in cols if "resume" in c.lower()),   None)
    category_col = next((c for c in cols if "categor" in c.lower() or "label" in c.lower()), None)

    if not resume_col:
        return err(f"Could not find 'resume' column. Found columns: {cols}")

    # Normalize rows
    normalized = []
    for i, row in enumerate(rows):
        resume_text  = row.get(resume_col,"")
        category     = row.get(category_col,"Unknown") if category_col else "Unknown"
        if not resume_text.strip(): continue
        skills_found = extract_skills(resume_text)["flat"]
        exp          = extract_experience(resume_text)
        edu          = extract_education(resume_text)
        normalized.append({
            "candidate_id":    f"KG{i+1:04d}",
            "name":            f"Kaggle Candidate {i+1}",
            "role":            category.strip(),
            "experience_years":exp,
            "skills":          "; ".join(skills_found),
            "education":       edu["highest"],
            "certifications":  "From Kaggle dataset",
            "last_company":    "Unknown",
            "ats_score":       compute_ats_score(resume_text, skills_found),
            "summary":         resume_text[:200]
        })

    # Save merged to DATASET_PATH
    existing = load_csv(DATASET_PATH) if os.path.exists(DATASET_PATH) else []
    merged = existing + normalized
    
    with open(DATASET_PATH, "w", newline="", encoding="utf-8") as out:
        if merged:
            writer = csv.DictWriter(out, fieldnames=list(merged[0].keys()))
            writer.writeheader()
            writer.writerows(merged)

    return ok({"message": f"Loaded {len(normalized)} candidates from Kaggle."})

# ─── Error Handlers ───────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return err("Endpoint not found. GET / for API docs.", 404)

@app.errorhandler(413)
def too_large(e):
    return err("File too large. Maximum size is 20 MB.", 413)

@app.errorhandler(500)
def server_error(e):
    import traceback
    traceback.print_exc()
    return err(f"Internal server error: {str(e)}", 500)

# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  AI Resume Analyzer — Flask API")
    print("="*55)
    print(f"  Upload folder : {UPLOAD_FOLDER}")
    print(f"  Dataset path  : {DATASET_PATH}")
    print(f"  PDF backend   : {PDF_BACKEND or 'unavailable'}")
    print(f"  DOCX backend  : {'python-docx' if DOCX_AVAILABLE else 'unavailable'}")
    print(f"\n  Server starting at http://127.0.0.1:5000")
    print("="*55 + "\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
