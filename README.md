# NAXS — Neural Architecture Exchange Specification

**Version:** 0.1  
**Status:** Draft for Public Review  
**License:** CC-BY-4.0 / Apache-2.0 (dual)  
**Website:** https://neuroarchitectures.github.io  
**Community:** https://github.com/neuroarchitectures

---

## What is NAXS?

NAXS (Neural Architecture Exchange Specification) defines a **vendor-independent, framework-agnostic JSON format** for describing neural network architectures as directed graphs of typed, parameterized components.

NAXS is **not** an execution format (like ONNX), a training configuration (like PyTorch Lightning YAML), or a compiler IR (like MLIR). It is an **architecture topology exchange format**: it describes *what the architecture is* — its components, their parameters, and their connectivity — without prescribing *how* it runs.

The goal is interoperability: any tool, vendor, research group, or automated agent can produce or consume a NAXS document to share, compare, transform, or analyze a neural architecture without depending on a specific framework.

## Repository Structure

```
.
├── specification.md              # Full specification (§1–§25 + appendices)
├── LICENSE                       # Apache-2.0
├── naxs/
│   └── v0.1/
│       ├── schema.json           # Machine-readable JSON Schema (draft 2020-12)
│       └── examples/
│           ├── minimal_mlp.json            # Smallest valid document
│           ├── symbolic_shape.json         # Symbolic/dynamic dimensions
│           ├── vendor_custom.json         # Custom operators + vendor metadata
│           ├── bert_base_repetition.json  # 12-layer transformer via block templates
│           ├── resnet_repetition.json     # 4-stage ResNet via repeat directives
│           └── nested_blocks_llama.json  # Nested block templates + $expr params
├── pynaxs/                       # Python validator (pip install -e pynaxs/)
│   ├── pyproject.toml
│   ├── pynaxs/
│   │   ├── validator.py          # Core validation engine (§13 + §25)
│   │   ├── registry.py           # Standard operator/parameter registry
│   │   └── cli.py                # CLI entry point
│   └── tests/                    # 33 tests covering all validation rules
└── README.md                     # This file
```

## Key Features

- **Graph-first** — An architecture is a directed graph; connectivity is explicit.
- **Parameterized** — Each component carries typed parameters; one operator type produces many concrete nodes.
- **Block templates & repetition** — Define a reusable subgraph once, then reference and repeat it (e.g. 12 transformer layers from a single template). See §25.
- **Extensible** — Unknown fields are preserved, not rejected. Vendors can add metadata without forking the spec.
- **Human-readable** — A valid NAXS document can be as small as 10 lines of JSON.

## Quick Start

A minimal NAXS document:

```json
{
  "spec_version": "0.1",
  "id": "minimal-mlp",
  "name": "Minimal MLP",
  "components": [
    {
      "id": "n1",
      "type": "input",
      "name": "x",
      "params": { "shape": [10] },
      "inputs": [],
      "outputs": ["n2"]
    },
    {
      "id": "n2",
      "type": "linear",
      "name": "fc1",
      "params": { "inFeatures": 10, "outFeatures": 5 },
      "inputs": ["n1"],
      "outputs": []
    }
  ],
  "connections": [
    { "id": "c1", "from": "n1", "to": "n2" }
  ]
}
```

## Validation

### pynaxs — Python Validator

`pynaxs` is the reference validator implementation. It checks all rules from §13 (structural integrity, consistency, parameter validity, soft validation) and §25.11 (block template validation).

```bash
# Install
cd pynaxs && pip install -e .

# Validate a single file
pynaxs validate path/to/architecture.json

# Validate all JSON files in a directory
pynaxs validate path/to/architectures/

# Suppress warnings (--strict = only show errors)
pynaxs validate --strict path/to/architecture.json

# JSON output for CI integration
pynaxs validate --format json path/to/architecture.json
```

Python API:

```python
from pynaxs import NaxsValidator

validator = NaxsValidator()
result = validator.validate_file("architecture.json")

if result.is_valid():
    print(f"Valid! ({len(result.warnings)} warnings)")
else:
    for err in result.errors:
        print(f"ERROR [{err.rule}] {err.path}: {err.message}")
```

### JSON Schema

For structural validation only, the JSON Schema can be used directly:

```bash
# Using python-jsonschema
pip install jsonschema
python -c "
import json, jsonschema
schema = json.load(open('naxs/v0.1/schema.json'))
doc = json.load(open('naxs/v0.1/examples/minimal_mlp.json'))
jsonschema.validate(doc, schema)
print('Valid!')
"
```

## Specification

The full specification is in [`specification.md`](specification.md). Key sections:

| Section | Topic |
|---------|-------|
| §4–§5 | Document & component structure |
| §6 | Parameter value types |
| §7 | Operator type registry (79 standard types) |
| §9–§10 | Metadata & provenance |
| §13 | Validation rules |
| §20 | Conformance (producer / consumer / validator) |
| §25 | Block templates & repetition |
| Appendix A | Standard parameter name catalog |
| Appendix B | Scope pattern catalog |

## License

Code in this repository is licensed under [Apache-2.0](LICENSE). Documentation — the specification text in `specification.md`, including the JSON examples embedded within it — is licensed under [CC-BY-4.0](LICENSE-CC-BY-4.0.md). See individual directories for details:

| Path | Content | License |
|------|---------|---------|
| `specification.md` | Specification text (including embedded JSON examples) | CC-BY-4.0 |
| `naxs/v0.1/` | JSON Schema + example documents | Apache-2.0 |
| `pynaxs/` | Reference validator | Apache-2.0 |
| `assets/` | Brand assets | Apache-2.0 |

Implementations may choose either license.

## Contributing

This specification is in **Draft for Public Review** status. Feedback, issues, and pull requests are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) and the [issue templates](.github/ISSUE_TEMPLATE/) for how to submit spec feedback or register a new operator type.
