"""AI Contradiction Detector - Architecture & AI Reasoning Module (Stage 2)."""
from .claims import Claim, parse_and_validate_claims, extract_claims_rule_based
from .matcher import find_candidate_pairs, is_compatible_topic
from .comparator import ComparisonResult, compare_claims_rule_based, parse_and_validate_comparison
from .pipeline import ContradictionPipeline

__all__ = [
    "Claim",
    "parse_and_validate_claims",
    "extract_claims_rule_based",
    "find_candidate_pairs",
    "is_compatible_topic",
    "ComparisonResult",
    "compare_claims_rule_based",
    "parse_and_validate_comparison",
    "ContradictionPipeline",
]
