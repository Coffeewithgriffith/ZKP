"""Synthetic policy tests; not actual ZK, x402, oracle or EVM tests."""
import copy
import unittest
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from zktaf_sim import Policy, Quote, LocalGate, action_digest, parse_v2_challenge, GateRejected

NOW = 1_700_000_000
CHALLENGE = {"x402Version": 2, "resource": {"url": "https://example.invalid/api"},
             "accepts": [{"scheme": "exact", "network": "eip155:84532", "asset": "TOKEN",
                          "payTo": "MERCHANT", "amount": "100", "maxTimeoutSeconds": 60}]}


def policy():
    return Policy(delegated_to="agent", delegation_expires_at=NOW + 120,
                  approved_model_id="approved-model", approved_policy_id="approved-policy",
                  registry_epoch=3, network="eip155:84532", asset="TOKEN",
                  pay_to="MERCHANT", resource="https://example.invalid/api",
                  max_amount=150, total_budget=250, allowed_oracle_source="feed-A",
                  max_oracle_age_seconds=30, max_slippage_bps=100)


class LocalGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = LocalGate(policy())
        self.intent = parse_v2_challenge(CHALLENGE)
        self.kw = dict(intent=self.intent, expected_digest=action_digest(self.intent, "n1", NOW + 60, "demo-gate"),
                       nonce="n1", deadline=NOW + 60, now=NOW, actor_id="agent",
                       model_id="approved-model", policy_id="approved-policy",
                       registry_epoch=3, quote=Quote("feed-A", NOW - 5, 10000, 10050),
                       expected_state_version=0)

    def rejects(self, **changes):
        kw = dict(self.kw, **changes)
        with self.assertRaises(GateRejected):
            self.gate.simulate_settlement(**kw)
        self.assertEqual(self.gate.spent, 0)
        self.assertEqual(self.gate.version, 0)

    def test_clean_accepted(self):
        result = self.gate.simulate_settlement(**self.kw)
        self.assertEqual(result["spent"], 100)
        self.assertEqual(result["status"], "SIMULATED_ONLY")

    def test_replay(self):
        self.gate.simulate_settlement(**self.kw)
        with self.assertRaisesRegex(GateRejected, "replay"):
            self.gate.simulate_settlement(**self.kw)
        self.assertEqual(self.gate.spent, 100)

    def test_payee_mutation_after_digest(self):
        self.rejects(intent=replace(self.intent, pay_to="ATTACKER"))

    def test_amount_mutation_after_digest(self):
        self.rejects(intent=replace(self.intent, amount=150))

    def test_asset_mutation_after_digest(self):
        self.rejects(intent=replace(self.intent, asset="EVIL"))

    def test_wrong_network(self):
        mutated=replace(self.intent, network="eip155:1")
        self.rejects(intent=mutated, expected_digest=action_digest(mutated, "n1", NOW + 60, "demo-gate"))

    def test_wrong_resource(self):
        mutated=replace(self.intent, resource="https://example.invalid/other")
        self.rejects(intent=mutated, expected_digest=action_digest(mutated, "n1", NOW + 60, "demo-gate"))

    def test_stale_quote(self):
        self.rejects(quote=Quote("feed-A", NOW - 31, 10000, 10000))

    def test_untrusted_oracle(self):
        self.rejects(quote=Quote("feed-B", NOW - 1, 10000, 10000))

    def test_slippage(self):
        self.rejects(quote=Quote("feed-A", NOW, 10000, 10200))

    def test_revoke_epoch(self):
        self.rejects(registry_epoch=2)

    def test_wrong_model(self):
        self.rejects(model_id="unapproved-model")

    def test_expired_delegation(self):
        self.rejects(now=NOW + 121)

    def test_stale_state_version(self):
        self.rejects(expected_state_version=5)

    def test_unauthorized_actor(self):
        self.rejects(actor_id="intruder")

    def test_over_budget(self):
        self.gate.simulate_settlement(**self.kw)
        kw=dict(self.kw, nonce="n2", expected_state_version=1)
        kw["expected_digest"] = action_digest(self.intent, "n2", NOW + 60, "demo-gate")
        self.gate.simulate_settlement(**kw)
        kw.update(nonce="n3", expected_state_version=2)
        kw["expected_digest"] = action_digest(self.intent, "n3", NOW + 60, "demo-gate")
        with self.assertRaisesRegex(GateRejected, "budget"):
            self.gate.simulate_settlement(**kw)
        self.assertEqual(self.gate.spent, 200)

    def test_concurrent_state_overspend(self):
        def one(i):
            kw=dict(self.kw, nonce=f"n{i}")
            kw["expected_digest"] = action_digest(self.intent, kw["nonce"], NOW + 60, "demo-gate")
            try:
                self.gate.simulate_settlement(**kw)
                return True
            except GateRejected:
                return False
        with ThreadPoolExecutor(max_workers=10) as ex:
            results = list(ex.map(one, range(10)))
        # Only one can consume expected_state_version=0.
        self.assertEqual(sum(results), 1)
        self.assertEqual(self.gate.spent, 100)

    def test_challenge_extensions_change_digest(self):
        mutated=copy.deepcopy(CHALLENGE)
        mutated["extensions"]={"zktaf": {"context": "other"}}
        other=parse_v2_challenge(mutated)
        self.assertNotEqual(action_digest(other, "n1", NOW+60, "demo-gate"),
                            action_digest(self.intent, "n1", NOW+60, "demo-gate"))

    def test_unsigned_false_but_fresh_oracle_cannot_be_detected(self):
        # This is a deliberate limitation demonstration.
        forged_but_fresh=Quote("feed-A", NOW, 10000, 10000)
        result=self.gate.simulate_settlement(**dict(self.kw, quote=forged_but_fresh))
        self.assertEqual(result["status"], "SIMULATED_ONLY")

    def test_bad_challenges(self):
        for change in ({"x402Version": 1}, {"accepts": []}):
            broken=copy.deepcopy(CHALLENGE); broken.update(change)
            with self.assertRaises(GateRejected):
                parse_v2_challenge(broken)


if __name__ == "__main__":
    unittest.main()
