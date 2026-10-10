"""Stage 02 Architecture & Decision Flow Explorer.

Interactive Streamlit interface for Stage 02:
- Explains the multi-stage decoupled pipeline architecture.
- Demonstrates Pydantic Claim Object structure.
- Shows candidate topic alignment in action (filtering out non-matching topics).
- Visualizes the pairwise fact comparison decision flowchart.
"""

import sys
import os
import streamlit as st
import json

STAGE_DIR = os.path.dirname(os.path.abspath(__file__))
if STAGE_DIR not in sys.path:
    sys.path.insert(0, STAGE_DIR)

from src.claims import Claim, extract_claims_rule_based
from src.matcher import find_candidate_pairs, is_compatible_topic
from src.comparator import compare_claims_rule_based
from src.cleaner import clean_text

st.set_page_config(
    page_title="AI Contradiction Detector | Stage 2 Architecture",
    page_icon="📐",
    layout="wide"
)

st.title("📐 Stage 02: Architecture & Decision Flow Explorer")
st.caption("Reference: PDF 03 — Architecture, Claim Model, Decision Flowcharts & Prompt Design")

st.markdown("""
<style>
    .flow-box {
        background-color: #f1f5f9;
        border-radius: 8px;
        padding: 16px;
        border-left: 4px solid #0284c7;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Architecture Overview Tab
tab_arch, tab_claims, tab_align, tab_flow = st.tabs([
    "🏗️ Pipeline Architecture",
    "📄 Pydantic Claim Schema",
    "🔗 Topic Alignment Engine",
    "⚖️ Comparison Decision Flow"
])

with tab_arch:
    st.subheader("Why Separate Extraction & Comparison?")
    st.info(
        "A single monolithic prompt asking 'Do these two documents contradict?' causes hallucinations and cannot pinpoint exact lines. "
        "Our modular pipeline separates text ingestion, structured claim parsing, topic clustering, and pairwise comparison."
    )
    st.code("""
[SOURCE A] & [SOURCE B]
       │
       ▼
[PyMuPDF Extraction]
       │
       ▼
[Text Cleaning & Normalization]
       │
       ▼
[Claim Extraction (JSON Array via Pydantic)]
       │
       ▼
[Candidate Alignment (Subject/Attribute Clustering)]
       │
       ▼
[Pairwise Fact Comparison (Decision Flowchart)]
       │
       ▼
[Evidence Report & Confidence Heuristic]
    """, language="text")

with tab_claims:
    st.subheader("Structured Claim Object (Pydantic BaseModel)")
    st.markdown("Every claim strictly captures 6 core dimensions:")
    sample_claim = {
        "claim_id": "A-01",
        "subject": "ABC Technologies",
        "attribute": "employment_period",
        "value": {"start": "2024-01", "end": "2024-12"},
        "source_text": "I worked at ABC Technologies from January 2024 to December 2024.",
        "source": "Document A"
    }
    st.json(sample_claim)
    st.caption("Pydantic validation guarantees that missing fields or ungrounded claims are trapped before comparison.")

with tab_align:
    st.subheader("Claim Alignment vs Quadratic Matching")
    st.markdown("Alignment prevents blind all-to-all comparisons. Observe the PDF 03 alignment rules below:")

    align_data = [
        {"Claim A": "ABC Technologies (employment_period)", "Claim B": "ABC Technologies (employment_period)", "Aligned?": "✅ YES (Same topic)"},
        {"Claim A": "ABC Technologies (employment_period)", "Claim B": "Education (cgpa)", "Aligned?": "❌ NO (Filtered out)"},
        {"Claim A": "Project Allocation (project_budget)", "Claim B": "Project Allocation (project_budget)", "Aligned?": "✅ YES (Same topic)"},
        {"Claim A": "Project Allocation (project_budget)", "Claim B": "Candidate (current_location)", "Aligned?": "❌ NO (Filtered out)"}
    ]
    st.table(align_data)

with tab_flow:
    st.subheader("Comparison Decision Flowchart")
    st.markdown("""
    ```text
    Are the claims about the same topic?
      ├─ NO  ──► Do not compare
      └─ YES ──► Are both claims factual enough to compare?
                   ├─ NO  ──► Insufficient information
                   └─ YES ──► Do values conflict?
                                ├─ YES ──► Potential contradiction (Requires human verification)
                                └─ NO  ──► Compatible
    ```
    """)
    st.markdown("#### Live Pairwise Comparison Tester")
    val_a = st.text_input("Claim A Value:", value="January 2024 to December 2024")
    val_b = st.text_input("Claim B Value:", value="June 2023 to March 2025")
    
    if st.button("Evaluate Decision Flow"):
        c_a = Claim(claim_id="A-01", subject="ABC", attribute="tenure", value=val_a, source_text=val_a, source="Doc A")
        c_b = Claim(claim_id="B-01", subject="ABC", attribute="tenure", value=val_b, source_text=val_b, source="Doc B")
        res = compare_claims_rule_based(c_a, c_b, topic="tenure")
        st.write(f"**Classification:** `{res.classification.upper()}`")
        st.write(f"**Reason:** {res.reason}")
        st.write(f"**Confidence:** {res.confidence * 100:.1f}%")
        st.write(f"**Status:** `{res.status}`")
