"""Test fixtures: valid and invalid NAXS documents for testing each validation rule."""

import json
import tempfile
from pathlib import Path


# ─── Valid documents ──────────────────────────────────────────────────────────

VALID_MINIMAL = {
    "spec_version": "1.0",
    "id": "test-mlp",
    "name": "Test MLP",
    "description": "A minimal valid document for testing.",
    "components": [
        {
            "id": "n1",
            "type": "input",
            "name": "x",
            "params": {"shape": [10]},
            "inputs": [],
            "outputs": ["n2"],
            "scope": "input",
        },
        {
            "id": "n2",
            "type": "linear",
            "name": "fc1",
            "params": {"inFeatures": 10, "outFeatures": 5},
            "inputs": ["n1"],
            "outputs": [],
            "scope": "layer.0",
        },
    ],
    "connections": [
        {"id": "c1", "from": "n1", "to": "n2"}
    ],
}

VALID_WITH_BLOCK_TEMPLATE = {
    "spec_version": "1.0",
    "id": "test-block",
    "name": "Test Block Arch",
    "description": "Architecture using block templates and repetition.",
    "block_templates": [
        {
            "id": "encoder_layer",
            "description": "A transformer encoder layer",
            "params": {
                "hiddenDim": {"type": "integer", "description": "Hidden dim"},
                "numHeads": {"type": "integer", "description": "Number of heads"},
            },
            "nodes": [
                {
                    "id": "attn",
                    "type": "multiHeadAttention",
                    "name": "Attention",
                    "params": {
                        "numHeads": "$numHeads",
                        "hiddenDim": "$hiddenDim",
                    },
                },
                {
                    "id": "ln",
                    "type": "layerNorm",
                    "name": "LayerNorm",
                    "params": {"normalizedShape": "$hiddenDim"},
                },
            ],
            "edges": [
                {"from": "attn", "to": "ln"},
            ],
            "interface": {
                "inputs": [{"name": "x"}],
                "outputs": [{"name": "y", "source_node": "ln"}],
            },
        }
    ],
    "components": [
        {
            "id": "input1",
            "type": "input",
            "name": "Input",
            "params": {"shape": [128]},
            "inputs": [],
            "outputs": ["layers"],
            "scope": "input",
        },
        {
            "id": "layers",
            "type": "block",
            "name": "Layers",
            "block_ref": "encoder_layer",
            "params": {"hiddenDim": 128, "numHeads": 8},
            "inputs": ["input1"],
            "outputs": ["output1"],
            "scope": "encoder",
            "repeat": {"count": 4, "mode": "sequential"},
        },
        {
            "id": "output1",
            "type": "output",
            "name": "Output",
            "params": {"shape": [128]},
            "inputs": ["layers"],
            "outputs": [],
            "scope": "output",
        },
    ],
    "connections": [
        {"id": "c1", "from": "input1", "to": "layers"},
        {"id": "c2", "from": "layers", "to": "output1"},
    ],
}

VALID_WITH_EXPR = {
    "spec_version": "1.0",
    "id": "test-expr",
    "name": "Test Expr",
    "description": "Architecture using $expr parameter derivation.",
    "block_templates": [
        {
            "id": "ffn_block",
            "params": {
                "hiddenDim": {"type": "integer", "description": "Hidden dim"},
                "numHeads": {"type": "integer", "description": "Heads"},
            },
            "nodes": [
                {
                    "id": "ffn",
                    "type": "feedForward",
                    "name": "FFN",
                    "params": {
                        "hiddenDim": "$hiddenDim",
                        "ffDim": {"$expr": "hiddenDim * 4"},
                        "headDim": {"$expr": "hiddenDim / numHeads"},
                    },
                },
            ],
            "edges": [],
            "interface": {
                "inputs": [{"name": "x"}],
                "outputs": [{"name": "y", "source_node": "ffn"}],
            },
        }
    ],
    "components": [
        {
            "id": "n1",
            "type": "input",
            "name": "x",
            "params": {"shape": [256]},
            "inputs": [],
            "outputs": ["n2"],
            "scope": "input",
        },
        {
            "id": "n2",
            "type": "block",
            "name": "FFN",
            "block_ref": "ffn_block",
            "params": {"hiddenDim": 256, "numHeads": 8},
            "inputs": ["n1"],
            "outputs": [],
            "scope": "ffn",
        },
    ],
    "connections": [
        {"id": "c1", "from": "n1", "to": "n2"},
    ],
}


