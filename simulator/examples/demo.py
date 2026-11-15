"""No-payment demonstration: approved local action then a replay rejection."""
from zktaf_sim import Policy, Quote, LocalGate, action_digest, parse_v2_challenge, GateRejected

NOW = 1_700_000_000  # deterministic synthetic timestamp (not the current time)
CHALLENGE = {
    "x402Version": 2,
    "resource": {"url": "https://example.invalid/paid-market-data"},
    "accepts": [{"scheme": "exact", "network": "eip155:84532",
                 "asset": "0xDemoToken", "payTo": "0xDemoMerchant",
                 "amount": "100", "maxTimeoutSeconds": 60}],
}
POLICY = Policy(
    delegated_to="agent-01", delegation_expires_at=NOW + 300,
    approved_model_id="model-v1", approved_policy_id="policy-v1",
    registry_epoch=7, network="eip155:84532", asset="0xDemoToken",
    pay_to="0xDemoMerchant", resource="https://example.invalid/paid-market-data",
    max_amount=200, total_budget=500, allowed_oracle_source="oracle-demo",
    max_oracle_age_seconds=60, max_slippage_bps=100,
)


def run():
    intent = parse_v2_challenge(CHALLENGE)
    gate = LocalGate(POLICY)
    params = dict(intent=intent, expected_digest=action_digest(intent, "nonce-1", NOW + 30, gate.gate_id),
                  nonce="nonce-1", deadline=NOW + 30, now=NOW, actor_id="agent-01",
                  model_id="model-v1", policy_id="policy-v1", registry_epoch=7,
                  quote=Quote("oracle-demo", NOW - 5, 10000, 10020), expected_state_version=0)
    print("First simulation:", gate.simulate_settlement(**params))
    try:
        gate.simulate_settlement(**params)
    except GateRejected as exc:
        print("Replay blocked:", str(exc))
    print("No blockchain transaction was made.")


if __name__ == "__main__":
    run()
