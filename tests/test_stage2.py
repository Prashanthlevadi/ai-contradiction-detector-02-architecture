"""Automated Test Suite for Stage 02 Architecture & AI Reasoning.

Verifies:
- Pydantic Claim schema and validation.
- Topic-based candidate claim alignment (positive and negative pairs).
- Detection of known contradictions and compatible pairs.
- Error handling for invalid model outputs.
- Responsible AI language safeguards (no defamatory terms, 'potential contradiction' phrasing).
"""

import os
import sys
import pytest
from pydantic import ValidationError

# Ensure Stage 2 is on sys.path
STAGE2_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if STAGE2_DIR not in sys.path:
    sys.path.insert(0, STAGE2_DIR)

from src.claims import Claim, parse_and_validate_claims, extract_claims_rule_based
from src.matcher import find_candidate_pairs, is_compatible_topic
from src.comparator import (
    ComparisonResult,
    compare_claims_rule_based,
    parse_and_validate_comparison,
    ClassificationType
)
from src.pipeline import ContradictionPipeline


def test_claim_model_valid():
    claim = Claim(
        claim_id="A-01",
        subject="ABC Technologies",
        attribute="employment_period",
        value={"start": "2024-01", "end": "2024-12"},
        source_text="I worked at ABC Technologies from January 2024 to December 2024.",
        source="Document A"
    )
    assert claim.claim_id == "A-01"
    assert claim.subject == "ABC Technologies"
    assert claim.attribute == "employment_period"
    assert claim.value["start"] == "2024-01"


def test_claim_model_missing_field():
    with pytest.raises(ValidationError):
        # Missing required source_text
        Claim(
            claim_id="A-02",
            subject="ABC Technologies",
            attribute="employment_period",
            value="2024",
            source="Document A"  # type: ignore
        )


def test_parse_and_validate_claims_json():
    raw_json = """[
        {
            "claim_id": "A-01",
            "subject": "ABC Technologies",
            "attribute": "employment_period",
            "value": {"start": "2024-01", "end": "2024-12"},
            "source_text": "I worked at ABC Technologies from January 2024 to December 2024.",
            "source": "Document A"
        }
    ]"""
    claims = parse_and_validate_claims(raw_json, "Document A")
    assert len(claims) == 1
    assert claims[0].claim_id == "A-01"


def test_parse_invalid_json_caught():
    with pytest.raises(ValueError, match="Model generated invalid JSON"):
        parse_and_validate_claims("Not valid JSON content", "Document A")


def test_alignment_logic_rules():
    """Verifies alignment table from PDF 03 Page 3:
    - ABC employment dates + ABC employment dates -> YES
    - ABC employment dates + College CGPA -> NO
    - Project budget + Project budget -> YES
    - Project budget + Project location -> NO
    """
    claim_emp_a = Claim(
        claim_id="A-01", subject="ABC Technologies", attribute="employment_period",
        value={"start": "2024-01", "end": "2024-12"}, source_text="Worked 2024", source="Doc A"
    )
    claim_emp_b = Claim(
        claim_id="B-01", subject="ABC Technologies", attribute="employment_period",
        value={"start": "2023-06", "end": "2025-03"}, source_text="Worked 2023-2025", source="Doc B"
    )
    claim_cgpa = Claim(
        claim_id="B-02", subject="College", attribute="cgpa",
        value="8.9", source_text="CGPA is 8.9", source="Doc B"
    )
    claim_budget_a = Claim(
        claim_id="A-03", subject="Project Allocation", attribute="project_budget",
        value=50000, source_text="Budget $50,000", source="Doc A"
    )
    claim_budget_b = Claim(
        claim_id="B-03", subject="Project Allocation", attribute="project_budget",
        value=75000, source_text="Budget $75,000", source="Doc B"
    )
    claim_loc = Claim(
        claim_id="B-04", subject="Project", attribute="project_location",
        value="Bengaluru", source_text="Located in Bengaluru", source="Doc B"
    )

    # 1. Emp dates vs Emp dates -> YES
    align1, _, _ = is_compatible_topic(claim_emp_a, claim_emp_b)
    assert align1 is True

    # 2. Emp dates vs CGPA -> NO
    align2, _, _ = is_compatible_topic(claim_emp_a, claim_cgpa)
    assert align2 is False

    # 3. Budget vs Budget -> YES
    align3, _, _ = is_compatible_topic(claim_budget_a, claim_budget_b)
    assert align3 is True

    # 4. Budget vs Location -> NO
    align4, _, _ = is_compatible_topic(claim_budget_a, claim_loc)
    assert align4 is False


