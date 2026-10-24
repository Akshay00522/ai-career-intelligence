# Evaluation report

Dataset: 56 labelled pairs (8 resumes x 7 job descriptions), labels 0-3 (poor / weak / good / strong fit). Regenerate with `python cli.py evaluate --write-report docs/EVALUATION.md`.

## Ablation: baselines vs. each added feature

| System | Spearman | AUC (good fit) | Top-1 role | Pearson |
|---|---|---|---|---|
| Baseline A: skill overlap (Jaccard) | 0.640 | 0.871 | 1.00 | 0.786 |
| Baseline B: TF-IDF cosine only | 0.709 | 0.906 | 1.00 | 0.821 |
| Hybrid v0.1 (no implications, no OR groups) | 0.645 | 0.866 | 1.00 | 0.788 |
| Hybrid + skill implications | 0.672 | 0.902 | 1.00 | 0.800 |
| Hybrid v1.0 (+ implications + OR groups) | 0.693 | 0.914 | 1.00 | 0.808 |
| Hybrid v1.0 with weights tuned by leave-one-resume-out CV | 0.729 | 0.896 | 1.00 | 0.831 |

Default weights: required=0.60, preferred=0.15, semantic=0.25.
Weights tuned on all data (for reference only, optimistic): required=0.50, preferred=0.00, semantic=0.50.

## Does the top-ranked role match the best-labelled role?

| Resume | Top predicted JD (score) | Best-labelled JD(s) | Correct |
|---|---|---|---|
| r1_data_analyst | j1_data_analyst (75.8) | j1_data_analyst | yes |
| r2_ml_graduate | j2_ml_engineer (44.7) | j1_data_analyst, j2_ml_engineer | yes |
| r3_fullstack_web | j3_fullstack (77.6) | j3_fullstack | yes |
| r4_backend_python | j4_backend_python (81.1) | j4_backend_python | yes |
| r5_devops | j5_devops (89.6) | j5_devops | yes |
| r6_deep_learning_cv | j2_ml_engineer (51.2) | j2_ml_engineer | yes |
| r7_llm_genai | j6_genai_engineer (77.4) | j6_genai_engineer | yes |
| r8_data_engineer | j7_data_engineer (88.2) | j7_data_engineer | yes |

## Limitations (read before quoting these numbers)

- The resumes and JDs are hand-written personas, not real documents, and the labels come from a single annotator. Treat this as a regression benchmark and smoke test, not as evidence of real-world accuracy.
- The taxonomy and the test documents were written by the same person, so skill-extraction recall is optimistic.
- 56 pairs from 8 resumes is small; differences of a few hundredths between systems are noise.
- Embedding similarity (`--embedding`) is not part of this table; add it on a machine with `sentence-transformers` installed.
- To strengthen the study: add real anonymised resumes and JDs with several annotators and report inter-annotator agreement.
