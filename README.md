# NAXS — Neural Architecture Exchange Specification

**Version:** 1.0  
**Status:** Draft for Public Review  
**License:** CC-BY-4.0 / Apache-2.0 (dual)

---

## What is NAXS?

NAXS (Neural Architecture Exchange Specification) defines a **vendor-independent, framework-agnostic JSON format** for describing neural network architectures as directed graphs of typed, parameterized components.

NAXS is **not** an execution format (like ONNX), a training configuration (like PyTorch Lightning YAML), or a compiler IR (like MLIR). It is an **architecture topology exchange format**: it describes *what the architecture is* — its components, their parameters, and their connectivity — without prescribing *how* it runs.

The goal is interoperability: any tool, vendor, research group, or automated agent can produce or consume a NAXS document to share, compare, transform, or analyze a neural architecture without depending on a specific framework.

## Repository Structure

```
.
├── architecture_spec.md          # Full specification (§1–§25 + appendices)
├── LICENSE                       # Apache-2.0
├── naxs/
│   └── v1.0/
│       ├── schema.json           # Machine-readable JSON Schema (draft 2020-12)
│       └── examples/
│           ├── minimal_mlp.json            # Smallest valid document
│           ├── symbolic_shape.json         # Symbolic/dynamic dimensions
│           ├── vendor_custom.json         # Custom operators + vendor metadata
│           ├── bert_base_repetition.json  # 12-layer transformer via block templates
│           ├── resnet_repetition.json     # 4-stage ResNet via repeat directives
│           └── nested_blocks_llama.json  # Nested block templates + $expr params
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
  "spec_version": "1.0",
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

Validate any NAXS document against the JSON Schema:

```bash
# Using python-jsonschema
pip install jsonschema
python -c "
import json, jsonschema
schema = json.load(open('naxs/v1.0/schema.json'))
doc = json.load(open('naxs/v1.0/examples/minimal_mlp.json'))
jsonschema.validate(doc, schema)
print('Valid!')
"
```

## Specification

The full specification is in [`architecture_spec.md`](architecture_spec.md). Key sections:

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

- The **specification text** (`architecture_spec.md`) is licensed under CC-BY-4.0.
- The **JSON Schema and examples** are licensed under Apache-2.0.
- Implementations may choose either license.

## Contributing

This specification is in **Draft for Public Review** status. Feedback, issues, and pull requests are welcome.
