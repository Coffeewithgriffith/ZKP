# ZK-TAF — Python Research Prototypes

Educational policy-gating research prototypes for studying agentic blockchain payment controls. **This public GitHub repository no longer contains the ICBC 2027 Overleaf manuscript or bibliography in its current main branch.**

## Repository layout

- `prototype/policy_gate.py` — illustrative deterministic payment-policy reference model.
- `prototype/test_policy_gate.py` — tests for the reference model.
- `simulator/README.md` — documented x402 v2 sample-challenge policy simulator.
- `simulator/src/zktaf_sim/simulator.py` — research-only Python simulator.
- `simulator/tests/test_gate.py` — unit tests.
- `simulator/examples/demo.py` — local demonstration with no real payments.
- `simulator/experiments/smoke_benchmark.py` — synthetic Python-only timing test.
- `simulator/docs/REPRODUCIBILITY.md` — research limitations.
- `.github/workflows/zktaf-simulator.yml` — GitHub Actions CI.

## Run reference-model tests

```sh
python -m unittest discover -s prototype -p 'test_*.py' -v
```

## Run the x402 policy simulator

Python 3.10+:

```sh
python -m pip install -e ./simulator
python simulator/examples/demo.py
python -m unittest discover -s simulator/tests -v
python simulator/experiments/smoke_benchmark.py --repeats 100
```

## Research integrity

Neither Python prototype is an operational ZK prover/verifier or actual on-chain payment system. The original pilot's experimental scripts and raw CSV results were not included in the provided manuscript archive; neither prototype reproduces the claimed results. The synthetic benchmark is not a ZK proving/verification, gas, or blockchain finality benchmark.

**Publication note:** `paper/main.tex` and `paper/references.bib` were deleted from the current branch at the author's request. Earlier public Git commits may still contain these sources; deletion from the latest branch does not erase Git history or copies held elsewhere.
