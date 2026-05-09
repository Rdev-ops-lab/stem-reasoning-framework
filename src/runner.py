"""
Main benchmark runner.
Usage: python -m src.runner --benchmark benchmarks/physics_mechanics.json
"""
import json
import os
import time
import argparse
from src.llm_solver import LLMSolver
from src.step_verifier import StepVerifier
from src.scoring import ReasoningScorer

USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"


def run_benchmark(benchmark_path: str, output_path: str = "outputs/results.json"):
    with open(benchmark_path) as f:
        problems = json.load(f)

    solver = LLMSolver(mock=USE_MOCK)
    verifier = StepVerifier()
    scorer = ReasoningScorer()
    results = []

    for problem in problems:
        start = time.time()
        solution = solver.solve(problem["problem_text"])

        step_results = []
        prev = None
        for i, step in enumerate(solution["steps"], 1):
            result = verifier.verify(
                step_num=i,
                step_description=step["description"],
                expected_expression=problem.get("expected_steps", [None] * i)[i - 1],
                previous_step=prev,
                mock=USE_MOCK,
            )
            step_results.append(result)
            prev = result

        score_data = scorer.score(step_results)
        elapsed = round((time.time() - start) * 1000, 1)

        result_obj = {
            "problem_id": problem["id"],
            "domain": problem["domain"],
            "difficulty": problem.get("difficulty", "phd"),
            "final_answer_correct": solution.get("final_answer", "") == problem.get("expected_answer", ""),
            "reasoning_score": score_data["reasoning_score"],
            "verdict": score_data["verdict"],
            "step_trace": [
                {
                    "step": s.step,
                    "description": s.description,
                    "symbolic_correct": s.symbolic_correct,
                    "unit_correct": s.unit_correct,
                    "coherent": s.coherent,
                    "score": s.score,
                }
                for s in step_results
            ],
            "model": os.getenv("MODEL", "gpt-4o"),
            "processing_time_ms": elapsed,
        }
        results.append(result_obj)
        print(f"  {problem['id']} → {score_data['verdict']} ({score_data['reasoning_score']})")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    passed = sum(1 for r in results if r["verdict"] == "PASS")
    print(f"\nDone: {passed}/{len(results)} PASS | results → {output_path}")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--output", default="outputs/results.json")
    args = parser.parse_args()
    run_benchmark(args.benchmark, args.output)