def test_contradiction_detection():
    claim_emp_a = Claim(
        claim_id="A-01", subject="ABC Technologies", attribute="employment_period",
        value={"start": "2024-01", "end": "2024-12"},
        source_text="I worked at ABC Technologies from January 2024 to December 2024.",
        source="Document A"
    )
    claim_emp_b = Claim(
        claim_id="B-01", subject="ABC Technologies", attribute="employment_period",
        value={"start": "2023-06", "end": "2025-03"},
        source_text="Employment Dates: June 2023 to March 2025",
        source="Document B"
    )

    result = compare_claims_rule_based(claim_emp_a, claim_emp_b, topic="employment_period")
    assert result.classification == "contradiction"
    assert "potential contradiction" in result.reason.lower()
    assert result.status == "Requires human verification"


def test_compatible_pair_accepted():
    claim_deg_a = Claim(
        claim_id="A-04", subject="Education", attribute="degree",
        value="B.Tech in Computer Science",
        source_text="Degree: B.Tech in Computer Science",
        source="Document A"
    )
    claim_deg_b = Claim(
        claim_id="B-04", subject="Education", attribute="degree",
        value="B.Tech in Computer Science",
        source_text="Degree: B.Tech in Computer Science",
        source="Document B"
    )

    result = compare_claims_rule_based(claim_deg_a, claim_deg_b, topic="degree")
    assert result.classification == "compatible"
    assert result.confidence >= 0.90


def test_responsible_ai_defamation_filter():
    """Ensures defamatory labels like 'liar' are sanitized."""
    claim_a = Claim(claim_id="A-01", subject="S", attribute="A", value="1", source_text="T1", source="Doc A")
    claim_b = Claim(claim_id="B-01", subject="S", attribute="A", value="2", source_text="T2", source="Doc B")

    res = ComparisonResult(
        topic="test",
        classification="contradiction",
        confidence=0.9,
        reason="The author is a liar and committed fraud.",
        claim_a="A-01",
        claim_b="B-01",
        source_a="T1",
        source_b="T2"
    )
    assert "liar" not in res.reason.lower()
    assert "fraud" not in res.reason.lower()
    assert "conflicting data point" in res.reason


def test_pipeline_end_to_end_synthetic_docs():
    doc_a = (
        "Candidate Name: Prashanth Levadi\n"
        "Company: ABC Technologies\n"
        "Employment Period: January 2024 to December 2024\n"
        "Project Budget: $50,000\n"
        "City: Bengaluru, India\n"
        "Degree: B.Tech in Computer Science\n"
        "Status: Completed in June 2024\n"
    )
    doc_b = (
        "Candidate Name: Prashanth Levadi\n"
        "Company: ABC Technologies\n"
        "Employment Dates: June 2023 to March 2025\n"
        "Project Budget: $75,000\n"
        "City: Hyderabad, India\n"
        "Degree: B.Tech in Computer Science\n"
        "Status: Completed in June 2024\n"
    )

    pipe = ContradictionPipeline()
    out = pipe.process_texts(doc_a, doc_b)

    assert len(out["claims_a"]) >= 4
    assert len(out["claims_b"]) >= 4
    assert out["metrics"]["contradictions"] >= 2  # dates, budget, location
    assert out["metrics"]["compatible"] >= 1      # degree or status
