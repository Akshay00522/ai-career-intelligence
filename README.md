# AI Career Intelligence & Skill-Gap Analyzer

Compare a resume with a job description and get:

- A **match score (0–100)** with a transparent breakdown.
- **Required and preferred skills** you match or miss, understanding that scikit-learn implies machine learning and that "FastAPI or Flask" needs only one.
- A **learning plan**: missing skills ordered with prerequisites first, effort estimates, free resources, and a practice project for each.
- Optional **job-market demand** from a folder of postings, used to prioritise what to learn.

Works from the command line, as a REST API, or in a Streamlit web app. Reads `.txt`, `.md`, `.pdf`, and `.docx` resumes.

## Live Demo

Try the deployed application: [AI Career Intelligence & Skill-Gap Analyzer](https://ai-career-intelligence-canppethsu2ikstdq96n7h.streamlit.app/)

Upload a resume in PDF, DOCX, TXT, or Markdown format, enter a job description, and review the match score, matched and missing skills, and suggested learning plan.
### Example Analysis

![AI Career Intelligence — Resume Analysis Results](docs/screenshots/analysis-results.png)

## Quick start

```bash
python -m venv .venv

# Activate the environment:
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# macOS/Linux:
source .venv/bin/activate

pip install -r requirements-dev.txt -r requirements-ui.txt

pytest -q
python cli.py analyze samples/resume.txt samples/jd.txt
streamlit run ui/streamlit_app.py
uvicorn src.app:app --reload
docker compose up --build
```

- Streamlit web app: [http://localhost:8501](http://localhost:8501)
- FastAPI Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Only the CLI needs `pip install -r requirements.txt` (scikit-learn and NumPy).

## Usage

```bash
# Analyze a PDF, DOCX, or TXT resume.
# --hours sets study time per week; --market-dir ranks skills by demand.
python cli.py analyze my_resume.pdf job.txt --hours 8 --market-dir data/eval/jobs --report report.md

# Evaluate the scorer on the labelled benchmark.
python cli.py evaluate --write-report docs/EVALUATION.md --min-spearman 0.60 --min-auc 0.85

# Find the skills most in demand across a folder of job descriptions.
python cli.py market data/eval/jobs --top 15
```

### REST API

Analyze resume and job-description text using the API:

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "...",
    "jd_text": "...",
    "hours_per_week": 8
  }'
```

Upload a resume file and provide job-description text:

```bash
curl -X POST http://127.0.0.1:8000/analyze/upload \
  -F "resume=@my_resume.pdf" \
  -F "jd_text=$(cat job.txt)"
```

## How it works

```text
resume + JD
     |
   parsers
     |
 skill extraction
     |
 requirements (required / preferred, alternative "or" groups)
     |
 implication expansion + coverage per section
     |
 weighted score <-- text similarity (TF-IDF or embeddings)
     |
 gap report
     |
 learning plan (prerequisites, effort, resources, market demand)
```

1. **Skill extraction** — A taxonomy of 67 skills with aliases (`data/skills.json`). Matching uses boundary-safe patterns so `Java` is not found inside `JavaScript`, `R` is not found in `R&D`, and `Azure ML` is classified as Azure rather than machine learning. The longest match wins.

2. **Implications** — Having PyTorch implies Python, deep learning, and machine learning, so a resume is not penalised for not repeating them. Skills matched this way are flagged in the report.

3. **Requirements** — The job description is split into required and nice-to-have sections. "FastAPI or Flask" and "AWS, GCP or Azure" become one requirement satisfied by any option, provided the alternatives share a skill category.

4. **Score** — `0.60 × required coverage + 0.15 × preferred coverage + 0.25 × text similarity`, with weights renormalised when a job description has no nice-to-have section.

5. **Learning plan** — Missing skills are ordered by importance and demand, with prerequisites such as Linux, Docker, and Kubernetes scheduled first. A prerequisite the candidate already has, or whose parent skill they have, is not repeated.

## Evaluation

The benchmark contains 56 hand-labelled resume/JD pairs (8 resumes × 7 roles, labels 0–3). See [docs/EVALUATION.md](docs/EVALUATION.md) for the full report.

| System | Spearman | AUC (good fit) |
|---|---:|---:|
| Skill overlap (Jaccard) | 0.640 | 0.871 |
| TF-IDF cosine only | 0.709 | 0.906 |
| Hybrid v0.1 (no implications, no OR groups) | 0.645 | 0.866 |
| Hybrid + implications | 0.672 | 0.902 |
| **Hybrid v1.0 (default)** | **0.693** | **0.914** |

### What the evaluation does and does not show

- Implications and OR groups each improved the hybrid (0.645 → 0.672 → 0.693 Spearman).
- **The hybrid does not beat plain TF-IDF at ranking** (0.693 vs. 0.709). Its advantage is explainability: it identifies matched and missing skills.
- The dataset is small, hand-written, and labelled by one person. Treat these numbers as a regression benchmark rather than proof of real-world accuracy.

## Project layout

```text
cli.py                    Command line (analyze / evaluate / market)
src/analyzer/              Skills, JD parser, parsers, similarity, pipeline,
                           learning, market, evaluation, report, service
src/app.py                 FastAPI service
ui/streamlit_app.py        Streamlit web app
data/skills.json           Skill taxonomy
data/resources.json        Learning resource catalogue
data/eval/                 Benchmark resumes, JDs, labels.csv
tests/                     Automated tests
docs/                      Architecture, evaluation, viva Q&A
Dockerfile                 Docker image configuration
docker-compose.yml         Container orchestration
.github/workflows/ci.yml   CI workflow
Makefile                   Development commands
```

## Status

### Deployment

- **Live demo:** Deployed on Streamlit Community Cloud.
- **Resume uploads:** PDF upload and the main analysis workflow have been verified in the deployed application.
- **Core workflow:** Match scoring, missing-skills analysis, and learning-plan generation have been checked.
- **Input validation:** Empty resumes, invalid PDF uploads, short resumes, and unrelated resume/job-description pairs have been tested.

### Testing and automation

- **Automated tests:** `pytest -q` — 81 tests passed in the latest confirmed run.
- **GitHub Actions:** CI checks passed, including the supported Python-version test matrix and benchmark quality gate.
- **Docker:** Image build passed in GitHub Actions.
- **FastAPI:** The API starts successfully, Swagger UI is accessible at `/docs`, and `POST /analyze` returned HTTP 200 for the tested input.

These results reflect the tests and checks completed so far; they do not guarantee that every possible input or deployment environment will behave identically.

Resource links in `data/resources.json` should be opened and checked before relying on them.

## Limitations and future work

- **Small skill taxonomy:** The current taxonomy contains 67 skills. Extend `data/skills.json` or consider integrating ESCO or O*NET.
- **Experience level:** Years of experience and proficiency levels are not modelled.
- **Skill phrasing:** Alias-based matching may miss skills described in different words, such as "built dashboards". An NER or LLM-based extractor could help.
- **Scanned PDFs:** Scanned documents require OCR.
- **Evaluation data:** The benchmark should be expanded with real, anonymised documents and labels from multiple annotators.
- **Similarity ranking:** The current hybrid scorer does not outperform plain TF-IDF on the reported ranking metrics. Further evaluation and tuning may help establish where the hybrid approach adds the most value.