# ─── Invalid documents (one per rule) ─────────────────────────────────────────

INVALID_MISSING_REQUIRED = {
    "spec_version": "1.0",
    "id": "bad-missing",
    "name": "Missing Required Fields",
    # Missing: components, connections
}

INVALID_DUPLICATE_COMPONENT_ID = {
    "spec_version": "1.0",
    "id": "bad-dup-id",
    "name": "Duplicate IDs",
    "description": "Two components with the same id.",
    "components": [
        {"id": "n1", "type": "input", "name": "a", "params": {}, "inputs": [], "outputs": []},
        {"id": "n1", "type": "input", "name": "b", "params": {}, "inputs": [], "outputs": []},
    ],
    "connections": [],
}

INVALID_DANGLING_REF = {
    "spec_version": "1.0",
    "id": "bad-dangling",
    "name": "Dangling Reference",
    "description": "Component references non-existent id.",
    "components": [
        {"id": "n1", "type": "input", "name": "a", "params": {}, "inputs": [], "outputs": ["n2"]},
    ],
    "connections": [],
}

INVALID_INCONSISTENT_IO = {
    "spec_version": "1.0",
    "id": "bad-inconsistent",
    "name": "Inconsistent IO",
    "description": "A lists B in outputs but B doesn't list A in inputs.",
    "components": [
        {"id": "n1", "type": "input", "name": "a", "params": {}, "inputs": [], "outputs": ["n2"]},
        {"id": "n2", "type": "linear", "name": "b", "params": {}, "inputs": [], "outputs": []},
    ],
    "connections": [],
}

INVALID_CONNECTION_MISMATCH = {
    "spec_version": "1.0",
    "id": "bad-conn",
    "name": "Connection Mismatch",
    "description": "Connection from A to B but A doesn't list B in outputs.",
    "components": [
        {"id": "n1", "type": "input", "name": "a", "params": {}, "inputs": [], "outputs": []},
        {"id": "n2", "type": "linear", "name": "b", "params": {}, "inputs": ["n1"], "outputs": []},
    ],
    "connections": [
        {"id": "c1", "from": "n1", "to": "n2"},
    ],
}

INVALID_NULL_PARAM = {
    "spec_version": "1.0",
    "id": "bad-null-param",
    "name": "Null Param",
    "description": "Parameter value is null.",
    "components": [
        {"id": "n1", "type": "input", "name": "a", "params": {"shape": None}, "inputs": [], "outputs": []},
    ],
    "connections": [],
}

INVALID_NESTED_PARAM = {
    "spec_version": "1.0",
    "id": "bad-nested-param",
    "name": "Nested Object Param",
    "description": "Parameter value is a nested object.",
    "components": [
        {"id": "n1", "type": "custom", "name": "a", "params": {"bad": {"nested": "obj"}}, "inputs": [], "outputs": []},
    ],
    "connections": [],
}

INVALID_DUPLICATE_CONN_ID = {
    "spec_version": "1.0",
    "id": "bad-dup-conn",
    "name": "Duplicate Connection ID",
    "description": "Two connections with the same id.",
    "components": [
        {"id": "n1", "type": "input", "name": "a", "params": {}, "inputs": [], "outputs": ["n2"]},
        {"id": "n2", "type": "linear", "name": "b", "params": {}, "inputs": ["n1"], "outputs": []},
    ],
    "connections": [
        {"id": "c1", "from": "n1", "to": "n2"},
        {"id": "c1", "from": "n1", "to": "n2"},
    ],
}

INVALID_BLOCK_REF = {
    "spec_version": "1.0",
    "id": "bad-block-ref",
    "name": "Bad Block Ref",
    "description": "block_ref references non-existent template.",
    "block_templates": [],
    "components": [
        {
            "id": "n1", "type": "block", "name": "layer",
            "block_ref": "nonexistent_template",
            "params": {}, "inputs": [], "outputs": [],
        },
    ],
    "connections": [],
}

