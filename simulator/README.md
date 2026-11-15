# ZK-TAF / x402 — Policy-Gated Agentic Payments (Research Prototype)

**Status: Educational Python simulator only.** This repository contains a newly written local simulation of deterministic agent payment-policy checks motivated by research into trustworthy autonomous blockchain finance. It does **not** contain a zero-knowledge proof system, payment wallet, cryptographic verifier, smart contract, real oracle authentication or live x402 settlement.

**Publication note:** The ICBC 2027 paper draft and its LaTeX sources have intentionally **not** been published here because this repository is public and the manuscript may be subject to anonymous review. This code was not supplied with the original reported pilot and does not independently reproduce any manuscript figures, tables or trial-level results.

## Architecture

    AI Agent --> decoded x402 v2 sample challenge --> Local policy kernel
                        |                                    |
                 challenge digest                    local state update
                                                             |
                            ** Proposed ZK prover / smart-account gate **
                                     (NOT IMPLEMENTED)

## What the Python code tests

| Intended assurance | Simulator behaviour | Unimplemented security property |
|---|---|---|
| Delegation scope | Actor ID and expiry check | Credential signatures and delegation proof |
| Model / policy identity | Approved IDs and registry epoch | Provenance and model execution proof |
| Oracle controls | Configured source ID, timestamp and slippage | Signed oracle authenticity and economic truth |
| State continuity | Mutex-protected version, cumulative budget and nonce tracking | Authenticated on-chain state and exclusive spend path |
| Financial controls | Payee, asset, network, resource and amount checks | Settlement enforcement |
| Exact action binding | Domain-separated SHA-256 digest over sample challenge + action | Formal cross-chain encoding and ZK proof of binding |

## Layout

    src/zktaf_sim/simulator.py       Policy checks and sample challenge parser
    src/zktaf_sim/__init__.py        Public Python imports
    tests/test_gate.py              Twenty local unit tests
    examples/demo.py                Local accept-then-replay rejection demo
    experiments/smoke_benchmark.py  Local timing smoke test only
    docs/REPRODUCIBILITY.md         Limitations and research roadmap
    .github/workflows/tests.yml     Automated tests

## Run (Python 3.10+)

    python -m pip install -e .
    python examples/demo.py
    python -m unittest discover -s tests -v
    python experiments/smoke_benchmark.py --repeats 100 --output smoke_results.csv

All sample URLs are synthetic and use example.invalid; no private keys or real money are required. The simulator makes no network calls and signs no transactions. The smoke benchmark measures only local Python execution, not ZK proving or blockchain latency.

## Six-property research integration

Research would require formal delegation and model/policy registries, signed oracle evidence, a formally specified canonical action encoding, a ZK circuit/prover/verifier, and an **exclusive** smart-account or escrow settlement path. An off-chain check cannot prevent an unconstrained valid wallet signature from bypassing policy. See docs/REPRODUCIBILITY.md.

## Related protocol

x402 official repository: https://github.com/x402-foundation/x402 . This project only parses decoded **sample** x402 v2-style payment requirements; it does not claim conformance to the full protocol.

## Licensing and research integrity

The code here is published under this repository's MIT licence (see LICENSE). Never present synthetic smoke-test outputs as proof metrics, actual chain settlement, or reproduction of unpublished ICBC results. Check conference policies before linking this personally identifiable public repository from a double-blind submission.
