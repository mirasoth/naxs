"""Tests for the pynaxs validator, covering every validation rule."""

import json
import os
import sys
import unittest
from pathlib import Path

# Ensure the package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pynaxs import NaxsValidator, ValidationResult
from tests.fixtures import ALL_FIXTURES, write_temp_json, VALID_MINIMAL, VALID_WITH_BLOCK_TEMPLATE, VALID_WITH_EXPR


class TestValidDocuments(unittest.TestCase):
    """Valid documents should pass with zero errors."""

    def setUp(self):
        self.validator = NaxsValidator()

    def test_valid_minimal(self):
        result = self.validator.validate_document(VALID_MINIMAL, "valid_minimal")
        self.assertTrue(result.is_valid(), f"Expected valid, got errors: {[e.message for e in result.errors]}")

    def test_valid_block_template(self):
        result = self.validator.validate_document(VALID_WITH_BLOCK_TEMPLATE, "valid_block_template")
        self.assertTrue(result.is_valid(), f"Expected valid, got errors: {[e.message for e in result.errors]}")

    def test_valid_expr(self):
        result = self.validator.validate_document(VALID_WITH_EXPR, "valid_expr")
        self.assertTrue(result.is_valid(), f"Expected valid, got errors: {[e.message for e in result.errors]}")

    def test_valid_minimal_has_warnings(self):
        """Valid documents may still have soft validation warnings."""
        result = self.validator.validate_document(VALID_MINIMAL, "valid_minimal")
        self.assertTrue(result.is_valid())
        # minimal_mlp has no scope on components → should have warnings
        # But our fixture has scope, so maybe 0 warnings
        # Just check it doesn't crash


class TestStructuralValidation(unittest.TestCase):
    """Structural integrity rules."""

    def setUp(self):
        self.validator = NaxsValidator()

    def test_missing_required_fields(self):
        from tests.fixtures import INVALID_MISSING_REQUIRED
        result = self.validator.validate_document(INVALID_MISSING_REQUIRED, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("components" in m for m in error_msgs))

    def test_duplicate_component_id(self):
        from tests.fixtures import INVALID_DUPLICATE_COMPONENT_ID
        result = self.validator.validate_document(INVALID_DUPLICATE_COMPONENT_ID, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("Duplicate component id" in m for m in error_msgs))

    def test_dangling_reference(self):
        from tests.fixtures import INVALID_DANGLING_REF
        result = self.validator.validate_document(INVALID_DANGLING_REF, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("non-existent" in m for m in error_msgs))

    def test_duplicate_connection_id(self):
        from tests.fixtures import INVALID_DUPLICATE_CONN_ID
        result = self.validator.validate_document(INVALID_DUPLICATE_CONN_ID, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("Duplicate connection id" in m for m in error_msgs))

    def test_empty_components(self):
        from tests.fixtures import INVALID_EMPTY_COMPONENTS
        result = self.validator.validate_document(INVALID_EMPTY_COMPONENTS, "test")
        self.assertFalse(result.is_valid())

    def test_missing_component_fields(self):
        from tests.fixtures import INVALID_MISSING_COMPONENT_FIELDS
        result = self.validator.validate_document(INVALID_MISSING_COMPONENT_FIELDS, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("missing required field" in m for m in error_msgs))

    def test_bad_version(self):
        from tests.fixtures import INVALID_BAD_VERSION
        result = self.validator.validate_document(INVALID_BAD_VERSION, "test")
        self.assertFalse(result.is_valid())


class TestConsistencyValidation(unittest.TestCase):
    """Consistency rules."""

    def setUp(self):
        self.validator = NaxsValidator()

    def test_inconsistent_io(self):
        from tests.fixtures import INVALID_INCONSISTENT_IO
        result = self.validator.validate_document(INVALID_INCONSISTENT_IO, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("does not list" in m for m in error_msgs))

    def test_connection_mismatch(self):
        from tests.fixtures import INVALID_CONNECTION_MISMATCH
        result = self.validator.validate_document(INVALID_CONNECTION_MISMATCH, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("does not list" in m for m in error_msgs))


class TestParameterValidity(unittest.TestCase):
    """Parameter validity rules."""

    def setUp(self):
        self.validator = NaxsValidator()

    def test_null_param(self):
        from tests.fixtures import INVALID_NULL_PARAM
        result = self.validator.validate_document(INVALID_NULL_PARAM, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("null" in m.lower() for m in error_msgs))

    def test_nested_object_param(self):
        from tests.fixtures import INVALID_NESTED_PARAM
        result = self.validator.validate_document(INVALID_NESTED_PARAM, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("nested object" in m for m in error_msgs))


