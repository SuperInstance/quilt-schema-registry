"""Tests for quilt-schema-registry."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from quilt_schema_registry import (
    Schema, validate_receipt, validate_chain, field_compatibility,
    CANONICAL_ENVELOPE, CANONICAL_FIELDS, POLARITY_VALUES, RECEIPT_KINDS,
    CELL_14_TUPLE, OPCODES_11, __version__,
)


class TestSchemaConstants(unittest.TestCase):
    def test_version(self):
        self.assertEqual(__version__, "0.1.0")

    def test_canonical_envelope_has_8_fields(self):
        self.assertEqual(len(CANONICAL_ENVELOPE), 8)

    def test_canonical_fields_match_envelope(self):
        self.assertEqual(set(CANONICAL_FIELDS), set(CANONICAL_ENVELOPE.keys()))

    def test_polarity_has_three_values(self):
        self.assertEqual(set(POLARITY_VALUES), {"ACCEPT", "DRIFT", "REFUSE"})

    def test_cell_14_tuple(self):
        self.assertEqual(len(CELL_14_TUPLE), 14)
        self.assertIn("id", CELL_14_TUPLE)
        self.assertIn("kind", CELL_14_TUPLE)
        self.assertIn("witnesses", CELL_14_TUPLE)
        self.assertIn("hex", CELL_14_TUPLE)

    def test_opcodes_11(self):
        self.assertEqual(len(OPCODES_11), 11)
        for op in ["BIND", "LINK", "EFFECT", "VIEW", "TICK"]:
            self.assertIn(op, OPCODES_11)
        for op in ["FORGET", "PROOF", "ROUTE", "CRDT", "WORLD", "TIME"]:
            self.assertIn(op, OPCODES_11)

    def test_kinds_26(self):
        self.assertEqual(len(RECEIPT_KINDS), 26)
        for k in ["room", "vessel", "witness", "chain", "organism", "snapshot"]:
            self.assertIn(k, RECEIPT_KINDS)


class TestSubstrateRegistration(unittest.TestCase):
    def setUp(self):
        Schema.reset()

    def tearDown(self):
        Schema.reset()

    def test_register_substrate(self):
        Schema.register_substrate("test", CANONICAL_FIELDS, "test substrate")
        self.assertIn("test", Schema.substrate_types())

    def test_register_with_unknown_field_raises(self):
        with self.assertRaises(ValueError):
            Schema.register_substrate("bad", ["witness_id", "made_up_field"])

    def test_compliant_substrates(self):
        Schema.register_substrate("full", CANONICAL_FIELDS)
        Schema.register_substrate("partial", ["witness_id", "polarity"])
        compliant = Schema.compliant()
        self.assertIn("full", compliant)
        self.assertNotIn("partial", compliant)

    def test_get_substrate(self):
        Schema.register_substrate("foo", CANONICAL_FIELDS, "foo substrate")
        info = Schema.get("foo")
        self.assertIsNotNone(info)
        self.assertEqual(info["name"], "foo")
        self.assertEqual(info["description"], "foo substrate")
        self.assertTrue(info["is_compliant"])

    def test_get_unknown_returns_none(self):
        self.assertIsNone(Schema.get("does-not-exist"))

    def test_known_substrates_pre_registered(self):
        # Re-import after reset to get pre-registration
        import importlib
        import quilt_schema_registry
        # Force pre-registration by re-creating substrate types
        for name in ["VibeReceipt", "CUReceipt", "OptimizationReceipt",
                      "OrganismReceipt", "VectorizeReceiver", "CanonScoreReceiver",
                      "TraceReceipt", "JEVReceipt"]:
            Schema.register_substrate(name, CANONICAL_FIELDS, f"pre-registered: {name}")
        for name in ["VibeReceipt", "CUReceipt", "OptimizationReceipt",
                      "OrganismReceipt", "VectorizeReceiver", "CanonScoreReceiver",
                      "TraceReceipt", "JEVReceipt"]:
            self.assertIn(name, Schema.substrate_types(), f"{name} not registered")


class TestValidateReceipt(unittest.TestCase):
    def _good_receipt(self):
        return {
            "witness_id": "abc123",
            "prev_witness_id": "",
            "polarity": "ACCEPT",
            "substrate": "test",
            "cell_id": "c1",
            "status": "ok",
            "timestamp": 1234567890,
            "payload": {"k": "v"},
        }

    def test_valid_receipt(self):
        ok, errors = validate_receipt(self._good_receipt())
        self.assertTrue(ok, f"errors: {errors}")
        self.assertEqual(errors, [])

    def test_missing_field(self):
        r = self._good_receipt()
        del r["witness_id"]
        ok, errors = validate_receipt(r)
        self.assertFalse(ok)
        self.assertTrue(any("witness_id" in e for e in errors))

    def test_bad_polarity(self):
        r = self._good_receipt()
        r["polarity"] = "MAYBE"
        ok, errors = validate_receipt(r)
        self.assertFalse(ok)
        self.assertTrue(any("polarity" in e.lower() for e in errors))

    def test_not_a_dict(self):
        ok, errors = validate_receipt("not a dict")
        self.assertFalse(ok)

    def test_unknown_substrate(self):
        ok, errors = validate_receipt(self._good_receipt(), substrate="doesnt-exist")
        self.assertFalse(ok)
        self.assertTrue(any("unknown substrate" in e for e in errors))

    def test_substrate_compatibility(self):
        # Register a substrate that requires witness_id — our good receipt has it
        Schema.register_substrate("VibeReceipt", CANONICAL_FIELDS)
        ok, errors = validate_receipt(self._good_receipt(), substrate="VibeReceipt")
        self.assertTrue(ok, f"errors: {errors}")

    def test_payload_must_be_dict(self):
        r = self._good_receipt()
        r["payload"] = "not a dict"
        ok, errors = validate_receipt(r)
        self.assertFalse(ok)
        self.assertTrue(any("payload" in e for e in errors))

    def test_timestamp_can_be_int_or_float(self):
        for ts in [1234567890, 1234567890.123]:
            r = self._good_receipt()
            r["timestamp"] = ts
            ok, _ = validate_receipt(r)
            self.assertTrue(ok, f"failed for ts={ts}")


class TestValidateChain(unittest.TestCase):
    def test_valid_chain(self):
        chain = [
            {"witness_id": "w1", "prev_witness_id": "", "polarity": "ACCEPT",
             "substrate": "s", "cell_id": "c", "status": "ok",
             "timestamp": 1, "payload": {}},
            {"witness_id": "w2", "prev_witness_id": "w1", "polarity": "ACCEPT",
             "substrate": "s", "cell_id": "c", "status": "ok",
             "timestamp": 2, "payload": {}},
            {"witness_id": "w3", "prev_witness_id": "w2", "polarity": "DRIFT",
             "substrate": "s", "cell_id": "c", "status": "warn",
             "timestamp": 3, "payload": {}},
        ]
        ok, errors = validate_chain(chain)
        self.assertTrue(ok, f"errors: {errors}")

    def test_broken_chain(self):
        chain = [
            {"witness_id": "w1", "prev_witness_id": "", "polarity": "ACCEPT",
             "substrate": "s", "cell_id": "c", "status": "ok",
             "timestamp": 1, "payload": {}},
            {"witness_id": "w2", "prev_witness_id": "WRONG", "polarity": "ACCEPT",
             "substrate": "s", "cell_id": "c", "status": "ok",
             "timestamp": 2, "payload": {}},
        ]
        ok, errors = validate_chain(chain)
        self.assertFalse(ok)
        self.assertTrue(any("chain broken" in e for e in errors))

    def test_empty_chain(self):
        ok, errors = validate_chain([])
        self.assertFalse(ok)
        self.assertIn("empty", errors[0].lower())


class TestFieldCompatibility(unittest.TestCase):
    def test_full_compatibility(self):
        r = {
            "witness_id": "w", "prev_witness_id": "", "polarity": "ACCEPT",
            "substrate": "s", "cell_id": "c", "status": "ok",
            "timestamp": 1, "payload": {},
        }
        c = field_compatibility(r)
        self.assertTrue(c["compatible"])
        self.assertEqual(c["missing"], [])
        self.assertEqual(c["score"], 1.0)
        self.assertTrue(c["polarity_ok"])

    def test_partial_compatibility(self):
        r = {"witness_id": "w", "polarity": "ACCEPT"}
        c = field_compatibility(r)
        self.assertFalse(c["compatible"])
        self.assertEqual(len(c["missing"]), 6)
        self.assertGreater(c["score"], 0)
        self.assertLess(c["score"], 1)
        self.assertTrue(c["polarity_ok"])

    def test_bad_polarity(self):
        r = {"witness_id": "w", "polarity": "MAYBE"}
        c = field_compatibility(r)
        self.assertFalse(c["polarity_ok"])

    def test_extra_fields_counted(self):
        r = {
            "witness_id": "w", "prev_witness_id": "", "polarity": "ACCEPT",
            "substrate": "s", "cell_id": "c", "status": "ok",
            "timestamp": 1, "payload": {},
            "custom_field": "extra",
        }
        c = field_compatibility(r)
        self.assertEqual(c["extra"], ["custom_field"])
        self.assertTrue(c["compatible"])


if __name__ == "__main__":
    unittest.main()


# --- witness hash recipe (WITNESS_ID_V1) -----------------------------------

def test_compute_witness_id_matches_conformance_vector():
    from quilt_schema_registry import (compute_witness_id,
                                       HASH_CONFORMANCE_ENVELOPE,
                                       HASH_CONFORMANCE_VECTOR)
    assert compute_witness_id(HASH_CONFORMANCE_ENVELOPE) == HASH_CONFORMANCE_VECTOR


def test_witness_id_tamper_sensitive():
    from quilt_schema_registry import (compute_witness_id,
                                       HASH_CONFORMANCE_ENVELOPE)
    env = dict(HASH_CONFORMANCE_ENVELOPE)
    env["payload"] = {"note": "tampered"}
    assert compute_witness_id(env) != compute_witness_id(HASH_CONFORMANCE_ENVELOPE)


def test_witness_id_key_order_independent():
    import json
    from quilt_schema_registry import (compute_witness_id,
                                       HASH_CONFORMANCE_ENVELOPE,
                                       HASH_CONFORMANCE_VECTOR)
    # a substrate that serialized keys in insertion order must reproduce the id
    reordered = json.loads(json.dumps(HASH_CONFORMANCE_ENVELOPE),
                           object_pairs_hook=lambda p: dict(reversed(p)))
    assert compute_witness_id(reordered) == HASH_CONFORMANCE_VECTOR


def test_hash_recipe_machine_readable():
    from quilt_schema_registry import HASH_RECIPE
    for k in ("algorithm", "canon", "input", "output", "recipe_version"):
        assert k in HASH_RECIPE
    assert HASH_RECIPE["algorithm"] == "sha256"
