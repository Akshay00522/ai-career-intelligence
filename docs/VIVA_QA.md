# Interview and viva questions

**What problem does it solve?** Candidates cannot see why their resume fits or misses a role. The tool compares a resume with a job description, scores the fit, lists missing skills and turns them into an ordered study plan.

**Why not just ask an LLM?** An LLM can do it, but the answer is not reproducible or measurable. A taxonomy-based pipeline is deterministic, free to run, explainable skill by skill, and I could evaluate it. An LLM extractor could replace the extraction step later.

**How do you extract skills?** A taxonomy of canonical skills with aliases, matched by regular expressions with lookarounds instead of `\b`, because `\b` fails on `C++` and `CI/CD` and matches `Java` inside `JavaScript`. Overlaps resolve to the longest match so `Azure ML` is not also machine learning.

**What are skill implications?** Having scikit-learn implies Python and machine learning. Without that, a resume mentioning only scikit-learn was flagged as missing machine learning. Implications are data in the taxonomy and flagged in the report so the user can see them.

**How are "FastAPI or Flask" requirements handled?** Mentions joined by "or" (or a comma list ending in "or") form one requirement satisfied by any option, provided the options share a category. Without this, a candidate with Flask was penalised for lacking FastAPI.

**How is the score computed?** 60 percent required coverage, 15 percent preferred coverage, 25 percent text similarity, renormalised when a section is absent. TF-IDF cosine is small in absolute terms, so it is scaled by 2 and capped at 1 before blending.

**How did you evaluate it?** 56 hand-labelled pairs (8 resumes x 7 roles, labels 0-3). I report Spearman correlation, AUC for "good fit", and top-1 role accuracy, and compare against two baselines (skill overlap, TF-IDF only) with an ablation that adds implications and then OR groups.

**Did the hybrid beat the baselines?** Against skill overlap, yes. Against TF-IDF alone, no on Spearman (0.693 vs 0.709), slightly yes on AUC (0.914 vs 0.906), and both differences are within noise for this dataset. The hybrid's value is that it explains the result; I say so in the report instead of hiding it.

**What are the weaknesses of your evaluation?** Hand-written personas, one annotator, the same author wrote the taxonomy and the test data, and only 56 pairs. It is a regression benchmark, not a measure of real-world accuracy. Next steps: real anonymised documents, multiple annotators, inter-annotator agreement.

**How did you avoid overfitting the weights?** I tuned them with leave-one-resume-out cross-validation and compared against the defaults. The tuned weights varied across folds and the gain was within noise, so I kept the defaults I chose before looking at results.

**How does the learning plan order skills?** Missing skills become nodes. Prerequisites (from `implies` and `prereqs`) are added unless the candidate already has them or already has the skill that depends on them. A topological sort with a priority queue then orders them by importance, market demand, and effort, always placing prerequisites first. A unit test caught a bug where it re-listed the prerequisites of skills the candidate already had.

**How would you scale it?** Move the taxonomy to ESCO or O*NET, add an NER or LLM extractor behind the same interface, cache embeddings, and store job postings in a database for demand analysis.

**What would you do differently?** Collect real labelled data first, add experience-level matching, and evaluate extraction accuracy separately from scoring.
