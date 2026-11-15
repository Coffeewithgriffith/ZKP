# Reproducibility and research boundaries

## Original data not available

The research manuscript source package used to prepare this prototype contained a LaTeX draft, bibliography and documentation, **not** the original experimental script and raw CSV logs. The manuscript and bibliography are not included in this public repository to preserve submission confidentiality. No manuscript pilot outcomes or timing values have been independently reproduced.

## What is actually implemented

Python policy checks in a single process, domain-separated action digest, decoded sample v2 x402 challenge parsing, in-memory nonce and cumulative budget tracking, stale-quote rejection, local concurrency lock, illustrative demo, unit tests and a local smoke benchmark. An allowed source ID is not proof that an oracle message is signed or true. A passed model ID does not prove which model produced an action. The claimed externally approved digest is not cryptographically verified.

## Missing for a genuine full ZK-TAF evaluation

1. Canonical typed action/PaymentRequired encoding with interoperability test vectors.
2. Delegation credential signatures, model/policy provenance, revocation and key management.
3. Authenticated oracle feeds and explicit assumptions about manipulated but valid data.
4. ZK statement, circuit, proving keys, proof generation and proof verifier.
5. Exclusive smart-account / escrow settlement gate with actual on-chain state and replay protection.
6. Real signed x402 requests, middleware/facilitator integration and receipts.
7. Matched baseline experiments for ungated, deterministic policy only, conventional x402, full ZK-TAF and no-ZK exclusive settlement variants.
8. Raw per-run data, hardware/software versions, seeds, clean/attack case matrices, and statistics for proof size, proving time, verification time, gas, finality and forbidden transaction acceptance.

## Evidence boundary

The 20 unit tests demonstrate expected behaviour for the coded local checks, not cryptographic soundness or deployed payment safety. The smoke benchmark measures only local Python operation. Do **not** present it as a replication of previously reported experiments.

## Publication

This existing GitHub repository is publicly accessible. The draft paper, anonymous author list, original figures and bibliography were intentionally omitted. Avoid including links to this account in an anonymous submission without checking review policy.