INVALID_DUP_NODE_ID = {
    "spec_version": "1.0",
    "id": "bad-dup-node",
    "name": "Duplicate Node ID in Template",
    "description": "Two nodes with same id in a template.",
    "block_templates": [
        {
            "id": "t1",
            "params": {},
            "nodes": [
                {"id": "a", "type": "linear", "name": "a"},
                {"id": "a", "type": "linear", "name": "b"},
            ],
            "edges": [],
        }
    ],
    "components": [
        {"id": "n1", "type": "input", "name": "x", "params": {}, "inputs": [], "outputs": []},
    ],
    "connections": [],
}

INVALID_EDGE_REF = {
    "spec_version": "1.0",
    "id": "bad-edge-ref",
    "name": "Bad Edge Ref",
    "description": "Edge references non-existent node.",
    "block_templates": [
        {
            "id": "t1",
            "params": {},
            "nodes": [
                {"id": "a", "type": "linear", "name": "a"},
            ],
            "edges": [
                {"from": "a", "to": "nonexistent"},
            ],
        }
    ],
    "components": [
        {"id": "n1", "type": "input", "name": "x", "params": {}, "inputs": [], "outputs": []},
    ],
    "connections": [],
}

INVALID_BAD_REPEAT_COUNT = {
    "spec_version": "1.0",
    "id": "bad-repeat",
    "name": "Bad Repeat Count",
    "description": "repeat.count is 0.",
    "block_templates": [
        {
            "id": "t1",
            "params": {},
            "nodes": [{"id": "a", "type": "linear", "name": "a"}],
            "edges": [],
        }
    ],
    "components": [
        {
            "id": "n1", "type": "block", "name": "layer",
            "block_ref": "t1", "params": {},
            "inputs": [], "outputs": [],
            "repeat": {"count": 0, "mode": "sequential"},
        },
    ],
    "connections": [],
}

INVALID_BAD_REPEAT_MODE = {
    "spec_version": "1.0",
    "id": "bad-repeat-mode",
    "name": "Bad Repeat Mode",
    "description": "repeat.mode is invalid.",
    "block_templates": [
        {
            "id": "t1",
            "params": {},
            "nodes": [{"id": "a", "type": "linear", "name": "a"}],
            "edges": [],
        }
    ],
    "components": [
        {
            "id": "n1", "type": "block", "name": "layer",
            "block_ref": "t1", "params": {},
            "inputs": [], "outputs": [],
            "repeat": {"count": 3, "mode": "invalid_mode"},
        },
    ],
    "connections": [],
}

INVALID_OVERRIDE_OUT_OF_RANGE = {
    "spec_version": "1.0",
    "id": "bad-override",
    "name": "Override Out of Range",
    "description": "Override index exceeds count.",
    "block_templates": [
        {
            "id": "t1",
            "params": {"d": {"type": "integer", "description": "d"}},
            "nodes": [{"id": "a", "type": "linear", "name": "a", "params": {"inFeatures": "$d"}}],
            "edges": [],
        }
    ],
    "components": [
        {
            "id": "n1", "type": "block", "name": "layer",
            "block_ref": "t1", "params": {"d": 10},
            "inputs": [], "outputs": [],
            "repeat": {"count": 2, "mode": "sequential", "overrides": [
                {"index": 5, "params": {"d": 20}},
            ]},
        },
    ],
    "connections": [],
}

INVALID_UNRESOLVED_PARAM = {
    "spec_version": "1.0",
    "id": "bad-unresolved-param",
    "name": "Unresolved Param Ref",
    "description": "$-reference doesn't resolve to declared param.",
    "block_templates": [
        {
            "id": "t1",
            "params": {"d": {"type": "integer", "description": "d"}},
            "nodes": [
                {"id": "a", "type": "linear", "name": "a", "params": {"inFeatures": "$undeclared"}},
            ],
            "edges": [],
        }
    ],
    "components": [
        {"id": "n1", "type": "input", "name": "x", "params": {}, "inputs": [], "outputs": []},
    ],
    "connections": [],
}

