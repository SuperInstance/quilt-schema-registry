"""Canonical schemas and validation for the Quilt substrate walker fleet."""
from __future__ import annotations
from typing import Any, Optional
import hashlib
import json


# The canonical witness envelope — every substrate walker emits this shape.
# This is the contract that makes receipts composable across the fleet.
CANONICAL_ENVELOPE = {
    "witness_id": str,          # sha256-of-canonical, unique per receipt
    "prev_witness_id": str,     # "" for the genesis receipt
    "polarity": str,            # "ACCEPT" | "DRIFT" | "REFUSE"
    "substrate": str,           # which walker emitted this
    "cell_id": str,             # which item the receipt is about
    "status": str,              # walker-specific status text
    "timestamp": (int, float),  # unix time
    "payload": dict,            # walker-specific extra data
}

# Required field names (for quick checks)
CANONICAL_FIELDS = list(CANONICAL_ENVELOPE.keys())

# Polarity is a closed enum
POLARITY_VALUES = ["ACCEPT", "DRIFT", "REFUSE"]

# The 14-tuple cell schema (the substrate's internal cell representation)
# 5 opcodes + 6 adopted + 3 ledger = 14
CELL_14_TUPLE = [
    "id",          # stable cell id
    "kind",        # one of RECEIPT_KINDS (26 kinds)
    "payload",     # cell-specific data
    "parents",     # list of parent cell ids (causal lineage)
    "links",       # list of edges in the lattice graph
    "witnesses",   # list of witness ids attached to this cell
    "effects",     # side-effects produced
    "ticker",      # last tick (from TICK opcode)
    "hex",         # content hash (sha256)
    "tag",         # human-readable label
    "meta",        # arbitrary metadata dict
    "created_at",  # timestamp of creation
    "updated_at",  # timestamp of last update
    "author",      # who/what created this cell
]

# 5 base opcodes + 6 adopted = 11 opcodes
OPCODES_5 = ["BIND", "LINK", "EFFECT", "VIEW", "TICK"]
OPCODES_6_ADOPTED = ["FORGET", "PROOF", "ROUTE", "CRDT", "WORLD", "TIME"]
OPCODES_11 = OPCODES_5 + OPCODES_6_ADOPTED

# 26 cell kinds (the universe of cells we know how to build)
RECEIPT_KINDS = [
    "room",          # a contained space (the substrate's anchor)
    "vessel",        # holds secrets + makes choices
    "perception",    # sensor data
    "document",      # a piece of writing
    "decision",      # a verdict (binary or weighted)
    "claim",         # legalese claim
    "counter",       # counter-claim
    "contract",      # binding agreement
    "seed",          # four-scalar genome cell
    "pecked",        # post-peck (inside/outside)
    "witness",       # a single observation
    "chain",         # a sequence of witnesses
    "graph",         # a lattice of cells
    "tree",          # hierarchical cells
    "vector",        # embedding cell (768-dim default)
    "score",         # canonicity score
    "route",         # routing solution (VRP/TSP)
    "program",       # LP/MILP problem
    "solution",      # LP/MILP solution
    "fable",         # narrative artifact
    "doctrine",      # rule/contract that other cells follow
    "epoch",         # time-bracketed batch
    "organ",         # multi-lens composition
    "tissue",        # similarity-grouped cells
    "organism",      # the walker
    "snapshot",      # the frozen state
]

assert len(CELL_14_TUPLE) == 14, f"expected 14, got {len(CELL_14_TUPLE)}"
assert len(OPCODES_11) == 11, f"expected 11, got {len(OPCODES_11)}"
assert len(RECEIPT_KINDS) == 26, f"expected 26, got {len(RECEIPT_KINDS)}"


class Schema:
    """The registry of substrate walker schemas.

    Substrates register their compatibility with the canonical envelope.
    A substrate is "compliant" if it emits all 8 canonical fields.
    A substrate is "compatible" if it emits a SUBSET of canonical fields.
    """

    _substrates: dict[str, dict] = {}

    @classmethod
    def register_substrate(cls, name: str, fields: list[str],
                           description: str = "",
                           extras: dict = None) -> None:
        """Register a substrate type with its supported fields."""
        unknown = set(fields) - set(CANONICAL_FIELDS)
        if unknown:
            raise ValueError(
                f"substrate '{name}' has non-canonical fields: {unknown}. "
                f"Allowed: {CANONICAL_FIELDS}. "
                f"Use 'extras' for substrate-specific fields."
            )
        cls._substrates[name] = {
            "name": name,
            "fields": fields,
            "description": description,
            "extras": extras or {},
            "is_compliant": set(CANONICAL_FIELDS).issubset(set(fields)),
        }

    @classmethod
    def substrate_types(cls) -> list[str]:
        return sorted(cls._substrates.keys())

    @classmethod
    def get(cls, name: str) -> Optional[dict]:
        return cls._substrates.get(name)

    @classmethod
    def compliant(cls) -> list[str]:
        """Substrates that emit all 8 canonical fields."""
        return [n for n, s in cls._substrates.items() if s["is_compliant"]]

    @classmethod
    def reset(cls) -> None:
        cls._substrates = {}


# Pre-register the known walkers (so validation works out of the box)
for name, desc in [
    ("VibeReceipt", "quilt-seed.vibe cynicism-dial walker"),
    ("CUReceipt", "quilt-seed.cu_substrate collective-unconscious RAG"),
    ("OptimizationReceipt", "quilt-optimization cuOpt walker"),
    ("OrganismReceipt", "quilt-organism corpus walker"),
    ("VectorizeReceiver", "quilt-organism vectorize receiver"),
    ("CanonScoreReceiver", "quilt-organism canon-score receiver"),
    ("TraceReceipt", "quilt-trace visualizer output"),
    ("JEVReceipt", "jev-quilt oracle session"),
]:
    Schema.register_substrate(
        name,
        CANONICAL_FIELDS,
        description=desc,
    )


