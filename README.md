# Stage 02: Architecture, Claim Model, Decision Flowcharts & Prompt Design
**AI Contradiction Detector — 1-Week Practical AI/NLP Mini-Project**  
*Reference: PDF 03 Official Student Build Guide*

---

## 1. System Architecture

Rather than passing two complete documents to an LLM in a single monolithic prompt, this system implements an explainable, multi-stage pipeline:

```
[SOURCE A] & [SOURCE B]
         │
         ▼
[PyMuPDF Extraction]
         │
         ▼
[Text Cleaning & Normalization]
         │
         ▼
[Factual Claim Extraction (JSON)]
         │
         ▼
[Candidate Claim Alignment (Topic Matching)]
         │
         ▼
[Pairwise Fact Comparison & Decision Flow]
         │
         ▼
[Evidence Report & Metrics]
```

### Why Separate Extraction and Comparison?
1. **Explainability:** Directly pinpoints the exact sentence pair causing a conflict.
2. **Auditability:** Every claim retains its original `source_text`.
3. **Efficiency:** Alignment filters out unrelated facts (e.g., employment dates vs CGPA), avoiding expensive $O(N \times M)$ all-to-all LLM calls.

---

## 2. Claim Object Specification

Claims conform strictly to the Pydantic `Claim` model:
```json
{
  "claim_id": "A-01",
  "subject": "ABC Technologies",
  "attribute": "employment_period",
  "value": {
    "start": "2024-01",
    "end": "2024-12"
  },
  "source_text": "I worked at ABC Technologies from January 2024 to December 2024.",
  "source": "Document A"
}
```

---

## 3. Comparison Decision Flow

```
Are the claims about the same topic?
  ├─ NO  ──► Do not compare
  └─ YES ──► Are both claims factual enough to compare?
               ├─ NO  ──► Insufficient information
               └─ YES ──► Do values conflict?
                            ├─ YES ──► Potential contradiction (Requires human verification)
                            └─ NO  ──► Compatible
```

---

## 4. Responsible AI Guardrails

- **Neutral Labeling:** The system never labels a person or company as a "liar", "fraudster", or "dishonest".
- **Actionable Status:** Findings are strictly designated as **"Potential Contradiction"** with status **"Requires human verification"**.
- **Confidence Heuristic:** The confidence score is a model-generated estimate for prioritizing human triage, not calibrated mathematical probability or judicial proof.

---

## 5. Automated Testing & Verification

Run the test suite:
```bash
python -m pytest tests/test_stage2.py -v
```

Run the Day 2–3 Definition of Done verification:
```bash
python verify_stage2.py
```

---

## 6. Day 2–3 Definition of Done Audit

| Checkpoint | Pass Criteria | Result | Evidence |
| :--- | :--- | :--- | :--- |
| **Structured Claims** | Two sample documents produce structured claims | ✅ PASS | Extracted 5 claims from Doc A, 5 from Doc B |
| **Claim Pairing** | Related claims correctly paired in controlled examples | ✅ PASS | Alignment confirmed for 5 matching topics |
| **Contradiction Detection** | At least one known contradiction detected | ✅ PASS | Employment period conflict detected (94% conf) |
| **Compatible Acceptance** | At least one compatible pair accepted | ✅ PASS | Job role and degree matches confirmed (95% conf) |
| **Error Trapping** | Invalid model output caught rather than displayed | ✅ PASS | Pydantic and JSON validation errors trapped |
