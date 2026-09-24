"""quilt-schema-registry demo — the substrate walker at the schema layer.

Shows how the registry validates receipts across the fleet, registers
new substrates, and verifies a chain's integrity.

The substrate walker pattern at the 5th layer:
  vibe / cu_substrate / routing / LP / organism / trace / snapshot /
  → schema (this): walks the receipt space, validates the contract
"""
import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from quilt_schema_registry import (
    Schema, validate_receipt, validate_chain, field_compatibility,
    CANONICAL_FIELDS, CANONICAL_ENVELOPE, CELL_14_TUPLE, OPCODES_11,
    RECEIPT_KINDS, POLARITY_VALUES, __version__,
)


def main():
    print("\n" + "=" * 60)
    print(f"🧬 quilt-schema-registry v{__version__}")
    print("=" * 60)

    # Act 1: Inspect the constants
    print(f"\n[Act 1] The canonical schema")
    print(f"  Envelope fields: {len(CANONICAL_FIELDS)} ({', '.join(CANONICAL_FIELDS)})")
    print(f"  Cell 14-tuple: {len(CELL_14_TUPLE)} fields")
    print(f"  Opcodes: {len(OPCODES_11)} ({len(OPCODES_11) - 6} base + 6 adopted)")
    print(f"  Cell kinds: {len(RECEIPT_KINDS)}")
    print(f"  Polarity: {POLARITY_VALUES}")

    # Act 2: List registered substrates
    print(f"\n[Act 2] Pre-registered substrates ({len(Schema.substrate_types())})")
    for name in Schema.substrate_types():
        info = Schema.get(name)
        compliant = "✓" if info["is_compliant"] else " "
        print(f"  [{compliant}] {name:25}  {info['description']}")
    compliant = Schema.compliant()
    print(f"\n  {len(compliant)}/{len(Schema.substrate_types())} are compliant")

    # Act 3: Validate a real receipt (would be from quilt-organism)
    print(f"\n[Act 3] Validate a real-shaped receipt")
    receipt = {
        "witness_id": "sha256:abc123",
        "prev_witness_id": "sha256:def456",
        "polarity": "ACCEPT",
        "substrate": "OrganismReceipt",
        "cell_id": "what-the-mooring-line-holds.md",
        "status": "canonical",
        "timestamp": 1790234567,
        "payload": {"canon_score": 0.8646},
    }
    ok, errors = validate_receipt(receipt)
    print(f"  Receipt: {receipt['cell_id']}")
    print(f"  Polarity: {receipt['polarity']} (score={receipt['payload']['canon_score']})")
    print(f"  Validation: {'PASS' if ok else 'FAIL'}")
    if errors:
        print(f"  Errors: {errors}")

    # Act 4: Show what an invalid receipt looks like
    print(f"\n[Act 4] Show an invalid receipt")
    bad = {
        "witness_id": "x",
        "polarity": "MAYBE",  # invalid
        # missing: prev_witness_id, substrate, cell_id, status, timestamp, payload
    }
    ok, errors = validate_receipt(bad)
    compat = field_compatibility(bad)
    print(f"  Bad receipt: missing {len(compat['missing'])} canonical fields")
    print(f"  Compatibility score: {compat['score']:.0%}")
    print(f"  Polarity OK: {compat['polarity_ok']}")
    print(f"  Errors:")
    for e in errors:
        print(f"    • {e}")

    # Act 5: Validate a chain
    print(f"\n[Act 5] Validate a 5-receipt chain")
    chain = []
    for i in range(5):
        prev = chain[-1]["witness_id"] if chain else ""
        polarity = ["ACCEPT", "DRIFT", "ACCEPT", "REFUSE", "ACCEPT"][i]
        chain.append({
            "witness_id": f"w{i}",
            "prev_witness_id": prev,
            "polarity": polarity,
            "substrate": "OrganismReceipt",
            "cell_id": f"essay-{i}",
            "status": polarity.lower(),
            "timestamp": 1790234567 + i * 100,
            "payload": {"i": i},
        })
    ok, errors = validate_chain(chain)
    print(f"  Chain: {len(chain)} receipts, all link properly")
    print(f"  Validation: {'PASS' if ok else 'FAIL'}")
    if errors:
        for e in errors:
            print(f"    • {e}")

    # Act 6: Register a new substrate
    print(f"\n[Act 6] Register a new substrate: 'quilt-fable'")
    Schema.register_substrate(
        "quilt-fable",
        CANONICAL_FIELDS,
        description="quilt-fable multi-voice narrative substrate",
    )
    print(f"  ✓ Registered. Total substrates: {len(Schema.substrate_types())}")
    print(f"  Compliant: {len(Schema.compliant())}")

    # Summary
    print("\n" + "=" * 60)
    print("✅ Schema registry works: validates receipts, tracks substrates,")
    print("   ensures the canonical envelope is honored across the fleet.")
    print("=" * 60)


if __name__ == "__main__":
    main()
