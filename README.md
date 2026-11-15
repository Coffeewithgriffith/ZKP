# ZK-TAF — ICBC 2027 research draft

Research materials for **ZK-TAF: Proof-Carrying x402 Payments for Policy-Gated Agentic Blockchain Finance**.

## Repository layout

- `paper/main.tex` — anonymised IEEE conference manuscript (Overleaf source, from the provided archive).
- `paper/references.bib` — BibLaTeX bibliography (from the provided archive).
- `paper/README.md` — original Overleaf instructions from the provided archive.
- `prototype/policy_gate.py` — **new illustrative Python reference model** of deterministic payment-gate checks, replay protection and serialized budget accounting.
- `prototype/test_policy_gate.py` — functional tests for the reference model.

## Build the manuscript

Upload the three files in `paper/` to Overleaf as a project; use pdfLaTeX and Biber as specified in `paper/README.md`.

## Run the reference model tests

Python 3.10+ and the Python standard library are sufficient:

```sh
python -m unittest discover -s prototype -p 'test_*.py' -v
```

## Research integrity and status

**The uploaded archive contained only `main.tex`, `references.bib` and `README.md`.** It did *not* contain the experiment script or raw CSV files mentioned in the manuscript. Therefore the reported local pilot measurements have **not been independently reproduced by the code in this repository**. The new `prototype/` code is a small deterministic reference model, not the original pilot implementation.

The prototype has **no zero-knowledge prover/verifier, x402 client/server, payment signature verification, smart contract, authenticated oracle, or live blockchain settlement**. It is **not production-ready**, and its JSON digest is illustrative rather than a standardized ABI/EIP-712 encoding. Its source-level policy checks and unit tests do not substantiate the paper's benchmark values or the six-property ZK relation.

Before making a reproducibility claim, add the original pilot implementation, raw result logs/CSVs, seed, environment and hardware metadata, and exact measurement procedure. A full ZK-TAF implementation would additionally require the specified circuit, proof verifier, on-chain gate, and x402 adapter.