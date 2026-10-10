"""Stage 2 Standalone Verification Script.

Audits Day 2-3 Definition of Done from PDF 03 Page 4:
1. Two sample documents produce structured claims.
2. Related claims are correctly paired in controlled examples.
3. At least one known contradiction is detected.
4. At least one compatible pair is correctly accepted.
5. Invalid model output is caught rather than silently displayed.
"""

import os
import sys

def run_verification():
    print("=" * 60)
    print("STAGE 02 — DEFINITION OF DONE VERIFICATION")
    print("=" * 60)

    from src.claims import Claim, parse_and_validate_claims, extract_claims_rule_based
    from src.matcher import find_candidate_pairs
    from src.comparator import compare_claims_rule_based, ComparisonResult
    from src.cleaner import clean_text
    from src.pdf_reader import extract_text

    # 1. Structured claims from sample documents
    print("[1/5] Extracting structured claims from sample documents...")
    sample_a_path = os.path.join(os.path.dirname(__file__), "data", "samples", "sample_doc_a.pdf")
    sample_b_path = os.path.join(os.path.dirname(__file__), "data", "samples", "sample_doc_b.pdf")

    with open(sample_a_path, "rb") as f:
        bytes_a = f.read()
    with open(sample_b_path, "rb") as f:
        bytes_b = f.read()

    txt_a = clean_text(extract_text(bytes_a))
    txt_b = clean_text(extract_text(bytes_b))

    claims_a = extract_claims_rule_based(txt_a, "Document A")
    claims_b = extract_claims_rule_based(txt_b, "Document B")
    assert len(claims_a) >= 4, "Must extract at least 4 claims from Document A"
    assert len(claims_b) >= 4, "Must extract at least 4 claims from Document B"
    print(f"  - Extracted {len(claims_a)} claims from Doc A, {len(claims_b)} claims from Doc B (OK)")

    # 2. Related claims correctly paired
    print("\n[2/5] Pairing candidate claims by topic...")
    pairs = find_candidate_pairs(claims_a, claims_b)
    assert len(pairs) >= 3, "Must find at least 3 aligned candidate pairs"
    topics = [p["topic"] for p in pairs]
    print(f"  - Aligned topics: {topics} (OK)")

    # 3. Known contradiction detected
    print("\n[3/5] Testing known contradiction detection...")
    contradictions = []
    compatibles = []
    for p in pairs:
        res = compare_claims_rule_based(p["a"], p["b"], p["topic"])
        if res.classification == "contradiction":
            contradictions.append(res)
        elif res.classification == "compatible":
            compatibles.append(res)

    assert len(contradictions) >= 1, "Must detect at least 1 contradiction"
    c0 = contradictions[0]
    print(f"  - Contradiction detected on topic '{c0.topic}':")
    print(f"    Reason: {c0.reason}")
    print(f"    Confidence: {c0.confidence * 100:.1f}%")
    print(f"    Status: {c0.status} (OK)")

    # 4. Known compatible pair accepted
    print("\n[4/5] Testing compatible pair acceptance...")
    assert len(compatibles) >= 1, "Must accept at least 1 compatible pair"
    comp0 = compatibles[0]
    print(f"  - Compatible pair accepted on topic '{comp0.topic}':")
    print(f"    Reason: {comp0.reason}")
    print(f"    Confidence: {comp0.confidence * 100:.1f}% (OK)")

    # 5. Invalid model output caught
    print("\n[5/5] Testing invalid output trapping...")
    invalid_json = '{"invalid": "schema", "missing": "fields"}'
    try:
        parse_and_validate_claims(invalid_json, "Doc")
        print("  - ERROR: Failed to catch invalid output!")
        sys.exit(1)
    except Exception as exc:
        print(f"  - Correctly caught invalid model output: {type(exc).__name__} (OK)")

    print("\n" + "=" * 60)
    print("ALL 5 DAY 2-3 DEFINITION OF DONE CHECKPOINTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_verification()
