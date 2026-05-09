"""
Sample usage — mock mode, no API key needed.
Run: USE_MOCK=true python examples/sample_usage.py
"""
import os, sys
os.environ["USE_MOCK"] = "true"
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.llm_solver import LLMSolver
from src.step_verifier import StepVerifier
from src.scoring import ReasoningScorer

solver = LLMSolver(mock=True)
verifier = StepVerifier()
scorer = ReasoningScorer()

problem = "A block of mass 4 kg is pushed by 50 N force. Find displacement after 2s."
solution = solver.solve(problem)

step_results, prev = [], None
for i, step in enumerate(solution["steps"], 1):
    r = verifier.verify(i, step["description"], mock=True, previous_step=prev)
    step_results.append(r)
    prev = r

score_data = scorer.score(step_results)
print(f"\nVerdict: {score_data['verdict']}  |  Score: {score_data['reasoning_score']}")
for s in step_results:
    tag = "PASS" if s.score == 1.0 else "PARTIAL" if s.score > 0 else "FAIL"
    print(f"  Step {s.step} [{tag}]: {s.description}")
print(f"Final answer: {solution['final_answer']}")
