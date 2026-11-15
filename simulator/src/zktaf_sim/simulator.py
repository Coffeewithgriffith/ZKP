"""Single-process policy simulation for researching the ZK-TAF architecture.

This code is NOT a payment system. No cryptographic credential or oracle proof is
verified, and the digest is not a chain-approved action encoding. Do not use for funds.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from threading import Lock
from typing import Any
import json


class GateRejected(ValueError):
    """An encoded local policy rule rejected the action."""


def _bytes_len_prefixed(value: str) -> bytes:
    """Demonstrative typed field encoding, not x402's consensus definition."""
    b = value.encode("utf-8")
    return len(b).to_bytes(4, "big") + b


def _canonical_json(value: Any) -> bytes:
    # Research-only JSON normalisation for a sample challenge. Production needs
    # formal canonical typed encoding, cross-language vectors and ambiguity tests.
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def parse_v2_challenge(challenge: dict[str, Any], offer_index: int = 0) -> "PaymentIntent":
    """Parse a *decoded* x402 v2 sample; no HTTP/signatures/settlement.

    The entire challenge is hashed so mutations of resource/other offers and
    extensions also change the intent digest (stronger than a selected-offer-only
    binding, but this is a local research design, not mandated x402 behavior).
    """
    if type(challenge) is not dict or type(challenge.get("x402Version")) is not int or challenge["x402Version"] != 2:
        raise GateRejected("x402 v2 required")
    if type(challenge.get("resource")) is not dict or not challenge["resource"].get("url"):
        raise GateRejected("resource url required")
    accepts = challenge.get("accepts")
    if type(accepts) is not list or not (0 <= offer_index < len(accepts)):
        raise GateRejected("valid selected offer required")
    offer = accepts[offer_index]
    if type(offer) is not dict:
        raise GateRejected("offer must be an object")
    fields = ["scheme", "network", "asset", "payTo", "amount", "maxTimeoutSeconds"]
    if any(f not in offer for f in fields):
        raise GateRejected("incomplete payment offer")
    if any(type(offer[k]) is not str or not offer[k] for k in ("scheme", "network", "asset", "payTo", "amount")):
        raise GateRejected("malformed payment offer")
    if not offer["amount"].isascii() or not offer["amount"].isdecimal() or int(offer["amount"]) <= 0:
        raise GateRejected("positive integer atomic-token amount required")
    if type(offer["maxTimeoutSeconds"]) is not int or offer["maxTimeoutSeconds"] <= 0:
        raise GateRejected("invalid timeout")
    if offer["scheme"] != "exact" or ":" not in offer["network"]:
        raise GateRejected("demo supports exact and CAIP-2 networks only")
    return PaymentIntent(
        scheme=offer["scheme"], network=offer["network"], asset=offer["asset"],
        pay_to=offer["payTo"], amount=int(offer["amount"]),
        resource=challenge["resource"]["url"],
        requirements_hash=sha256(_canonical_json(challenge)).hexdigest(),
    )


@dataclass(frozen=True)
class PaymentIntent:
    scheme: str
    network: str
    asset: str
    pay_to: str
    amount: int
    resource: str
    requirements_hash: str


@dataclass(frozen=True)
class Quote:
    """Trusted-source string is a *configuration check*, not oracle verification."""
    source_id: str
    observed_at: int
    reference_price: int
    execution_price: int


@dataclass(frozen=True)
class Policy:
    delegated_to: str
    delegation_expires_at: int
    approved_model_id: str
    approved_policy_id: str
    registry_epoch: int
    network: str
    asset: str
    pay_to: str
    resource: str
    max_amount: int
    total_budget: int
    allowed_oracle_source: str
    max_oracle_age_seconds: int
    max_slippage_bps: int


def action_digest(intent: PaymentIntent, nonce: str, deadline: int, gate_id: str) -> str:
    """Domain-separate and bind all action fields, replay nonce, deadline and gate.

    This is *not* the manuscript's formally agreed on-chain typed encoding.
    """
    fields = (intent.network, intent.scheme, intent.asset, intent.pay_to,
              str(intent.amount), intent.resource, intent.requirements_hash,
              nonce, str(deadline), gate_id)
    preimage = b"ZKTAF-LOCAL-PAY-v1\x00" + b"".join(_bytes_len_prefixed(x) for x in fields)
    return sha256(preimage).hexdigest()


class LocalGate:
    """In-memory deterministic policy gate. Not a smart account or ZK verifier."""

    def __init__(self, policy: Policy, gate_id: str = "demo-gate"):
        self.policy = policy
        self.gate_id = gate_id
        self.spent = 0
        self.version = 0
        self.used_nonces: set[str] = set()
        self._lock = Lock()

    def simulate_settlement(self, *, intent: PaymentIntent, expected_digest: str,
                            nonce: str, deadline: int, now: int,
                            actor_id: str, model_id: str, policy_id: str,
                            registry_epoch: int, quote: Quote,
                            expected_state_version: int) -> dict[str, int | str]:
        """Check then update local state atomically; no on-chain payment occurs.

        `expected_digest` is assumed to have been approved externally. This
        simulator cannot prove who approved it: authority proof is unimplemented.
        """
        with self._lock:
            p = self.policy
            if not nonce or len(nonce) > 128:
                raise GateRejected("invalid nonce")
            if nonce in self.used_nonces:
                raise GateRejected("replay rejected")
            if now > deadline or now > p.delegation_expires_at:
                raise GateRejected("deadline or delegation expired")
            if actor_id != p.delegated_to:
                raise GateRejected("delegation scope rejected")
            if (model_id, policy_id, registry_epoch) != (p.approved_model_id, p.approved_policy_id, p.registry_epoch):
                raise GateRejected("model/policy registry rejected")
            if expected_state_version != self.version:
                raise GateRejected("stale state version")
            if action_digest(intent, nonce, deadline, self.gate_id) != expected_digest:
                raise GateRejected("action/challenge mutation")
            if (intent.scheme, intent.network, intent.asset, intent.pay_to, intent.resource) != (
                "exact", p.network, p.asset, p.pay_to, p.resource):
                raise GateRejected("network/scheme/asset/payee/resource mismatch")
            if intent.amount <= 0 or intent.amount > p.max_amount or self.spent + intent.amount > p.total_budget:
                raise GateRejected("amount or aggregate budget exceeded")
            if quote.source_id != p.allowed_oracle_source:
                raise GateRejected("untrusted oracle source ID")
            if quote.observed_at > now or now - quote.observed_at > p.max_oracle_age_seconds:
                raise GateRejected("stale or future oracle timestamp")
            if quote.reference_price <= 0 or quote.execution_price <= 0:
                raise GateRejected("invalid quote")
            # Integer arithmetic prevents floating point threshold boundary drift.
            if abs(quote.execution_price - quote.reference_price) * 10_000 > p.max_slippage_bps * quote.reference_price:
                raise GateRejected("slippage exceeded")
            self.spent += intent.amount
            self.version += 1
            self.used_nonces.add(nonce)
            return {"status": "SIMULATED_ONLY", "spent": self.spent, "state_version": self.version,
                    "action_digest": expected_digest}
