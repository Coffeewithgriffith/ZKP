"""Pure-stdlib functional tests; run with python -m unittest discover -s prototype -v."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import unittest

try:
    from .policy_gate import Payment, Policy, ReferenceGate, Rejected, action_digest
except ImportError:
    from policy_gate import Payment, Policy, ReferenceGate, Rejected, action_digest


class GateTests(unittest.TestCase):
    def setUp(self):
        self.policy = Policy('eip155:84532', 'USDC', frozenset({'merchant'}), 100, 150, 30, 7)
        self.gate = ReferenceGate(self.policy, '0xGate')
        self.action = Payment('eip155:84532', 'exact', 'USDC', 'merchant', 70,
                              '/data', 'requirements-digest', 'nonce-1', 1100)

    def settle(self, a=None, digest=None, **kwargs):
        a = a or self.action
        args = dict(claimed_digest=action_digest(a, '0xGate') if digest is None else digest,
                    now=1000, oracle_timestamp=995, registry_epoch=7, delegation_expiry=1050)
        args.update(kwargs)
        return self.gate.settle(a, **args)

    def test_clean_payment(self):
        self.assertEqual(self.settle(), action_digest(self.action, '0xGate'))
        self.assertEqual(self.gate.total_spent, 70)

    def test_replay(self):
        self.settle()
        with self.assertRaises(Rejected): self.settle()

    def test_digest_mutation(self):
        with self.assertRaises(Rejected):
            self.settle(replace(self.action, amount=80), digest=action_digest(self.action, '0xGate'))

    def test_wrong_payee(self):
        with self.assertRaises(Rejected): self.settle(replace(self.action, pay_to='attacker'))

    def test_wrong_network(self):
        with self.assertRaises(Rejected): self.settle(replace(self.action, network='eip155:1'))

    def test_stale_oracle(self):
        with self.assertRaises(Rejected): self.settle(oracle_timestamp=900)

    def test_future_oracle(self):
        with self.assertRaises(Rejected): self.settle(oracle_timestamp=1001)

    def test_wrong_epoch(self):
        with self.assertRaises(Rejected): self.settle(registry_epoch=6)

    def test_expired_delegation(self):
        with self.assertRaises(Rejected): self.settle(delegation_expiry=999)

    def test_expired_payment(self):
        with self.assertRaises(Rejected): self.settle(now=1101)

    def test_budget(self):
        self.settle()
        with self.assertRaises(Rejected): self.settle(replace(self.action, nonce='nonce-2', amount=90))

    def test_invalid_payment(self):
        with self.assertRaises(Rejected): self.settle(replace(self.action, amount=0))

    def test_concurrent_budget(self):
        def job(i):
            a = replace(self.action, amount=80, nonce=f'concurrent-{i}')
            try:
                self.settle(a)
                return True
            except Rejected:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(job, range(2)))
        self.assertEqual(results.count(True), 1)
        self.assertEqual(self.gate.total_spent, 80)


if __name__ == '__main__':
    unittest.main()
