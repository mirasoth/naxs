"""NAXS v1.0 validator — core validation engine.

Implements all validation rules from the NAXS specification:
  - §13.1 Structural Integrity
  - §13.2 Consistency
  - §13.3 Parameter Validity
  - §13.4 Soft Validation (warnings)
  - §25.11 Block Template validation
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import jsonschema

from .registry import OPERATOR_REGISTRY, STANDARD_PARAMS

# ─── Path to the bundled JSON Schema ──────────────────────────────────────────

# Look for schema.json relative to the package, then in the repo root
_SCHEMA_CANDIDATES = [
    Path(__file__).resolve().parent / "schema.json",          # bundled in package
    Path(__file__).resolve().parent.parent / "naxs" / "v1.0" / "schema.json",  # repo root
    Path(__file__).resolve().parent.parent.parent / "naxs" / "v1.0" / "schema.json",  # repo root (installed)
]


def _load_schema() -> dict[str, Any]:
    """Load the NAXS JSON Schema from the repository."""
    for candidate in _SCHEMA_CANDIDATES:
        if candidate.exists():
            with open(candidate) as f:
                return json.load(f)
    raise FileNotFoundError(
        "NAXS schema.json not found. Expected it at one of:\n"
        + "\n".join(f"  {p}" for p in _SCHEMA_CANDIDATES)
    )


# ─── Data classes for validation results ──────────────────────────────────────


@dataclass
class ValidationError:
    """A hard validation error (document is non-conforming)."""

    path: str
    message: str
    rule: str  # e.g. "§13.1.4"


@dataclass
class ValidationWarning:
    """A soft validation warning (document is conforming but suboptimal)."""

    path: str
    message: str
    rule: str


@dataclass
class ValidationResult:
    """Result of validating a NAXS document."""

    document_path: str
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationWarning] = field(default_factory=list)

    def is_valid(self) -> bool:
        """True if there are no hard errors."""
        return len(self.errors) == 0

    def add_error(self, path: str, message: str, rule: str) -> None:
        self.errors.append(ValidationError(path=path, message=message, rule=rule))

    def add_warning(self, path: str, message: str, rule: str) -> None:
        self.warnings.append(ValidationWarning(path=path, message=message, rule=rule))

    def summary(self) -> str:
        if self.is_valid():
            return f"✅ VALID: {self.document_path} ({len(self.warnings)} warnings)"
        return f"❌ INVALID: {self.document_path} ({len(self.errors)} errors, {len(self.warnings)} warnings)"


# ─── Expression parser for $expr validation ──────────────────────────────────

_EXPR_TOKEN_RE = re.compile(r"[A-Za-z_]\w*|\d+\.?\d*|[+\-*/()]")
_PARAM_REF_RE = re.compile(r"^\$\w+$")


def _validate_expr(expr: str, declared_params: set[str]) -> tuple[bool, str]:
    """Check that a $expr string is syntactically valid and references only declared params.

    Returns (is_valid, error_message).
    """
    try:
        tokens = _EXPR_TOKEN_RE.findall(expr)
        if not tokens:
            return False, "empty expression"

        # Extract identifiers (parameter references)
        identifiers = {
            t for t in tokens
            if t[0].isalpha() or t[0] == "_"
        }

        # Check all identifiers are declared params
        unknown = identifiers - declared_params
        if unknown:
            return False, f"references undeclared parameter(s): {', '.join(sorted(unknown))}"

        # Basic balance check for parentheses
        depth = 0
        for t in tokens:
            if t == "(":
                depth += 1
            elif t == ")":
                depth -= 1
                if depth < 0:
                    return False, "unbalanced parentheses"
        if depth != 0:
            return False, "unbalanced parentheses"

        return True, ""

    except Exception as e:
        return False, f"parse error: {e}"


# ─── Main validator ───────────────────────────────────────────────────────────


class NaxsValidator:
    """Validates NAXS v1.0 documents against the specification."""

    def __init__(self, schema: Optional[dict] = None):
        self._schema = schema or _load_schema()

    # ── Public API ──────────────────────────────────────────────────────────

    def validate_file(self, path: str | Path) -> ValidationResult:
        """Validate a NAXS document from a file path."""
        path = str(path)
        with open(path) as f:
            try:
                doc = json.load(f)
            except json.JSONDecodeError as e:
                result = ValidationResult(document_path=path)
                result.add_error("$", f"Invalid JSON: {e}", "JSON")
                return result
        return self.validate_document(doc, path)

    def validate_str(self, json_str: str, source_name: str = "<string>") -> ValidationResult:
        """Validate a NAXS document from a JSON string."""
        try:
            doc = json.loads(json_str)
        except json.JSONDecodeError as e:
            result = ValidationResult(document_path=source_name)
            result.add_error("$", f"Invalid JSON: {e}", "JSON")
            return result
        return self.validate_document(doc, source_name)

    def validate_document(self, doc: Any, source_name: str = "<document>") -> ValidationResult:
        """Validate a parsed NAXS document (dict)."""
        result = ValidationResult(document_path=source_name)

        if not isinstance(doc, dict):
            result.add_error("$", "Document must be a JSON object", "§13.1.1")
            return result

        # Phase 0: JSON Schema structural validation
        self._validate_json_schema(doc, result)

        # Phase 1: Structural integrity (§13.1)
        self._validate_structural(doc, result)

        # Phase 2: Consistency (§13.2)
        self._validate_consistency(doc, result)

        # Phase 3: Parameter validity (§13.3)
        self._validate_params(doc, result)

        # Phase 4: Block template validation (§25.11)
        self._validate_block_templates(doc, result)

        # Phase 5: Soft validation warnings (§13.4)
        self._validate_soft(doc, result)

        return result

    # ── Phase 0: JSON Schema ───────────────────────────────────────────────

    def _validate_json_schema(self, doc: dict, result: ValidationResult) -> None:
        """Run the JSON Schema validator (structural type/shape checks)."""
        try:
            jsonschema.validate(doc, self._schema)
        except jsonschema.ValidationError as e:
            # Convert the jsonschema path to a dot-path
            parts = [str(p) for p in e.absolute_path]
            path = "$" + ("." + ".".join(parts) if parts else "")
            result.add_error(path, e.message, "JSON-Schema")
        except jsonschema.SchemaError as e:
            result.add_error("$", f"Schema error: {e}", "JSON-Schema")

    # ── Phase 1: Structural Integrity (§13.1) ──────────────────────────────

    def _validate_structural(self, doc: dict, result: ValidationResult) -> None:
        # §13.1.1: required top-level fields present and non-null
        required_top = ["spec_version", "id", "name", "components"]
        for field_name in required_top:
            if field_name not in doc or doc[field_name] is None:
                result.add_error(f"$.{field_name}", f"Required field '{field_name}' is missing or null", "§13.1.1")

        # connections is required per JSON Schema, but check anyway
        if "connections" not in doc or doc["connections"] is None:
            result.add_error("$.connections", "Required field 'connections' is missing or null", "§13.1.1")

        # §13.1.2: components is non-empty array
        components = doc.get("components")
        if isinstance(components, list):
            if len(components) == 0:
                result.add_error("$.components", "components array must not be empty", "§13.1.2")
        elif components is not None:
            result.add_error("$.components", "components must be an array", "§13.1.2")

        # §13.1.3: every component has required fields
        component_ids: set[str] = set()
        component_map: dict[str, dict] = {}

        for i, comp in enumerate(components or []):
            cpath = f"$.components[{i}]"
            if not isinstance(comp, dict):
                result.add_error(cpath, "Component must be a JSON object", "§13.1.3")
                continue

            comp_id = comp.get("id")
            if comp_id:
                component_map[comp_id] = comp

            for req in ["id", "type", "name", "params", "inputs", "outputs"]:
                if req not in comp or comp[req] is None:
                    result.add_error(f"{cpath}.{req}", f"Component missing required field '{req}'", "§13.1.3")

            # §13.1.4: unique component IDs
            if comp_id:
                if comp_id in component_ids:
                    result.add_error(f"{cpath}.id", f"Duplicate component id '{comp_id}'", "§13.1.4")
                component_ids.add(comp_id)

        # §13.1.5: inputs/outputs reference existing component IDs
        for i, comp in enumerate(components or []):
            if not isinstance(comp, dict):
                continue
            cpath = f"$.components[{i}]"
            comp_id = comp.get("id", f"<index:{i}>")
            for field_name in ("inputs", "outputs"):
                refs = comp.get(field_name, [])
                if not isinstance(refs, list):
                    result.add_error(f"{cpath}.{field_name}", f"'{field_name}' must be an array", "§13.1.3")
                    continue
                for j, ref in enumerate(refs):
                    if not isinstance(ref, str):
                        result.add_error(f"{cpath}.{field_name}[{j}]", "Reference must be a string", "§13.1.5")
                        continue
                    if ref not in component_ids:
                        result.add_error(
                            f"{cpath}.{field_name}[{j}]",
                            f"References non-existent component id '{ref}'",
                            "§13.1.5",
                        )

        # §13.1.6-8: connections integrity
        connections = doc.get("connections", [])
        if isinstance(connections, list):
            conn_ids: set[str] = set()
            for i, conn in enumerate(connections):
                cpath = f"$.connections[{i}]"
                if not isinstance(conn, dict):
                    result.add_error(cpath, "Connection must be a JSON object", "§13.1.6")
                    continue

                for req in ["id", "from", "to"]:
                    if req not in conn or conn[req] is None:
                        result.add_error(f"{cpath}.{req}", f"Connection missing required field '{req}'", "§13.1.6")

                # §13.1.7: connection from/to reference existing components
                for field_name in ("from", "to"):
                    ref = conn.get(field_name)
                    if isinstance(ref, str) and ref not in component_ids:
                        result.add_error(
                            f"{cpath}.{field_name}",
                            f"References non-existent component id '{ref}'",
                            "§13.1.7",
                        )

                # §13.1.8: unique connection IDs
                conn_id = conn.get("id")
                if conn_id:
                    if conn_id in conn_ids:
                        result.add_error(f"{cpath}.id", f"Duplicate connection id '{conn_id}'", "§13.1.8")
                    conn_ids.add(conn_id)

        # Store for later phases
        result._component_ids = component_ids  # type: ignore[attr-defined]
        result._component_map = component_map  # type: ignore[attr-defined]

    # ── Phase 2: Consistency (§13.2) ────────────────────────────────────────

    def _validate_consistency(self, doc: dict, result: ValidationResult) -> None:
        components = doc.get("components", [])
        if not isinstance(components, list):
            return

        component_map: dict[str, dict] = getattr(result, "_component_map", {})

        # §13.2.9: For every component A that lists B in outputs, B MUST list A in inputs
        for i, comp in enumerate(components):
            if not isinstance(comp, dict):
                continue
            comp_id = comp.get("id")
            if not comp_id:
                continue
            cpath = f"$.components[{i}]"
            outputs = comp.get("outputs", [])
            if not isinstance(outputs, list):
                continue
            for ref in outputs:
                if not isinstance(ref, str):
                    continue
                target = component_map.get(ref)
                if target is None:
                    continue  # already reported in §13.1.5
                target_inputs = target.get("inputs", [])
                if not isinstance(target_inputs, list):
                    continue
                if comp_id not in target_inputs:
                    result.add_error(
                        f"{cpath}.outputs",
                        f"Component '{comp_id}' lists '{ref}' in outputs, but '{ref}' does not list '{comp_id}' in inputs",
                        "§13.2.9",
                    )

        # §13.2.10: For every connection {from: A, to: B}, A MUST list B in outputs and B MUST list A in inputs
        connections = doc.get("connections", [])
        if not isinstance(connections, list):
            return
        for i, conn in enumerate(connections):
            if not isinstance(conn, dict):
                continue
            cpath = f"$.connections[{i}]"
            from_id = conn.get("from")
            to_id = conn.get("to")
            if not (isinstance(from_id, str) and isinstance(to_id, str)):
                continue

            from_comp = component_map.get(from_id)
            to_comp = component_map.get(to_id)

            if from_comp is not None:
                from_outputs = from_comp.get("outputs", [])
                if isinstance(from_outputs, list) and to_id not in from_outputs:
                    result.add_error(
                        f"{cpath}.from",
                        f"Connection from '{from_id}' to '{to_id}', but '{from_id}' does not list '{to_id}' in outputs",
                        "§13.2.10",
                    )

            if to_comp is not None:
                to_inputs = to_comp.get("inputs", [])
                if isinstance(to_inputs, list) and from_id not in to_inputs:
                    result.add_error(
                        f"{cpath}.to",
                        f"Connection from '{from_id}' to '{to_id}', but '{to_id}' does not list '{from_id}' in inputs",
                        "§13.2.10",
                    )

    # ── Phase 3: Parameter Validity (§13.3) ─────────────────────────────────

    def _validate_params(self, doc: dict, result: ValidationResult) -> None:
        components = doc.get("components", [])
        if not isinstance(components, list):
            return

        for i, comp in enumerate(components):
            if not isinstance(comp, dict):
                continue
            cpath = f"$.components[{i}]"
            params = comp.get("params")
            if params is None:
                continue
            if not isinstance(params, dict):
                result.add_error(f"{cpath}.params", "params must be a JSON object", "§13.3.12")
                continue

            for key, val in params.items():
                ppath = f"{cpath}.params.{key}"
                self._check_param_value(key, val, ppath, result)

        # Also check block template node params
        for bt_idx, bt in enumerate(doc.get("block_templates", []) or []):
            if not isinstance(bt, dict):
                continue
            for n_idx, node in enumerate(bt.get("nodes", []) or []):
                if not isinstance(node, dict):
                    continue
                params = node.get("params")
                if not isinstance(params, dict):
                    continue
                npath = f"$.block_templates[{bt_idx}].nodes[{n_idx}]"
                for key, val in params.items():
                    ppath = f"{npath}.params.{key}"
                    self._check_param_value(key, val, ppath, result, allow_param_ref=True)

    def _check_param_value(
        self,
        key: str,
        val: Any,
        path: str,
        result: ValidationResult,
        allow_param_ref: bool = False,
    ) -> None:
        """Check a single parameter value against §13.3 rules."""
        # §13.3.15: MUST NOT be null
        if val is None:
            result.add_error(path, "Parameter value must not be null", "§13.3.15")
            return

        # §13.3.15: MUST NOT be nested objects (except $expr)
        if isinstance(val, dict):
            if allow_param_ref and "$expr" in val:
                expr = val["$expr"]
                if not isinstance(expr, str):
                    result.add_error(path, "$expr value must be a string", "§25.5")
                return
            result.add_error(path, "Parameter value must not be a nested object", "§13.3.15")
            return

        # §13.3.13: integer, float, boolean, string, array
        if isinstance(val, bool):
            return  # booleans are valid
        if isinstance(val, int):
            return
        if isinstance(val, float):
            return
        if isinstance(val, str):
            # $-references are valid in block template context
            if allow_param_ref and _PARAM_REF_RE.match(val):
                return
            return  # strings are valid (including symbolic dimensions)
        if isinstance(val, list):
            # §13.3.14: array elements limited to integer, string
            for j, elem in enumerate(val):
                if isinstance(elem, bool):
                    result.add_error(f"{path}[{j}]", "Array element must not be boolean", "§13.3.14")
                elif not isinstance(elem, (int, str)):
                    result.add_error(f"{path}[{j}]", "Array element must be integer or string", "§13.3.14")
            return

        result.add_error(path, f"Parameter value has invalid type: {type(val).__name__}", "§13.3.13")

    # ── Phase 4: Block Template Validation (§25.11) ─────────────────────────

    def _validate_block_templates(self, doc: dict, result: ValidationResult) -> None:
        block_templates = doc.get("block_templates")
        if block_templates is None:
            block_templates = []
        if not isinstance(block_templates, list):
            block_templates = []

        # §25.11.1: unique template IDs
        template_ids: set[str] = set()
        templates: dict[str, dict] = {}

        for i, bt in enumerate(block_templates):
            if not isinstance(bt, dict):
                continue
            btpath = f"$.block_templates[{i}]"
            bt_id = bt.get("id")
            if bt_id:
                if bt_id in template_ids:
                    result.add_error(f"{btpath}.id", f"Duplicate block template id '{bt_id}'", "§25.11.1")
                template_ids.add(bt_id)
                templates[bt_id] = bt

            # §25.11.3: template nodes have unique IDs within the template
            node_ids: set[str] = set()
            nodes = bt.get("nodes", [])
            if isinstance(nodes, list):
                for j, node in enumerate(nodes):
                    if not isinstance(node, dict):
                        continue
                    nid = node.get("id")
                    if nid:
                        if nid in node_ids:
                            result.add_error(
                                f"{btpath}.nodes[{j}].id",
                                f"Duplicate node id '{nid}' within template '{bt_id}'",
                                "§25.11.3",
                            )
                        node_ids.add(nid)

            # §25.11.4: template edges reference existing node IDs
            edges = bt.get("edges", [])
            if isinstance(edges, list):
                for j, edge in enumerate(edges):
                    if not isinstance(edge, dict):
                        continue
                    epath = f"{btpath}.edges[{j}]"
                    for field_name in ("from", "to"):
                        ref = edge.get(field_name)
                        if isinstance(ref, str) and ref not in node_ids:
                            result.add_error(
                                f"{epath}.{field_name}",
                                f"Edge references non-existent node '{ref}' in template '{bt_id}'",
                                "§25.11.4",
                            )

            # §25.11.9: all $paramName references resolve to declared template params or $i
            declared_params = set()
            bt_params = bt.get("params", {})
            if isinstance(bt_params, dict):
                declared_params = set(bt_params.keys())
            declared_params.add("i")  # $i is always available

            for j, node in enumerate(nodes if isinstance(nodes, list) else []):
                if not isinstance(node, dict):
                    continue
                node_params = node.get("params", {})
                if not isinstance(node_params, dict):
                    continue
                for key, val in node_params.items():
                    if isinstance(val, str) and _PARAM_REF_RE.match(val):
                        param_name = val[1:]  # strip $
                        if param_name not in declared_params:
                            result.add_error(
                                f"{btpath}.nodes[{j}].params.{key}",
                                f"$-reference '{val}' does not resolve to declared parameter or '$i'",
                                "§25.11.9",
                            )
                    elif isinstance(val, dict) and "$expr" in val:
                        expr = val["$expr"]
                        if isinstance(expr, str):
                            # Remove $i from declared_params for expr checking
                            # (expr uses bare names, not $-prefixed)
                            expr_params = declared_params - {"i"}
                            ok, msg = _validate_expr(expr, expr_params)
                            if not ok:
                                result.add_error(
                                    f"{btpath}.nodes[{j}].params.{key}",
                                    f"$expr '{expr}' is invalid: {msg}",
                                    "§25.11.10",
                                )

        # §25.11.2: block_ref values reference existing template IDs
        components = doc.get("components", [])
        if isinstance(components, list):
            for i, comp in enumerate(components):
                if not isinstance(comp, dict):
                    continue
                cpath = f"$.components[{i}]"
                block_ref = comp.get("block_ref")
                if isinstance(block_ref, str) and block_ref not in template_ids:
                    result.add_error(
                        f"{cpath}.block_ref",
                        f"block_ref '{block_ref}' does not reference an existing template id",
                        "§25.11.2",
                    )

                # §25.11.5-7: repeat directive validation
                repeat = comp.get("repeat")
                if isinstance(repeat, dict):
                    self._validate_repeat(repeat, f"{cpath}.repeat", result)

                # Also validate repeat in template nodes
                if isinstance(comp, dict):
                    pass  # already handled above

        # Also check repeat directives within block template nodes
        for i, bt in enumerate(block_templates):
            if not isinstance(bt, dict):
                continue
            btpath = f"$.block_templates[{i}]"
            nodes = bt.get("nodes", [])
            if isinstance(nodes, list):
                for j, node in enumerate(nodes):
                    if not isinstance(node, dict):
                        continue
                    repeat = node.get("repeat")
                    if isinstance(repeat, dict):
                        self._validate_repeat(repeat, f"{btpath}.nodes[{j}].repeat", result)

        # §25.11.8: no circular block references
        self._check_circular_refs(templates, result)

    def _validate_repeat(self, repeat: dict, path: str, result: ValidationResult) -> None:
        """Validate a repeat directive (§25.11.5-7)."""
        # §25.11.5: count is positive integer (or $-reference)
        count = repeat.get("count")
        if isinstance(count, int):
            if count < 1:
                result.add_error(f"{path}.count", f"repeat.count must be >= 1, got {count}", "§25.11.5")
        elif isinstance(count, str):
            if not _PARAM_REF_RE.match(count):
                result.add_error(f"{path}.count", f"repeat.count must be a positive integer or $-reference, got '{count}'", "§25.11.5")
        else:
            result.add_error(f"{path}.count", "repeat.count must be a positive integer or $-reference", "§25.11.5")

        # §25.11.6: mode is valid
        mode = repeat.get("mode", "sequential")
        if mode not in ("sequential", "parallel", "stacked"):
            result.add_error(f"{path}.mode", f"repeat.mode must be 'sequential', 'parallel', or 'stacked', got '{mode}'", "§25.11.6")

        # §25.11.7: overrides indices within [0, count-1]
        overrides = repeat.get("overrides", [])
        if isinstance(overrides, list) and isinstance(count, int):
            for k, ov in enumerate(overrides):
                if not isinstance(ov, dict):
                    continue
                idx = ov.get("index")
                if isinstance(idx, int):
                    if idx < 0 or idx >= count:
                        result.add_error(
                            f"{path}.overrides[{k}].index",
                            f"override index {idx} is out of range [0, {count - 1}]",
                            "§25.11.7",
                        )

    def _check_circular_refs(self, templates: dict[str, dict], result: ValidationResult) -> None:
        """Detect circular block template references (§25.11.8)."""
        # Build dependency graph: template -> set of templates it references
        deps: dict[str, set[str]] = {}
        for tid, bt in templates.items():
            referenced: set[str] = set()
            nodes = bt.get("nodes", [])
            if isinstance(nodes, list):
                for node in nodes:
                    if isinstance(node, dict):
                        ref = node.get("block_ref")
                        if isinstance(ref, str) and ref in templates:
                            referenced.add(ref)
            deps[tid] = referenced

        # DFS for cycles
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {tid: WHITE for tid in templates}

        def dfs(node: str, path: list[str]) -> bool:
            color[node] = GRAY
            path.append(node)
            for neighbor in deps.get(node, set()):
                if color.get(neighbor, WHITE) == GRAY:
                    cycle = path[path.index(neighbor):] + [neighbor]
                    result.add_error(
                        f"$.block_templates",
                        f"Circular block reference detected: {' -> '.join(cycle)}",
                        "§25.11.8",
                    )
                    return True
                if color.get(neighbor, WHITE) == WHITE:
                    if dfs(neighbor, path):
                        return True
            path.pop()
            color[node] = BLACK
            return False

        for tid in templates:
            if color[tid] == WHITE:
                dfs(tid, [])

    # ── Phase 5: Soft Validation Warnings (§13.4) ────────────────────────────

    def _validate_soft(self, doc: dict, result: ValidationResult) -> None:
        # §13.4: Documents without a description
        if not doc.get("description"):
            result.add_warning("$.description", "Document has no description", "§13.4")

        components = doc.get("components", [])
        if not isinstance(components, list):
            return

        for i, comp in enumerate(components):
            if not isinstance(comp, dict):
                continue
            cpath = f"$.components[{i}]"
            comp_type = comp.get("type", "")
            params = comp.get("params", {})

            # §13.4: Components with type "custom" and empty params
            if comp_type == "custom" and (not params or len(params) == 0):
                result.add_warning(f"{cpath}.params", "Custom operator with empty params", "§13.4")

            # §13.4: Components without a scope
            if not comp.get("scope"):
                result.add_warning(f"{cpath}.scope", "Component has no scope", "§13.4")

            # §13.4: Parameter names not in the standard registry
            if isinstance(params, dict) and len(params) > 0:
                standard = STANDARD_PARAMS.get(comp_type)
                if standard is not None:  # None means "any params are fine" (e.g. custom)
                    for pname in params:
                        if pname not in standard:
                            result.add_warning(
                                f"{cpath}.params.{pname}",
                                f"Parameter '{pname}' is not in the standard registry for type '{comp_type}'",
                                "§13.4",
                            )