def validate_receipt(receipt: dict, substrate: str = None) -> tuple[bool, list[str]]:
    """Validate a receipt against the canonical envelope.

    Returns:
        (ok, errors) — ok is True if the receipt has all 8 fields
    """
    errors = []

    if not isinstance(receipt, dict):
        return False, [f"receipt must be a dict, got {type(receipt).__name__}"]

    # Check canonical fields
    for field_name in CANONICAL_FIELDS:
        if field_name not in receipt:
            errors.append(f"missing canonical field: {field_name}")

    # Check polarity enum
    pol = receipt.get("polarity")
    if pol is not None and pol not in POLARITY_VALUES:
        errors.append(f"invalid polarity: '{pol}' not in {POLARITY_VALUES}")

    # Type checks (lenient: only check fields that are present)
    for fname, ftype in CANONICAL_ENVELOPE.items():
        if fname in receipt:
            val = receipt[fname]
            if isinstance(ftype, tuple):
                if not isinstance(val, ftype):
                    errors.append(f"field '{fname}' has wrong type: expected {ftype}, got {type(val).__name__}")
            elif ftype is dict and not isinstance(val, dict):
                errors.append(f"field '{fname}' must be dict, got {type(val).__name__}")
            elif ftype is str and not isinstance(val, str):
                errors.append(f"field '{fname}' must be str, got {type(val).__name__}")

    # Substrate compatibility
    if substrate:
        sub = Schema.get(substrate)
        if sub is None:
            errors.append(f"unknown substrate: '{substrate}'")
        else:
            for f in sub["fields"]:
                if f not in receipt:
                    errors.append(f"substrate '{substrate}' requires field '{f}'")

    return len(errors) == 0, errors


def validate_chain(receipts: list[dict]) -> tuple[bool, list[str]]:
    """Validate a chain of receipts (each links to the previous)."""
    errors = []

    if not receipts:
        return False, ["empty receipt chain"]

    prev = ""
    for i, r in enumerate(receipts):
        if not isinstance(r, dict):
            errors.append(f"receipt[{i}] is not a dict")
            continue

        # Check it has canonical envelope
        ok, sub_errors = validate_receipt(r)
        if not ok:
            errors.extend([f"receipt[{i}]: {e}" for e in sub_errors])
            continue

        # Check chain link
        if r.get("prev_witness_id") != prev:
            errors.append(
                f"receipt[{i}] chain broken: prev_witness_id='{r.get('prev_witness_id')}' "
                f"but expected '{prev}'"
            )

        prev = r.get("witness_id", "")

    return len(errors) == 0, errors


def field_compatibility(receipt: dict) -> dict:
    """Score how compatible a receipt is with the canonical envelope.

    Returns:
        {
          "compatible": bool,    # all required fields present
          "missing": list[str],  # canonical fields not present
          "extra": list[str],    # non-canonical fields
          "polarity_ok": bool,   # polarity is in enum
          "score": float,        # 0-1, % of canonical fields present
        }
    """
    if not isinstance(receipt, dict):
        return {"compatible": False, "missing": CANONICAL_FIELDS, "extra": [],
                "polarity_ok": False, "score": 0.0}

    missing = [f for f in CANONICAL_FIELDS if f not in receipt]
    extra = [k for k in receipt if k not in CANONICAL_FIELDS]
    pol_ok = receipt.get("polarity") in POLARITY_VALUES

    score = (len(CANONICAL_FIELDS) - len(missing)) / len(CANONICAL_FIELDS)

    return {
        "compatible": len(missing) == 0,
        "missing": missing,
        "extra": extra,
        "polarity_ok": pol_ok,
        "score": score,
    }


# --- witness identity: the hash recipe -------------------------------------
# Gap found by quilt-executor's witness bridge (use-driven): witness_id was
# documented as "sha256-of-canonical" but the canonicalization was unspecified,
# so two substrates could not reproduce each other's ids. This pins the recipe
# in machine-readable form, RECEIPTS_V2 chart style.
HASH_RECIPE = {
    "algorithm": "sha256",
    "canon": {"format": "json", "sort_keys": True, "separators": [",", ":"],
              "ensure_ascii": False, "encoding": "utf-8"},
    "input": "witness envelope dict (all 8 CANONICAL_FIELDS)",
    "output": "hex64 lowercase, no 0x prefix",
    "recipe_version": "WITNESS_ID_V1",
}

# Conformance vector (WITNESS_ID_V1): the envelope below hashes to this id.
HASH_CONFORMANCE_ENVELOPE = {
    "witness_id": "w000", "prev_witness_id": "", "polarity": "ACCEPT",
    "substrate": "conformance", "cell_id": "cell-0", "status": "ok",
    "timestamp": 1727000000,
    "payload": {"note": "registry hash recipe conformance"},
}
HASH_CONFORMANCE_VECTOR = "3162a3b69719190275cbb0079c3bb1e2ace49c8ad2e3a575eb41f1d92e6ce83e"


def compute_witness_id(envelope: dict) -> str:
    """Reproducible witness identity per HASH_RECIPE (WITNESS_ID_V1)."""
    spec = HASH_RECIPE["canon"]
    blob = json.dumps(envelope, sort_keys=spec["sort_keys"],
                      separators=tuple(spec["separators"]),
                      ensure_ascii=spec["ensure_ascii"]).encode(spec["encoding"])
    return hashlib.sha256(blob).hexdigest()
