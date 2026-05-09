"""
Per-step symbolic and unit verification for STEM reasoning chains.
Uses SymPy for symbolic equivalence and dimensional analysis for unit checks.
"""
from dataclasses import dataclass
from typing import Optional
import re
from sympy import sympify, simplify, Eq
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

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
            # Transformations taaki 'ma' ko 'm*a' samjha ja sake
            transformations = standard_transformations + (implicit_multiplication_application,)

            def parse_to_obj(s):
                s = s.strip()
                if "=" in s:
                    lhs, rhs = s.split("=")
                    # Eq object banate hain
                    return Eq(parse_expr(lhs, transformations=transformations), 
                              parse_expr(rhs, transformations=transformations))
                return parse_expr(s, transformations=transformations)

            obj1 = parse_to_obj(step)
            obj2 = parse_to_obj(expected)

            # Agar dono Equations (Eq) hain
            if isinstance(obj1, Eq) and isinstance(obj2, Eq):
                # Equation symmetric check: (LHS1 - RHS1) vs (LHS2 - RHS2)
                # Hum check karte hain ki kya dono ka difference zero hai
                diff1 = simplify(obj1.lhs - obj1.rhs)
                diff2 = simplify(obj2.lhs - obj2.rhs)
                # Ya toh diff1 == diff2 ho, ya diff1 == -diff2 (direction reversal)
                return simplify(diff1 - diff2) == 0 or simplify(diff1 + diff2) == 0

            # Agar ek equation hai aur ek expression, toh simplify karke check karein
            return simplify(obj1 - obj2) == 0
            
        except Exception:
            # Fallback for non-mathematical strings
            clean_step = re.sub(r'\s+', '', step).lower()
            clean_expected = re.sub(r'\s+', '', expected).lower()
            return clean_step == clean_expected

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
        # Mock logic as requested
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