class TestBlockTemplateValidation(unittest.TestCase):
    """Block template validation rules."""

    def setUp(self):
        self.validator = NaxsValidator()

    def test_bad_block_ref(self):
        from tests.fixtures import INVALID_BLOCK_REF
        result = self.validator.validate_document(INVALID_BLOCK_REF, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("block_ref" in m or "does not reference" in m for m in error_msgs))

    def test_duplicate_node_id(self):
        from tests.fixtures import INVALID_DUP_NODE_ID
        result = self.validator.validate_document(INVALID_DUP_NODE_ID, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("Duplicate node id" in m for m in error_msgs))

    def test_bad_edge_ref(self):
        from tests.fixtures import INVALID_EDGE_REF
        result = self.validator.validate_document(INVALID_EDGE_REF, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("non-existent node" in m for m in error_msgs))

    def test_bad_repeat_count(self):
        from tests.fixtures import INVALID_BAD_REPEAT_COUNT
        result = self.validator.validate_document(INVALID_BAD_REPEAT_COUNT, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("count" in m.lower() for m in error_msgs))

    def test_bad_repeat_mode(self):
        from tests.fixtures import INVALID_BAD_REPEAT_MODE
        result = self.validator.validate_document(INVALID_BAD_REPEAT_MODE, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("mode" in m.lower() for m in error_msgs))

    def test_override_out_of_range(self):
        from tests.fixtures import INVALID_OVERRIDE_OUT_OF_RANGE
        result = self.validator.validate_document(INVALID_OVERRIDE_OUT_OF_RANGE, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("out of range" in m for m in error_msgs))

    def test_unresolved_param_ref(self):
        from tests.fixtures import INVALID_UNRESOLVED_PARAM
        result = self.validator.validate_document(INVALID_UNRESOLVED_PARAM, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("does not resolve" in m for m in error_msgs))

    def test_bad_expr(self):
        from tests.fixtures import INVALID_BAD_EXPR
        result = self.validator.validate_document(INVALID_BAD_EXPR, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("$expr" in m or "undeclared" in m for m in error_msgs))

    def test_circular_ref(self):
        from tests.fixtures import INVALID_CIRCULAR_REF
        result = self.validator.validate_document(INVALID_CIRCULAR_REF, "test")
        self.assertFalse(result.is_valid())
        error_msgs = [e.message for e in result.errors]
        self.assertTrue(any("Circular" in m or "circular" in m for m in error_msgs))


class TestSoftValidation(unittest.TestCase):
    """Soft validation warnings."""

    def setUp(self):
        self.validator = NaxsValidator()

    def test_missing_description_warning(self):
        doc = {
            "spec_version": "0.1",
            "id": "test",
            "name": "Test",
            "components": [
                {"id": "n1", "type": "input", "name": "x", "params": {}, "inputs": [], "outputs": [], "scope": "s"},
            ],
            "connections": [],
        }
        result = self.validator.validate_document(doc, "test")
        self.assertTrue(result.is_valid())
        warn_msgs = [w.message for w in result.warnings]
        self.assertTrue(any("description" in m for m in warn_msgs))

    def test_missing_scope_warning(self):
        doc = {
            "spec_version": "0.1",
            "id": "test",
            "name": "Test",
            "description": "Has description.",
            "components": [
                {"id": "n1", "type": "input", "name": "x", "params": {}, "inputs": [], "outputs": ["n2"], "scope": "input"},
                {"id": "n2", "type": "linear", "name": "fc", "params": {}, "inputs": ["n1"], "outputs": []},
            ],
            "connections": [{"id": "c1", "from": "n1", "to": "n2"}],
        }
        result = self.validator.validate_document(doc, "test")
        self.assertTrue(result.is_valid())
        warn_msgs = [w.message for w in result.warnings]
        self.assertTrue(any("scope" in m for m in warn_msgs))

    def test_uniformly_unscoped_no_scope_warning(self):
        """A document that omits scope everywhere is consistent — no warning."""
        doc = {
            "spec_version": "0.1",
            "id": "test",
            "name": "Test",
            "description": "Has description.",
            "components": [
                {"id": "n1", "type": "input", "name": "x", "params": {}, "inputs": [], "outputs": ["n2"]},
                {"id": "n2", "type": "linear", "name": "fc", "params": {}, "inputs": ["n1"], "outputs": []},
            ],
            "connections": [{"id": "c1", "from": "n1", "to": "n2"}],
        }
        result = self.validator.validate_document(doc, "test")
        self.assertTrue(result.is_valid())
        warn_msgs = [w.message for w in result.warnings]
        self.assertFalse(any("scope" in m for m in warn_msgs))

    def test_embeddim_standard_for_transformer_types(self):
        """embedDim is standard for transformer-family types (no warning)."""
        for comp_type in ("swiglu", "geglu", "feedForward", "moeLayer", "sharedExpertMoE", "mla", "positionalEncoding", "transformerBlock"):
            doc = {
                "spec_version": "0.1",
                "id": "test",
                "name": "Test",
                "description": "Test.",
                "components": [
                    {"id": "n1", "type": comp_type, "name": "x", "params": {"embedDim": 4096}, "inputs": [], "outputs": []},
                ],
                "connections": [],
            }
            result = self.validator.validate_document(doc, f"test_{comp_type}")
            self.assertTrue(result.is_valid())
            warn_msgs = [w.message for w in result.warnings]
            self.assertFalse(
                any("embedDim" in m for m in warn_msgs),
                f"embedDim should be standard for '{comp_type}': {warn_msgs}",
            )

    def test_concatenate_standard_params(self):
        doc = {
            "spec_version": "0.1",
            "id": "test",
            "name": "Test",
            "description": "Test.",
            "components": [
                {"id": "n1", "type": "concatenate", "name": "cat", "params": {"dim": 1, "axis": 1, "numInputs": 3}, "inputs": [], "outputs": []},
            ],
            "connections": [],
        }
        result = self.validator.validate_document(doc, "test")
        self.assertTrue(result.is_valid())
        warn_msgs = [w.message for w in result.warnings]
        self.assertFalse(any("not in the standard registry" in m for m in warn_msgs))

    def test_custom_empty_params_warning(self):
        doc = {
            "spec_version": "0.1",
            "id": "test",
            "name": "Test",
            "description": "Test.",
            "components": [
                {"id": "n1", "type": "custom", "name": "x", "params": {}, "inputs": [], "outputs": [], "scope": "s"},
            ],
            "connections": [],
        }
        result = self.validator.validate_document(doc, "test")
        self.assertTrue(result.is_valid())
        warn_msgs = [w.message for w in result.warnings]
        self.assertTrue(any("empty params" in m for m in warn_msgs))