INVALID_BAD_EXPR = {
    "spec_version": "1.0",
    "id": "bad-expr",
    "name": "Bad Expression",
    "description": "$expr references undeclared parameter.",
    "block_templates": [
        {
            "id": "t1",
            "params": {"d": {"type": "integer", "description": "d"}},
            "nodes": [
                {"id": "a", "type": "linear", "name": "a",
                 "params": {"outFeatures": {"$expr": "d * undeclared"}}},
            ],
            "edges": [],
        }
    ],
    "components": [
        {"id": "n1", "type": "input", "name": "x", "params": {}, "inputs": [], "outputs": []},
    ],
    "connections": [],
}

INVALID_CIRCULAR_REF = {
    "spec_version": "1.0",
    "id": "bad-circular",
    "name": "Circular Block Ref",
    "description": "Template A references B which references A.",
    "block_templates": [
        {
            "id": "t1",
            "params": {},
            "nodes": [
                {"id": "a", "type": "block", "name": "a", "block_ref": "t2"},
            ],
            "edges": [],
        },
        {
            "id": "t2",
            "params": {},
            "nodes": [
                {"id": "b", "type": "block", "name": "b", "block_ref": "t1"},
            ],
            "edges": [],
        },
    ],
    "components": [
        {"id": "n1", "type": "input", "name": "x", "params": {}, "inputs": [], "outputs": []},
    ],
    "connections": [],
}

INVALID_BAD_VERSION = {
    "spec_version": "2.0",
    "id": "bad-version",
    "name": "Bad Version",
    "description": "Wrong spec_version.",
    "components": [
        {"id": "n1", "type": "input", "name": "x", "params": {}, "inputs": [], "outputs": []},
    ],
    "connections": [],
}

INVALID_EMPTY_COMPONENTS = {
    "spec_version": "1.0",
    "id": "bad-empty",
    "name": "Empty Components",
    "description": "components array is empty.",
    "components": [],
    "connections": [],
}

INVALID_MISSING_COMPONENT_FIELDS = {
    "spec_version": "1.0",
    "id": "bad-missing-comp-fields",
    "name": "Missing Component Fields",
    "description": "Component missing required fields.",
    "components": [
        {"id": "n1", "type": "input"},  # Missing name, params, inputs, outputs
    ],
    "connections": [],
}


def write_temp_json(doc: dict) -> str:
    """Write a dict to a temporary JSON file and return the path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(doc, f)
    f.close()
    return f.name


# Map of test fixture name -> (document, expected_valid)
ALL_FIXTURES = {
    # Valid
    "valid_minimal": (VALID_MINIMAL, True),
    "valid_block_template": (VALID_WITH_BLOCK_TEMPLATE, True),
    "valid_expr": (VALID_WITH_EXPR, True),
    # Invalid - structural
    "invalid_missing_required": (INVALID_MISSING_REQUIRED, False),
    "invalid_duplicate_component_id": (INVALID_DUPLICATE_COMPONENT_ID, False),
    "invalid_dangling_ref": (INVALID_DANGLING_REF, False),
    "invalid_inconsistent_io": (INVALID_INCONSISTENT_IO, False),
    "invalid_connection_mismatch": (INVALID_CONNECTION_MISMATCH, False),
    "invalid_null_param": (INVALID_NULL_PARAM, False),
    "invalid_nested_param": (INVALID_NESTED_PARAM, False),
    "invalid_duplicate_conn_id": (INVALID_DUPLICATE_CONN_ID, False),
    "invalid_empty_components": (INVALID_EMPTY_COMPONENTS, False),
    "invalid_missing_component_fields": (INVALID_MISSING_COMPONENT_FIELDS, False),
    "invalid_bad_version": (INVALID_BAD_VERSION, False),
    # Invalid - block templates
    "invalid_block_ref": (INVALID_BLOCK_REF, False),
    "invalid_dup_node_id": (INVALID_DUP_NODE_ID, False),
    "invalid_edge_ref": (INVALID_EDGE_REF, False),
    "invalid_bad_repeat_count": (INVALID_BAD_REPEAT_COUNT, False),
    "invalid_bad_repeat_mode": (INVALID_BAD_REPEAT_MODE, False),
    "invalid_override_out_of_range": (INVALID_OVERRIDE_OUT_OF_RANGE, False),
    "invalid_unresolved_param": (INVALID_UNRESOLVED_PARAM, False),
    "invalid_bad_expr": (INVALID_BAD_EXPR, False),
    "invalid_circular_ref": (INVALID_CIRCULAR_REF, False),
}
