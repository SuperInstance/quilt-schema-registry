# 🧬 quilt-schema-registry

> The canonical 14-tuple schema + envelope contract. Single source of truth.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![Tests](https://img.shields.io/badge/tests-28/28-brightgreen.svg)](tests/test_registry.py)
[![Pattern](https://img.shields.io/badge/pattern-substrate_walker-purple.svg)]()
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

## What is this?

The substrate walker fleet has grown to 8 walkers. Each emits receipts that
chain together. The schema drift was becoming visible:

- `quilt-seed.vibe.CellReceipt` (8 fields)
- `quilt-organism.OrganismReceipt` (8 fields, mirrored)
- `quilt-optimization.OptimizationReceipt` (8 fields)
- `jev-quilt signed_receipts` (different fields)
- `quilt-trace.AggregateStats` (ad-hoc dicts)

`quilt-schema-registry` is the **single source of truth** for the canonical
envelope, the 14-tuple cell schema, the 11 opcodes, and the 26 cell kinds.

## The canonical envelope (8 fields)

Every substrate walker emits receipts with these 8 fields:

```python
CANONICAL_ENVELOPE = {
    "witness_id": str,         # sha256-of-canonical, unique per receipt
    "prev_witness_id": str,    # "" for the genesis receipt
    "polarity": str,           # "ACCEPT" | "DRIFT" | "REFUSE"
    "substrate": str,          # which walker emitted this
    "cell_id": str,            # which item the receipt is about
    "status": str,             # walker-specific status text
    "timestamp": (int, float), # unix time
    "payload": dict,           # walker-specific extra data
}
```

## The 14-tuple cell schema

The substrate's internal cell representation:

```python
CELL_14_TUPLE = [
    "id", "kind", "payload", "parents", "links", "witnesses", "effects",
    "ticker", "hex", "tag", "meta", "created_at", "updated_at", "author",
]
```

## The 11 opcodes (5 base + 6 adopted)

```python
OPCODES_5 = ["BIND", "LINK", "EFFECT", "VIEW", "TICK"]
OPCODES_6_ADOPTED = ["FORGET", "PROOF", "ROUTE", "CRDT", "WORLD", "TIME"]
```

## The 26 cell kinds

`room`, `vessel`, `perception`, `document`, `decision`, `claim`, `counter`,
`contract`, `seed`, `pecked`, `witness`, `chain`, `graph`, `tree`, `vector`,
`score`, `route`, `program`, `solution`, `fable`, `doctrine`, `epoch`,
`organ`, `tissue`, `organism`, `snapshot`.

## Usage

### Validate a receipt

```python
from quilt_schema_registry import validate_receipt

receipt = {
    "witness_id": "sha256:abc",
    "prev_witness_id": "sha256:def",
    "polarity": "ACCEPT",
    "substrate": "OrganismReceipt",
    "cell_id": "essay.md",
    "status": "canonical",
    "timestamp": 1790234567,
    "payload": {"canon_score": 0.8646},
}

ok, errors = validate_receipt(receipt)  # (True, [])
```

### Validate a chain

```python
from quilt_schema_registry import validate_chain

ok, errors = validate_chain(chain_of_receipts)
```

### Register a new substrate

```python
from quilt_schema_registry import Schema, CANONICAL_FIELDS

Schema.register_substrate(
    "my-walker",
    CANONICAL_FIELDS,
    description="My custom substrate walker",
)
```

### Check field compatibility

```python
from quilt_schema_registry import field_compatibility

compat = field_compatibility(receipt)
# {"compatible": bool, "missing": [...], "extra": [...], "score": float}
```

### Inspect the pre-registered substrates

```python
from quilt_schema_registry import Schema

for name in Schema.substrate_types():
    info = Schema.get(name)
    print(f"{name}: {info['description']} (compliant={info['is_compliant']})")
```

Pre-registered:
- `VibeReceipt` — quilt-seed.vibe cynicism-dial walker
- `CUReceipt` — quilt-seed.cu_substrate CU RAG
- `OptimizationReceipt` — quilt-optimization cuOpt
- `OrganismReceipt` — quilt-organism corpus walker
- `VectorizeReceiver` — vectorize receiver
- `CanonScoreReceiver` — canon-score receiver
- `TraceReceipt` — quilt-trace visualizer output
- `JEVReceipt` — jev-quilt oracle session

## The substrate walker pattern (5th-layer wrapper)

This is the 5th substrate walker in the fleet:

```
vibe / cu_substrate / routing / LP / organism / trace /
snapshot / → schema (this): walks the receipt space, validates the contract
```

The schema walker doesn't have a corpus like `organism`. Its substrate IS
the fleet's receipts. Its receivers are the validation rules. Its output
is the compliance report (a list of receipts + pass/fail per field).

## Cross-fleet validation

Any walker in the fleet can import this registry and validate its receipts
before emitting them. This is how the doctrine stays coherent across:

- Python (quilt-organic, quilt-trace, quilt-optimization, jev-quilt)
- TypeScript (quilt-pincher, dethread, ideator)
- Rust (quilt-spreadsheet-inference ports)
- C/Haskell/Mercury (jev-quilt ports)

## Related

- [quilt-seed](https://github.com/SuperInstance/quilt-seed) — the substrate
- [quilt-trace](https://github.com/SuperInstance/quilt-trace) — the visualizer
- [quilt-organism](https://github.com/SuperInstance/quilt-organism) — the walker
- [quilt-optimization](https://github.com/SuperInstance/quilt-optimization) — cuOpt substrate
- [quilt-fleet-snapshot](https://github.com/SuperInstance/quilt-fleet-snapshot) — fleet state
- [quilt-director](https://github.com/SuperInstance/quilt-director) — the spirals

## License

Apache-2.0
