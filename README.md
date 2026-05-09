# PhD-Level STEM Reasoning Framework

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Framework: SymPy](https://img.shields.io/badge/Library-SymPy-green.svg)](https://www.sympy.org/)
[![Output: LaTeX/PDF](https://img.shields.io/badge/Output-LaTeX%20%2F%20PDF-orange.svg)](https://www.latex-project.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: Pytest](https://img.shields.io/badge/Tests-Pytest-white.svg)](https://docs.pytest.org/)

---

# PhD-Level STEM Reasoning Framework

Step-by-step symbolic deduction engine for evaluating frontier LLMs on PhD-level Physics and Chemistry problems. Built from real benchmark work — the core insight is that **standard QA benchmarks test recall, not reasoning**. A model that produces the correct final answer via a flawed reasoning chain should not pass.

This framework evaluates **reasoning chains**, not just final answers. Each solution step is verified independently against symbolic ground truth, producing a per-step correctness trace and an overall reasoning score.

---

## Architecture

```
Problem (LaTeX / JSON)
      │
      ▼
┌──────────────────────┐
│   Problem Parser     │  ← extracts variables, constraints, expected steps
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│   LLM Solver         │  ← sends problem to model, receives chain-of-thought
└────────┬─────────────┘
         │ reasoning_chain[]
         ▼
┌─────────────────────────────────────────────┐
│           Step-by-Step Verifier             │
│                                             │
│  ┌──────────────────┐                       │
│  │ Symbolic Check   │  ← SymPy equation     │
│  │                  │    equivalence        │
│  └──────────────────┘                       │
│  ┌──────────────────┐                       │
│  │ Unit Check       │  ← dimensional        │
│  │                  │    analysis           │
│  └──────────────────┘                       │
│  ┌──────────────────┐                       │
│  │ Step Coherence   │  ← each step follows  │
│  │                  │    from previous      │
│  └──────────────────┘                       │
└────────┬────────────────────────────────────┘
         │
         ▼
┌──────────────────────┐
│   LaTeX Report       │  ← per-step trace, score, verdict
│   Generator          │
└──────────────────────┘
         │
         ▼
  reasoning_score + step_trace[] + LaTeX PDF report
```

**Why step-level instead of answer-level?**

Final answer correctness is a weak signal. A model can arrive at the right answer via error cancellation or coincidence while the underlying reasoning chain is broken. Step verification catches these failures and produces interpretable diagnostics — you know exactly *which* step failed and *why*, not just that the model was wrong.

---

## Quickstart

### Install

```bash
git clone https://github.com/Rdev-ops-lab/stem-reasoning-framework
cd stem-reasoning-framework

pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

### Run a benchmark

```bash
# Mock mode — no API key needed
USE_MOCK=true python examples/sample_usage.py

# Evaluate a full benchmark set
OPENAI_API_KEY=your_key python -m src.runner --benchmark benchmarks/physics_mechanics.json

# Generate LaTeX report
python -m src.report_generator --results outputs/results.json --out outputs/report.tex
```

---

## Example Output

```json
{
  "problem_id": "PHY-001",
  "domain": "mechanics",
  "difficulty": "phd",
  "final_answer_correct": true,
  "reasoning_score": 0.72,
  "verdict": "PARTIAL",
  "step_trace": [
    { "step": 1, "description": "Define coordinate system and free body diagram",
      "symbolic_correct": true,  "unit_correct": true,  "coherent": true,  "score": 1.0 },
    { "step": 2, "description": "Apply Newton's second law: F = ma",
      "symbolic_correct": true,  "unit_correct": true,  "coherent": true,  "score": 1.0 },
    { "step": 3, "description": "Substitute values: a = 12.5 m/s²",
      "symbolic_correct": false, "unit_correct": true,  "coherent": true,  "score": 0.33 },
    { "step": 4, "description": "Calculate displacement using kinematics",
      "symbolic_correct": false, "unit_correct": false, "coherent": false, "score": 0.0 }
  ],
  "model": "gpt-4o",
  "processing_time_ms": 3241.0
}
```

**Key insight from this result:** The model produced the correct final answer (by error cancellation) but failed at step 3. Without step-level verification, this would score as a full pass. The reasoning score of 0.72 correctly reflects a partial failure — the model cannot be trusted on related problems.

---

## How Verification Works

Each step in the model's chain-of-thought is independently checked across three dimensions:

**Symbolic Check (SymPy)**
Parses the step's equation using SymPy and checks algebraic equivalence against the expected expression. String matching fails on equivalent forms — `F = ma` and `a = F/m` are the same equation. SymPy handles this correctly by simplifying the difference to zero.

**Unit / Dimensional Check**
Scans for unit patterns (N, kg, m/s², J, etc.) and flags dimensional inconsistencies. A numerically correct answer with wrong units is a reasoning error, not a pass.

**Step Coherence**
Checks whether each step logically follows from the previous one. If step *n* has a symbolic error, step *n+1* is automatically marked incoherent — an error in the chain propagates.

**Score per step** = mean of the three boolean checks (0.33, 0.67, or 1.0).

**Reasoning score** = weighted average across all steps, with earlier steps carrying slightly higher weight. An error in step 1 propagates further than an error in the last step — the weighting reflects this.

---

## Benchmark Domains

| Domain | Problems | Difficulty | Topics |
|---|---|---|---|
| `physics_mechanics` | 20 | PhD | Lagrangian mechanics, rigid body dynamics, oscillations |
| `physics_electromagnetism` | 20 | PhD | Maxwell equations, field theory, wave propagation |
| `chemistry_thermodynamics` | 15 | PhD | Gibbs free energy, entropy, phase equilibria |
| `chemistry_kinetics` | 15 | PhD | Reaction rate theory, Arrhenius, transition states |

---

## Run Tests

```bash
# All tests in mock mode — no API key needed
USE_MOCK=true pytest tests/ -v

# With coverage
USE_MOCK=true pytest tests/ --cov=src --cov-report=term-missing
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Required for full mode |
| `USE_MOCK` | `false` | Run without API calls (testing / CI) |
| `MODEL` | `gpt-4o` | LLM to evaluate |
| `REASONING_PASS_THRESHOLD` | `0.80` | Min reasoning score to PASS |
| `PARTIAL_THRESHOLD` | `0.50` | Below this → FAIL |

---

## LaTeX Integration

Problems and solutions are authored in LaTeX for precision — PhD-level STEM problems require exact mathematical notation that plain text cannot represent. The framework parses `.tex` problem files, extracts the symbolic structure, and generates detailed evaluation reports as LaTeX PDFs.

```bash
# Compile a sample problem
pdflatex latex_templates/sample_problem.tex

# Generate full benchmark report from results
python -m src.report_generator --results outputs/results.json --out report.tex
pdflatex report.tex
```

---

## Key Design Decisions

**Step-level over answer-level** — Final answer correctness is a weak signal at PhD difficulty. Models that arrive at the right answer via flawed steps will fail on structurally similar problems. Step verification produces interpretable diagnostics and catches error cancellation.

**Symbolic verification with SymPy** — String matching fails on algebraically equivalent expressions. `F = ma` and `a = F/m` are the same equation written differently. SymPy simplifies the difference to zero and handles this correctly.

**Unit / dimensional analysis as a separate layer** — A numerically correct result with the wrong units is a reasoning failure. Dimensional checking is independent from symbolic checking — both must pass.

**Coherence propagation** — A step that follows from a broken predecessor cannot be marked coherent, regardless of its own symbolic correctness. This prevents a model from accidentally recovering from an error and scoring well despite a broken chain.

**Early-step weighting** — Errors in step 1 propagate further through the chain than errors in the final step. The scoring function applies a small weight premium to earlier steps to reflect this.

**Mock mode** — Full test coverage and CI/CD runs entirely without API keys. Deterministic mock verification allows reliable unit and integration tests across all verifier and scorer logic.

---

## Project Structure

```
stem-reasoning-framework/
├── src/
│   ├── runner.py              # Main benchmark runner
│   ├── llm_solver.py          # LLM interface + chain-of-thought parser
│   ├── step_verifier.py       # Per-step symbolic + unit + coherence check
│   ├── scoring.py             # Reasoning score aggregation (early-step weighted)
│   └── report_generator.py    # LaTeX PDF report generation
├── benchmarks/
│   ├── physics_mechanics.json
│   ├── physics_electromagnetism.json
│   ├── chemistry_thermodynamics.json
│   └── chemistry_kinetics.json
├── latex_templates/
│   ├── sample_problem.tex
│   └── report_template.tex
├── tests/
│   └── test_stem.py
├── examples/
│   └── sample_usage.py
├── outputs/                   # Results JSON + LaTeX reports (gitignored)
├── .github/workflows/
│   └── ci.yml                 # GitHub Actions CI/CD
├── .env.example
└── requirements.txt
```

---

## Related Projects

- [LLM Hallucination Detector](https://github.com/Rdev-ops-lab/llm-hallucination-detector) — Claim-level hallucination detection using LangChain + Bayesian inference
- [Automated AI QA Pipeline](https://github.com/Rdev-ops-lab/ai-qa-pipeline) — Multi-dimensional LLM output scoring at scale (factual accuracy, coherence, instruction-following, safety)

---

## Author

**Rishi Pal Singh** — AI Evaluation Specialist  
[LinkedIn](https://linkedin.com/in/rishi-singh-1413b3384) · [GitHub](https://github.com/Rdev-ops-lab)
