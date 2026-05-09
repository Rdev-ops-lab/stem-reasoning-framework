"""
LLM interface — sends STEM problems to a model and extracts chain-of-thought steps.
Mock mode returns deterministic steps for testing.
"""
import os
import re

MODEL = os.getenv("MODEL", "gpt-4o")
USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"

SYSTEM_PROMPT = """You are an expert physicist and chemist. Solve the given problem step by step.
For each step:
1. State clearly what you are doing (e.g. "Step 1: Define variables")
2. Write the equation or expression
3. Show the substitution and simplification

Format each step as: STEP N: <description> | EXPR: <equation_or_expression>
End with: FINAL ANSWER: <value with units>"""

MOCK_STEPS = [
    "STEP 1: Define coordinate system and free body diagram | EXPR: sum_F = ma",
    "STEP 2: Apply Newton's second law | EXPR: F_net = m * a",
    "STEP 3: Substitute known values | EXPR: a = F/m = 50/4 = 12.5 m/s²",
    "STEP 4: Calculate displacement using kinematics | EXPR: s = ut + 0.5*a*t**2",
    "FINAL ANSWER: s = 25 m",
]


class LLMSolver:
    def __init__(self, mock: bool = False):
        self.mock = mock or USE_MOCK

    def solve(self, problem_text: str) -> dict:
        if self.mock:
            return self._mock_solve()
        return self._api_solve(problem_text)

    def _mock_solve(self) -> dict:
        steps = []
        final_answer = ""
        for line in MOCK_STEPS:
            if line.startswith("FINAL ANSWER:"):
                final_answer = line.replace("FINAL ANSWER:", "").strip()
            elif line.startswith("STEP"):
                parts = line.split("|")
                description = re.sub(r"^STEP \d+:\s*", "", parts[0]).strip()
                expr = parts[1].replace("EXPR:", "").strip() if len(parts) > 1 else ""
                steps.append({"description": description, "expression": expr})
        return {"steps": steps, "final_answer": final_answer, "raw": "\n".join(MOCK_STEPS)}

    def _api_solve(self, problem_text: str) -> dict:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": problem_text},
                ],
                temperature=0,
            )
            raw = response.choices[0].message.content
            return self._parse(raw)
        except Exception as e:
            return {"steps": [], "final_answer": "", "raw": "", "error": str(e)}

    def _parse(self, raw: str) -> dict:
        steps = []
        final_answer = ""
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.upper().startswith("FINAL ANSWER:"):
                final_answer = line.split(":", 1)[1].strip()
            elif re.match(r"^STEP \d+:", line, re.IGNORECASE):
                parts = line.split("|")
                description = re.sub(r"^STEP \d+:\s*", "", parts[0], flags=re.IGNORECASE).strip()
                expr = parts[1].replace("EXPR:", "").strip() if len(parts) > 1 else ""
                steps.append({"description": description, "expression": expr})
        return {"steps": steps, "final_answer": final_answer, "raw": raw}
