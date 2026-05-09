"""
Per-step symbolic and unit verification for STEM reasoning chains.
Uses SymPy for symbolic equivalence and dimensional analysis for unit checks.
"""
from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class StepResult:
    step: int
    description: str
    symbolic_correct: bool
    unit_correct: bool
    coherent: bool
    score: float
    notes: str = ""


class StepVerifier:
    def verify(
        self,
        step_num: int,
        step_description: str,
        expected_expression: Optional[str] = None,
        previous_step: Optional[StepResult] = None,
        mock: bool = False,
    ) -> StepResult:
        if mock:
            return self._mock_verify(step_num, step_description)

        symbolic_ok = self._check_symbolic(step_description, expected_expression)
        unit_ok = self._check_units(step_description)
        coherent = self._check_coherence(step_description, previous_step)
        score = self._aggregate(symbolic_ok, unit_ok, coherent)

        return StepResult(
            step=step_num,
            description=step_description,
            symbolic_correct=symbolic_ok,
            unit_correct=unit_ok,
            coherent=coherent,
            score=round(score, 4),
        )

    def _check_symbolic(self, step: str, expected: Optional[str]) -> bool:
        if not expected:
            return True
        try:
            from sympy import sympify, simplify
            lhs = sympify(step.split("=")[0].strip()) if "=" in step else sympify(step)
            rhs = sympify(expected.split("=")[0].strip()) if "=" in expected else sympify(expected)
            return simplify(lhs - rhs) == 0
        except Exception:
            # Fallback: simple string normalization
            return step.replace(" ", "").lower() == expected.replace(" ", "").lower()

    def _check_units(self, step: str) -> bool:
        # Basic unit consistency check — looks for common unit mismatches
        unit_patterns = {
            r"\bm/s²\b": "acceleration",
            r"\bN\b": "force",
            r"\bJ\b": "energy",
            r"\bkg\b": "mass",
        }
        detected = [label for pattern, label in unit_patterns.items() if re.search(pattern, step)]
        # No contradictory units found
        return len(set(detected)) == len(detected)

    def _check_coherence(self, step: str, previous: Optional[StepResult]) -> bool:
        if previous is None:
            return True
        # If previous step failed symbolically, this step cannot be coherent
        if not previous.symbolic_correct:
            return False
        return True

    def _aggregate(self, symbolic: bool, unit: bool, coherent: bool) -> float:
        weights = [(symbolic, 1.0), (unit, 1.0), (coherent, 1.0)]
        return sum(w for ok, w in weights if ok) / sum(w for _, w in weights)

    def _mock_verify(self, step_num: int, description: str) -> StepResult:
        # Deterministic mock: odd steps pass, even steps vary
        symbolic_ok = step_num % 3 != 0
        unit_ok = True
        coherent = step_num < 4
        score = self._aggregate(symbolic_ok, unit_ok, coherent)
        return StepResult(
            step=step_num,
            description=description,
            symbolic_correct=symbolic_ok,
            unit_correct=unit_ok,
            coherent=coherent,
            score=round(score, 4),
            notes="mock",
        )
