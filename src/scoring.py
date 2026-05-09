"""
Reasoning score aggregation.
Weights earlier steps slightly higher — errors in step 1 propagate further.
"""
from src.step_verifier import StepResult


class ReasoningScorer:
    def __init__(self, pass_threshold: float = 0.80, partial_threshold: float = 0.50):
        self.pass_threshold = pass_threshold
        self.partial_threshold = partial_threshold

    def score(self, steps: list[StepResult]) -> dict:
        if not steps:
            return {"reasoning_score": 0.0, "verdict": "FAIL"}

        # Earlier steps get slightly higher weight
        total_weight = 0.0
        weighted_sum = 0.0
        for i, step in enumerate(steps):
            weight = 1.0 + (len(steps) - i) * 0.1
            weighted_sum += step.score * weight
            total_weight += weight

        reasoning_score = round(weighted_sum / total_weight, 4)
        verdict = self._verdict(reasoning_score)
        return {"reasoning_score": reasoning_score, "verdict": verdict}

    def _verdict(self, score: float) -> str:
        if score >= self.pass_threshold:
            return "PASS"
        elif score >= self.partial_threshold:
            return "PARTIAL"
        return "FAIL"
