"""ZK-TAF deterministic settlement gate reference model.

Educational, off-chain demonstration only. This is NOT a ZK proof system,
cryptographic payment implementation, live x402 adapter, or a reproduction of
measurements reported in the paper. Inputs representing trusted infrastructure
(e.g. authenticated oracles and current registry epoch) are caller-provided.
"""

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from threading import RLock


class Rejected(ValueError):
    """A payment failed a deterministic settlement condition."""


@dataclass(frozen=True)
class Payment:
    network: str
    scheme: str
    asset: str
    pay_to: str
    amount: int  # smallest indivisible units, never a float
    resource: str
    requirements_hash: str
    nonce: str
    deadline: int  # Unix timestamp in seconds


def action_digest(action: Payment, gate_address: str) -> str:
    """Illustrative canonical digest; production requires a typed ABI/EIP-712 spec."""
    if not gate_address:
        raise ValueError('gate_address is required')
    if type(action.amount) is not int or type(action.deadline) is not int:
        raise TypeError('amount and deadline must be integers')
    data = {'domain': 'ZKTAF-PAY-v1', 'gate': gate_address, 'action': asdict(action)}
    encoded = json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return sha256(encoded.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class Policy:
    network: str
    asset: str
    allowed_payees: frozenset[str]
    max_single_payment: int
    total_budget: int
    max_oracle_age: int
    epoch: int


class ReferenceGate:
    """Serializes local decisions; real deployment needs contract-level atomicity."""

    def __init__(self, policy: Policy, gate_address: str):
        self.policy = policy
        self.gate_address = gate_address
        self.total_spent = 0
        self.used_nonces: set[str] = set()
        self._lock = RLock()

    def settle(self, action: Payment, *, claimed_digest: str, now: int,
               oracle_timestamp: int, registry_epoch: int,
               delegation_expiry: int) -> str:
        """Check local preconditions; return action digest on acceptance.

        The caller must authenticate delegation, oracle data, and epoch outside
        this example. No external chain transfer is made.
        """
        with self._lock:
            if type(now) is not int or type(oracle_timestamp) is not int:
                raise Rejected('timestamps must be integers')
            if action.scheme != 'exact' or action.network != self.policy.network:
                raise Rejected('scheme or network not allowed')
            if action.asset != self.policy.asset or action.pay_to not in self.policy.allowed_payees:
                raise Rejected('asset or payee not allowed')
            if type(action.amount) is not int or not 0 < action.amount <= self.policy.max_single_payment:
                raise Rejected('invalid amount or payment limit')
            if not action.resource or not action.requirements_hash or not action.nonce:
                raise Rejected('incomplete action descriptor')
            if type(action.deadline) is not int or now > action.deadline or now > delegation_expiry:
                raise Rejected('expired payment or delegation')
            if registry_epoch != self.policy.epoch:
                raise Rejected('stale policy epoch')
            if oracle_timestamp > now or now - oracle_timestamp > self.policy.max_oracle_age:
                raise Rejected('stale or future oracle')
            if action.nonce in self.used_nonces:
                raise Rejected('replayed nonce')
            if self.total_spent + action.amount > self.policy.total_budget:
                raise Rejected('aggregate budget exceeded')
            digest = action_digest(action, self.gate_address)
            if claimed_digest != digest:
                raise Rejected('payment mutation or wrong gate')
            # Local atomicity of state changes under the lock (not chain settlement).
            self.used_nonces.add(action.nonce)
            self.total_spent += action.amount
            return digest
