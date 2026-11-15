"""NEW synthetic local smoke benchmark. NOT a real ZK or x402 benchmark."""
import argparse
import csv
from pathlib import Path
from statistics import median
from time import perf_counter_ns
from zktaf_sim import Policy, Quote, LocalGate, action_digest, parse_v2_challenge

NOW=1_700_000_000
CHALLENGE={"x402Version":2,"resource":{"url":"https://example.invalid/api"},
           "accepts":[{"scheme":"exact","network":"eip155:84532","asset":"TKN",
                       "payTo":"MERCHANT","amount":"1","maxTimeoutSeconds":60}]}


def run(repeats):
    intent=parse_v2_challenge(CHALLENGE)
    gate=LocalGate(Policy("agent", NOW + 10000, "model", "policy", 1,
                          "eip155:84532", "TKN", "MERCHANT", "https://example.invalid/api",
                          1, repeats + 1, "feed", 30, 100))
    results=[]
    for i in range(repeats):
        nonce=f"trial-{i}"
        digest=action_digest(intent, nonce, NOW + 20, gate.gate_id)
        before=perf_counter_ns()
        gate.simulate_settlement(intent=intent, expected_digest=digest,
                                 nonce=nonce, deadline=NOW + 20, now=NOW,
                                 actor_id="agent", model_id="model", policy_id="policy",
                                 registry_epoch=1, quote=Quote("feed", NOW, 100, 100),
                                 expected_state_version=i)
        elapsed_ms=(perf_counter_ns()-before)/1_000_000
        results.append({"trial": i, "simulated_gate_ms": f"{elapsed_ms:.6f}",
                        "status": "SIMULATED_ONLY"})
    nums=sorted(float(r["simulated_gate_ms"]) for r in results)
    p95=nums[max(0, (95*len(nums)+99)//100-1)]
    return results,median(nums),p95


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats",type=int,default=100)
    parser.add_argument("--output",type=Path,default=Path("smoke_results.csv"))
    args=parser.parse_args()
    if args.repeats < 1 or args.repeats > 100_000:
        parser.error("repeats must be 1..100000")
    records,med,p95=run(args.repeats)
    with args.output.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=["trial","simulated_gate_ms","status"])
        writer.writeheader(); writer.writerows(records)
    print(f"NEW synthetic local simulator ONLY: n={len(records)} median={med:.4f} ms p95={p95:.4f} ms")
    print(f"Saved {args.output}; NOT a reproduction of manuscript results")


if __name__ == "__main__":
    main()