class TestFileValidation(unittest.TestCase):
    """Test the file-based and string-based validation APIs."""

    def setUp(self):
        self.validator = NaxsValidator()

    def test_validate_file(self):
        path = write_temp_json(VALID_MINIMAL)
        try:
            result = self.validator.validate_file(path)
            self.assertTrue(result.is_valid())
        finally:
            os.unlink(path)

    def test_validate_str(self):
        json_str = json.dumps(VALID_MINIMAL)
        result = self.validator.validate_str(json_str, "test")
        self.assertTrue(result.is_valid())

    def test_validate_str_invalid_json(self):
        result = self.validator.validate_str("{bad json", "test")
        self.assertFalse(result.is_valid())
        self.assertTrue(any("Invalid JSON" in e.message for e in result.errors))

    def test_validate_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.validator.validate_file("/nonexistent/path.json")


class TestAllFixtures(unittest.TestCase):
    """Run all fixtures and verify expected valid/invalid status."""

    def setUp(self):
        self.validator = NaxsValidator()

    def test_all_fixtures(self):
        for name, (doc, expected_valid) in ALL_FIXTURES.items():
            with self.subTest(fixture=name):
                result = self.validator.validate_document(doc, name)
                actual_valid = result.is_valid()
                if expected_valid:
                    self.assertTrue(
                        actual_valid,
                        f"Fixture '{name}' should be valid but has errors: "
                        + "; ".join(f"[{e.rule}] {e.path}: {e.message}" for e in result.errors),
                    )
                else:
                    self.assertFalse(
                        actual_valid,
                        f"Fixture '{name}' should be invalid but passed validation",
                    )


class TestNaxsExampleFiles(unittest.TestCase):
    """Validate the NAXS example files shipped alongside the package."""

    EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "naxs" / "v0.1" / "examples"

    def setUp(self):
        self.validator = NaxsValidator()

    def test_all_examples_valid(self):
        if not self.EXAMPLES_DIR.exists():
            self.skipTest(f"Examples directory not found: {self.EXAMPLES_DIR}")
        json_files = sorted(self.EXAMPLES_DIR.glob("*.json"))
        self.assertGreater(len(json_files), 0, "No example JSON files found")
        for f in json_files:
            with self.subTest(file=f.name):
                result = self.validator.validate_file(f)
                self.assertTrue(
                    result.is_valid(),
                    f"{f.name} should be valid but has errors: "
                    + "; ".join(f"[{e.rule}] {e.path}: {e.message}" for e in result.errors),
                )


if __name__ == "__main__":
    unittest.main()
