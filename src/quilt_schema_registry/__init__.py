"""quilt-schema-registry — the canonical 14-tuple schema + envelope contract.

The substrate walker fleet has grown to 8 walkers. Each emits receipts that
chain together. The schema drift is now visible:

- quilt-seed.vibe.CellReceipt has 8 fields
- quilt-organism.OrganismReceipt has 8 fields (mirrored)
- quilt-optimization.OptimizationReceipt has 8 fields
- jev-quilt signed_receipts has different fields
- quilt-trace.AggregateStats uses ad-hoc dicts

quilt-schema-registry is the SINGLE source of truth for:

1. The canonical Witness envelope (witness_id, prev_witness_id, polarity, ...)
2. The 14-tuple cell schema
3. The 26 cell kinds (room, vessel, perception, document, ...)
4. The 11 opcodes (5 base + 6 adopted)
5. Substrate compatibility (which walker emits which fields)
6. Receipt validation (does this receipt comply with the contract?)

Usage:
    from quilt_schema_registry import validate_receipt, CANONICAL_ENVELOPE

    # Validate any receipt against the canonical envelope
    ok, errors = validate_receipt(receipt_dict)
"""
from .registry import (
    Schema,
    CANONICAL_ENVELOPE,
    CANONICAL_FIELDS,
    POLARITY_VALUES,
    RECEIPT_KINDS,
    CELL_14_TUPLE,
    OPCODES_11,
    OPCODES_5,
    OPCODES_6_ADOPTED,
    validate_receipt,
    validate_chain,
    field_compatibility,
)

__version__ = "0.1.0"
__all__ = [
    "Schema",
    "CANONICAL_ENVELOPE",
    "CANONICAL_FIELDS",
    "POLARITY_VALUES",
    "RECEIPT_KINDS",
    "CELL_14_TUPLE",
    "OPCODES_11",
    "OPCODES_5",
    "OPCODES_6_ADOPTED",
    "validate_receipt",
    "validate_chain",
    "field_compatibility",
]
