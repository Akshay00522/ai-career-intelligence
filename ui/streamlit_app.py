"""Streamlit front end for the AI Career Intelligence & Skill-Gap Analyzer."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st  # noqa: E402

from analyzer.parsers import UnsupportedFormat, read_document  # noqa: E402
from analyzer.report import to_markdown  # noqa: E402
from analyzer.service import run_analysis  # noqa: E402


# ---------------------------------------------------------
# Page configuration and visual identity
# ---------------------------------------------------------

st.set_page_config(
    page_title="Career Compass | Skill-Gap Analyzer",
    page_icon="🎯",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Palette: warm ivory, forest green and muted copper */
    :root {
        --ivory: #F4F0E7;
        --paper: #FFFEFA;
        --forest: #234638;
        --forest-light: #E6EEE8;
        --copper: #B77852;
        --ink: #26352D;
        --muted: #726F64;
        --line: #DED7C9;
        --soft-red: #F7E9E4;
    }

    .stApp {
        background-color: var(--ivory);
        color: var(--ink);
    }

    [data-testid="stHeader"] {
        background: rgba(244, 240, 231, 0.92);
    }

    [data-testid="stSidebar"] {
        background-color: #EAE5D9;
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--forest);
    }

    .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .brand-label {
        color: var(--copper);
        font-size: 0.76rem;
        font-weight: 750;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
    }

    .hero-title {
        color: var(--forest);
        font-size: clamp(2rem, 4vw, 3.1rem);
        font-weight: 750;
        letter-spacing: -0.045em;
        line-height: 1.12;
        margin: 0 0 0.8rem 0;
    }

    .hero-description {
        color: var(--muted);
        font-size: 1.02rem;
        line-height: 1.7;
        max-width: 760px;
        margin-bottom: 1.3rem;
    }

    .section-label {
        color: var(--copper);
        font-size: 0.74rem;
        font-weight: 750;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    .section-heading {
        color: var(--forest);
        font-size: 1.45rem;
        font-weight: 720;
        letter-spacing: -0.025em;
        margin: 0 0 0.45rem 0;
    }

    .section-description {
        color: var(--muted);
        font-size: 0.94rem;
        line-height: 1.6;
        margin-bottom: 1rem;
    }

    [data-testid="stMetric"] {
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 13px;
        padding: 1.15rem 1.2rem;
        box-shadow: 0 3px 12px rgba(35, 70, 56, 0.035);
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted);
    }

    [data-testid="stMetricValue"] {
        color: var(--forest);
        font-weight: 750;
    }

    [data-testid="stMetricDelta"] {
        color: var(--copper);
    }

    [data-testid="stTextArea"] textarea,
    [data-testid="stFileUploader"] section {
        background-color: var(--paper);
        border-color: var(--line);
        border-radius: 10px;
    }

    .stTextArea label,
    .stFileUploader label,
    .stRadio label,
    .stSlider label {
        color: var(--forest);
        font-weight: 600;
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 9px;
        font-weight: 650;
        min-height: 2.7rem;
        transition: all 0.15s ease;
    }

    .stButton > button[kind="primary"] {
        background-color: var(--forest);
        border: 1px solid var(--forest);
        color: white;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #315C49;
        border-color: #315C49;
        color: white;
    }

    .stDownloadButton > button {
        background: var(--paper);
        border: 1px solid var(--forest);
        color: var(--forest);
    }

    .stDownloadButton > button:hover {
        background: var(--forest-light);
        border-color: var(--forest);
        color: var(--forest);
    }

    [data-testid="stExpander"] {
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 10px;
    }

    [data-testid="stProgressBar"] > div > div {
        background-color: var(--forest);
    }

    hr {
        border-color: var(--line);
    }

    .result-panel {
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 13px;
        padding: 1.2rem 1.25rem;
        min-height: 155px;
    }

    .panel-heading {
        color: var(--forest);
        font-size: 1.08rem;
        font-weight: 720;
        margin-bottom: 0.7rem;
    }

    .panel-copy {
        color: var(--ink);
        line-height: 1.8;
        overflow-wrap: anywhere;
    }

    .status-note {
        color: var(--muted);
        font-size: 0.87rem;
        line-height: 1.6;
    }

    @media (max-width: 700px) {
        .block-container {
            padding-top: 1rem;
        }

        .hero-title {
            font-size: 2rem;
        }

        [data-testid="stMetric"] {
            padding: 0.8rem;
        }
    }

/* ---------- Accessibility and contrast fixes ---------- */

/* Keep text readable throughout the sidebar */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #34483D !important;
}

/* Make text inputs and placeholders readable */
.stTextArea textarea,
.stTextInput input {
    background-color: #FFFEFA !important;
    color: #26352D !important;
    border: 1px solid #C9C1B2 !important;
    caret-color: #234638 !important;
}

.stTextArea textarea::placeholder,
.stTextInput input::placeholder {
    color: #77766D !important;
    opacity: 1 !important;
}

/* Improve the file uploader's contrast */
[data-testid="stFileUploader"] section {
    background-color: #FFFEFA !important;
    border: 1px dashed #A9B7AA !important;
}

[data-testid="stFileUploader"] section,
[data-testid="stFileUploader"] section *,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] button {
    color: #34483D !important;
}

[data-testid="stFileUploader"] button {
    background-color: #E6EEE8 !important;
    border: 1px solid #A9B7AA !important;
}

/* Use the same forest green for interactive controls */
.stButton > button[kind="primary"],
.stDownloadButton > button {
    background-color: #234638 !important;
    color: #FFFFFF !important;
    border-color: #234638 !important;
}

.stButton > button[kind="primary"]:hover,
.stDownloadButton > button:hover {
    background-color: #315C49 !important;
    color: #FFFFFF !important;
}

/* Replace Streamlit's default red slider accent */
.stSlider [data-testid="stSliderTrackFill"] {
    background-color: #234638 !important;
}

.stSlider [role="slider"] {
    background-color: #234638 !important;
    border-color: #234638 !important;
}

/* Make radio controls consistent with the theme */
.stRadio [data-testid="stMarkdownContainer"] p {
    color: #34483D !important;
}

/* Ensure muted text remains readable */
.stCaption,
[data-testid="stCaptionContainer"] p {
    color: #68685E !important;
}

/* Keyboard accessibility */
.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible,
.stTextArea textarea:focus-visible {
    outline: 2px solid #B77852 !important;
    outline-offset: 2px !important;
}

/* ---------- Readable validation and notification messages ---------- */

/* Warning: missing resume or job description */
[data-testid="stAlert"][kind="warning"],
div[data-baseweb="notification"][kind="warning"] {
    background-color: #FFF2D9 !important;
    border: 1px solid #D8A64D !important;
    border-radius: 10px !important;
    color: #513A16 !important;
}

[data-testid="stAlert"][kind="warning"] *,
div[data-baseweb="notification"][kind="warning"] * {
    color: #513A16 !important;
}

/* Errors */
[data-testid="stAlert"][kind="error"],
div[data-baseweb="notification"][kind="error"] {
    background-color: #F8E7E3 !important;
    border: 1px solid #C66A58 !important;
    border-radius: 10px !important;
    color: #702D25 !important;
}

[data-testid="stAlert"][kind="error"] *,
div[data-baseweb="notification"][kind="error"] * {
    color: #702D25 !important;
}

/* Informational messages */
[data-testid="stAlert"][kind="info"],
div[data-baseweb="notification"][kind="info"] {
    background-color: #E6EEE8 !important;
    border: 1px solid #A9B7AA !important;
    border-radius: 10px !important;
    color: #234638 !important;
}

[data-testid="stAlert"][kind="info"] *,
div[data-baseweb="notification"][kind="info"] * {
    color: #234638 !important;
}

/* Success messages */
[data-testid="stAlert"][kind="success"],
div[data-baseweb="notification"][kind="success"] {
    background-color: #E6EEE8 !important;
    border: 1px solid #8EAD98 !important;
    border-radius: 10px !important;
    color: #234638 !important;
}

[data-testid="stAlert"][kind="success"] * ,
div[data-baseweb="notification"][kind="success"] * {
    color: #234638 !important;
}

    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Reusable display helpers
# ---------------------------------------------------------

def show_section(label: str, heading: str, description: str = "") -> None:
    """Display a consistent section heading."""
    st.markdown(
        f'<div class="section-label">{label}</div>'
        f'<div class="section-heading">{heading}</div>'
        f'<div class="section-description">{description}</div>',
        unsafe_allow_html=True,
    )


def show_skill_panel(title: str, skills: list[str], matched: bool) -> None:
    """Display a matched-skill or missing-skill panel."""
    if skills:
        skill_text = ", ".join(str(skill) for skill in skills)
    else:
        skill_text = "None identified in this category."

    st.markdown(
        f"""
        <div class="result-panel">
            <div class="panel-heading">{title}</div>
            <div class="panel-copy">{skill_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_resources(resources: list[dict]) -> None:
    """Display valid learning links without assuming every resource has a URL."""
    valid_resources = [
        resource for resource in resources
        if isinstance(resource, dict)
    ]

    if not valid_resources:
        st.caption("No learning resources listed for this skill yet.")
        return

    st.markdown("**Learning resources**")

    for resource in valid_resources:
        title = str(resource.get("title") or "Learning resource")
        url = str(resource.get("url") or "").strip()
        provider = str(resource.get("provider") or "").strip()

        label = f"{title} — {provider}" if provider else title

        if url.startswith(("https://", "http://")):
            st.markdown(f"- [{label}]({url})")
        else:
            st.markdown(f"- {label}")


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    """
    <div class="brand-label">Career development · Data-driven insights</div>
    <div class="hero-title">Career Compass</div>
    <div class="hero-description">
        Understand how your resume aligns with a target role.
        Identify missing skills and turn the gaps into a structured,
        prerequisite-aware learning plan.
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()


# ---------------------------------------------------------
# Analysis inputs and settings
# ---------------------------------------------------------

with st.sidebar:
    st.markdown("## Analysis settings")
    st.caption("Configure your analysis before getting started.")

    hours = st.slider(
        "Study hours per week",
        min_value=2,
        max_value=40,
        value=10,
        help="Used to estimate how many weeks the learning plan may take.",
    )

    method = st.radio(
        "Similarity method",
        ["tfidf", "embedding"],
        format_func=lambda value: (
            "TF-IDF" if value == "tfidf" else "Sentence embeddings"
        ),
        help=(
            "Sentence embeddings require sentence-transformers and may "
            "download a model the first time they are used."
        ),
    )

    st.divider()
    st.caption(
        "Your results depend on the resume, job description, "
        "recognized skills and selected analysis method."
    )


show_section(
    "01 · Provide your information",
    "Start with your resume and target role",
    "Upload your resume or paste its text, then add the job description.",
)

left, right = st.columns(2, gap="large")

with left:
    st.markdown("#### Your resume")

    st.info(
        "Privacy notice: Your resume is processed to generate your analysis. "
        "Please avoid uploading confidential or highly sensitive personal "
        "information. Data handling may also depend on the hosting platform."
    )

    upload = st.file_uploader(
        "Upload a resume",
        type=["pdf", "docx", "txt", "md"],
        help="Supported formats: PDF, DOCX, TXT and Markdown.",
    )

    pasted = st.text_area(
        "Or paste resume text",
        height=235,
        placeholder=(
            "Paste your skills, education, projects and experience here..."
        ),
    )

with right:
    st.markdown("#### Target job description")

    jd_text = st.text_area(
        "Job description",
        height=330,
        placeholder=(
            "Paste the job description here, including required and "
            "preferred skills where available..."
        ),
    )

analyze_clicked = st.button(
    "Analyze my career fit",
    type="primary",
    use_container_width=True,
)

if analyze_clicked:
    resume_text = pasted

    if upload is not None:
        try:
            resume_text = read_document(upload.getvalue(), upload.name)
        except UnsupportedFormat as exc:
            st.error(str(exc))
            st.stop()
        except Exception as exc:
            st.error(f"Could not read the uploaded file: {exc}")
            st.stop()

    if len(resume_text.strip()) < 20 or len(jd_text.strip()) < 20:
        st.markdown(
            """
            <div style="
            background-color: #FFF2D9;
            color: #513A16;
            border: 1px solid #D8A64D;
            border-left: 5px solid #B77852;
            border-radius: 10px;
            padding: 16px 18px;
            margin: 12px 0;
            font-size: 15px;
            line-height: 1.6;
            ">
            <strong style="color: #513A16;">Input required</strong><br>
            Please provide both a resume and a job description
            with at least 20 characters of text in each.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    try:
        with st.spinner("Comparing skills and building your learning plan..."):
            out = run_analysis(resume_text, jd_text, method, hours)
    except ModuleNotFoundError as exc:
        st.error(
            f"Optional dependency missing: {exc.name}. "
            "Switch to TF-IDF or install the required dependency."
        )
        st.stop()
    except Exception as exc:
        st.error(f"The analysis could not be completed: {exc}")
        st.stop()

    a = out["analysis"]
    plan = out.get("plan", {})
    score_available = a.get("score_status", "available") == "available"
    skill_score = a.get("skill_match_score", a.get("score"))

    st.session_state["career_compass_result"] = {
        "output": out,
        "hours": hours,
        "method": method,
    }


# ---------------------------------------------------------
# Results
# Store results in session state so controls elsewhere in
# the app do not immediately hide the previous analysis.
# ---------------------------------------------------------

saved_result = st.session_state.get("career_compass_result")

if saved_result:
    out = saved_result["output"]
    a = out["analysis"]
    plan = out.get("plan", {})
    report_hours = saved_result["hours"]

    st.divider()

    show_section(
        "02 · Your results",
        "Your career-fit overview",
        "Use these indicators to understand your current alignment with "
        "the target role. They are estimates, not hiring guarantees.",
    )

    for warning in a.get("warnings", []):
        st.warning(warning)

    score_available = a.get("score_status", "available") == "available"
    skill_score = a.get("skill_match_score", a.get("score"))

    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.metric(
            "Skill-match score",
            (
                f"{skill_score} / 100"
                if score_available and skill_score is not None
                else "Unavailable"
            ),
        )

    with c2:
        st.metric(
            "Required skills covered",
            (
                f"{a['required_coverage']:.0%}"
                if score_available
                else "N/A"
            ),
        )

    with c3:
        st.metric(
            "Preferred skills covered",
            (
                f"{a['preferred_coverage']:.0%}"
                if score_available
                else "N/A"
            ),
        )

    if score_available and skill_score is not None:
        st.markdown("**Overall skill alignment**")
        st.progress(
            min(1.0, max(0.0, float(skill_score) / 100))
        )
        st.caption(
            "This score reflects the analyzer's scoring method; "
            "it is not a probability of getting hired."
        )
    else:
        st.info(
            "A skill-match score is unavailable because the job "
            "description did not contain recognized skills. Text "
            "similarity is shown separately and should not be treated "
            "as a qualification score."
        )

        similarity = a.get(
            "text_similarity_score",
            a.get("semantic_similarity", 0.0),
        )

        st.metric(
            "Text similarity (raw cosine, not a percentage)",
            f"{similarity:.3f}",
        )

    st.divider()

    show_section(
        "03 · Skill breakdown",
        "What matches — and what needs attention",
        "Review the detected matches and gaps before deciding what to learn.",
    )

    m, x = st.columns(2, gap="large")

    with m:
        show_skill_panel(
            "Matched skills",
            (
                list(a.get("matched_required", []))
                + list(a.get("matched_preferred", []))
            ),
            matched=True,
        )

        if a.get("matched_by_implication"):
            st.caption(
                "Also counted through implied skills: "
                + ", ".join(a["matched_by_implication"])
            )

    with x:
        show_skill_panel(
            "Skills to develop",
            (
                list(a.get("missing_required", []))
                + list(a.get("missing_preferred", []))
            ),
            matched=False,
        )

    st.markdown("#### Detailed breakdown")

    with st.expander("View required and preferred skills separately"):
        detail_left, detail_right = st.columns(2)

        with detail_left:
            st.markdown("**Required skills**")
            st.markdown(
                "**Matched:** "
                + (", ".join(a.get("matched_required", [])) or "None")
            )
            st.markdown(
                "**Missing:** "
                + (", ".join(a.get("missing_required", [])) or "None")
            )

        with detail_right:
            st.markdown("**Preferred skills**")
            st.markdown(
                "**Matched:** "
                + (", ".join(a.get("matched_preferred", [])) or "None")
            )
            st.markdown(
                "**Missing:** "
                + (", ".join(a.get("missing_preferred", [])) or "None")
            )

    st.divider()

    # -----------------------------------------------------
    # Learning roadmap
    # -----------------------------------------------------

    show_section(
        "04 · Your next steps",
        "Personalized learning roadmap",
        "Work through prerequisites before dependent skills. Estimated "
        "hours are planning estimates, not guaranteed completion times.",
    )

    steps = plan.get("steps", [])

    if not score_available:
        st.info(
            "The learning plan may be unreliable until the job description "
            "contains recognized skills. Review the detected skill gaps "
            "before following the roadmap."
        )

    if steps:
        total_hours = plan.get("total_hours", 0)
        estimated_weeks = plan.get("estimated_weeks", 0)

        p1, p2, p3 = st.columns(3)

        p1.metric("Estimated learning effort", f"{total_hours} hours")
        p2.metric("Estimated duration", f"{estimated_weeks} weeks")
        p3.metric("Weekly commitment", f"{report_hours} hours")

        st.progress(0.0)
        st.caption(
            "Roadmap overview: these steps are recommended learning tasks, "
            "not completed tasks. Progress tracking is not enabled."
        )

        for step in steps:
            title = (
                f"{step.get('order', '')}. {step.get('skill', 'Skill')}"
                f" · {step.get('importance', 'required').capitalize()}"
                f" · ~{step.get('hours', 0)} h"
            )

            with st.expander(title):
                st.markdown("**Why this skill matters**")
                st.write(step.get("why", "No explanation available."))

                prerequisites_list = step.get("prerequisites", [])
                if prerequisites_list:
                    st.markdown(
                        "**Prerequisites:** "
                        + ", ".join(prerequisites_list)
                    )

                st.markdown("**Suggested practice**")
                st.write(
                    step.get(
                        "practice",
                        "Build a small project using this skill.",
                    )
                )

                show_resources(step.get("resources", []))
    else:
        st.success("No skill gaps were identified for this job description.")

    st.divider()

    # -----------------------------------------------------
    # Downloads
    # -----------------------------------------------------

    show_section(
        "05 · Take your results with you",
        "Download your report",
        "Save the human-readable summary or the structured analysis data.",
    )

    download_left, download_right = st.columns(2, gap="medium")

    with download_left:
        st.markdown("**Readable report**")
        st.caption("Markdown format — useful for reviewing and sharing.")

        st.download_button(
            "Download Markdown report",
            data=to_markdown(a, plan),
            file_name="skill_gap_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with download_right:
        st.markdown("**Structured analysis data**")
        st.caption("JSON format — useful for inspection and further processing.")

        st.download_button(
            "Download JSON data",
            data=json.dumps(out, indent=2, ensure_ascii=False),
            file_name="skill_gap_report.json",
            mime="application/json",
            use_container_width=True,
        )

    st.caption(
        "Career Compass · An analytical aid for career planning, "
        "not a guarantee of recruitment outcomes."
    )

else:
    st.markdown(
        """
        <div class="result-panel">
            <div class="section-label">Your analysis workspace</div>
            <div class="panel-heading">Your results will appear here</div>
            <div class="panel-copy">
                Add your resume and a target job description, then select
                <strong>Analyze my career fit</strong> to view skill coverage,
                missing skills, a learning roadmap and downloadable reports.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
