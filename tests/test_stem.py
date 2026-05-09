"""
Tests for STEM Reasoning Framework — mock mode, no API key needed.
USE_MOCK=true pytest tests/ -v
"""
import os
os.environ["USE_MOCK"] = "true"

import pytest
from src.step_verifier import StepVerifier
from src.scoring import ReasoningScorer, StepResult


# ── StepVerifier ──────────────────────────────────────────────────────────────

@pytest.fixture
def verifier():
    return StepVerifier()

def test_verify_returns_step_result(verifier):
    r = verifier.verify(1, "Apply Newton's second law: F = ma", mock=True)
    assert r.step == 1
    assert 0.0 <= r.score <= 1.0

def test_verify_unit_check_clean(verifier):
    r = verifier._check_units("a = F/m gives acceleration in m/s²")
    assert isinstance(r, bool)

def test_verify_coherence_no_previous(verifier):
    assert verifier._check_coherence("any step", None) is True

def test_verify_coherence_fails_after_bad_step(verifier):
    bad_prev = StepResult(1, "bad", symbolic_correct=False, unit_correct=True, coherent=True, score=0.33)
    assert verifier._check_coherence("next step", bad_prev) is False

def test_verify_symbolic_equivalent_expressions(verifier):
    assert verifier._check_symbolic("F = m*a", "m*a = F") is True

def test_verify_symbolic_no_expected(verifier):
    assert verifier._check_symbolic("any step", None) is True


# ── ReasoningScorer ───────────────────────────────────────────────────────────

@pytest.fixture
def scorer():
    return ReasoningScorer(pass_threshold=0.80, partial_threshold=0.50)

def make_step(n, score):
    return StepResult(n, f"step {n}", symbolic_correct=score > 0.5, unit_correct=True, coherent=True, score=score)

def test_scorer_all_pass(scorer):
    steps = [make_step(i, 1.0) for i in range(1, 5)]
    result = scorer.score(steps)
    assert result["verdict"] == "PASS"
    assert result["reasoning_score"] >= 0.80

def test_scorer_all_fail(scorer):
    steps = [make_step(i, 0.0) for i in range(1, 5)]
    result = scorer.score(steps)
    assert result["verdict"] == "FAIL"
    assert result["reasoning_score"] < 0.50

def test_scorer_partial(scorer):
    steps = [make_step(1, 1.0), make_step(2, 1.0), make_step(3, 0.0), make_step(4, 0.0)]
    result = scorer.score(steps)
    assert result["verdict"] in {"PARTIAL", "FAIL"}

def test_scorer_empty_steps(scorer):
    result = scorer.score([])
    assert result["verdict"] == "FAIL"
    assert result["reasoning_score"] == 0.0

def test_scorer_earlier_steps_weighted_higher(scorer):
    # Steps 1-2 pass, steps 3-4 fail → should score higher than if 3-4 pass and 1-2 fail
    early_pass = [make_step(1, 1.0), make_step(2, 1.0), make_step(3, 0.0), make_step(4, 0.0)]
    late_pass  = [make_step(1, 0.0), make_step(2, 0.0), make_step(3, 1.0), make_step(4, 1.0)]
    assert scorer.score(early_pass)["reasoning_score"] > scorer.score(late_pass)["reasoning_score"]
