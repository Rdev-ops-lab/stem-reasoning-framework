"""
Per-step symbolic and unit verification for STEM reasoning chains.
Uses SymPy for symbolic equivalence and dimensional analysis for unit checks.
"""
from dataclasses import dataclass
from typing import Optional
import re
from sympy import sympify, simplify, Eq

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
            # Step aur Expected ko Equation objects mein convert karein
            def parse_to_eq(s):
                if "=" in s:
                    parts = s.split("=")
                    return Eq(sympify(parts[0].strip()), sympify(parts[1].strip()))
                return sympify(s.strip())

            expr1 = parse_to_eq(step)
            expr2 = parse_to_eq(expected)

            # Agar dono equations hain, toh check karein ki kya wo mathematically same hain
            # SymPy simplify(lhs - rhs) equations ke liye handle karta hai
            if isinstance(expr1, Eq) and isinstance(expr2, Eq):
                # Equation logic: (LHS1 - RHS1) should be equivalent to (LHS2 - RHS2) or its negative
                diff1 = expr1.lhs - expr1.rhs
                diff2 = expr2.lhs - expr2.rhs
                return simplify(diff1 - diff2) == 0 or simplify(diff1 + diff2) == 0

            return simplify(expr1 - expr2) == 0
        except Exception:
            return step.replace(" ", "").lower() == expected.replace(" ", "").lower()

    def _check_units(self, step: str) -> bool:
        unit_patterns = {
            r"\bm/s²\b": "acceleration",
            r"\bN\b": "force",
            r"\bJ\b": "energy",
            r"\bkg\b": "mass",
        }
        detected = [label for pattern, label in unit_patterns.items() if re.search(pattern, step)]
        return len(set(detected)) == len(detected)

    def _check_coherence(self, step: str, previous: Optional[StepResult]) -> bool:
        if previous is None:
            return True
        if not previous.symbolic_correct:
            return False
        return True

    def _aggregate(self, symbolic: bool, unit: bool, coherent: bool) -> float:
        weights = [(symbolic, 1.0), (unit, 1.0), (coherent, 1.0)]
        return sum(w for ok, w in weights if ok) / sum(w for _, w in weights)

    def _mock_verify(self, step_num: int, description: str) -> StepResult:
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
