# pynaxs — NAXS Validator

Python validator for the **Neural Architecture Exchange Specification (NAXS)** v1.0.

## Install

```bash
cd /Users/xiaming/Workspace/naxs/pynaxs
pip install -e .
```

## CLI Usage

```bash
# Validate a single file
pynaxs validate path/to/architecture.json

# Validate all JSON files in a directory
pynaxs validate path/to/architectures/

# Show only errors (suppress warnings)
pynaxs validate --strict path/to/architecture.json

# JSON output for CI integration
pynaxs validate --format json path/to/architecture.json
```

## Python API

```python
from pynaxs import NaxsValidator

validator = NaxsValidator()
result = validator.validate_file("architecture.json")

if result.is_valid():
    print(f"Valid! ({len(result.warnings)} warnings)")
else:
    for err in result.errors:
        print(f"ERROR: {err.path}: {err.message}")
    for warn in result.warnings:
        print(f"WARN:  {warn.path}: {warn.message}")
```

## Validation Coverage

Implements all rules from the NAXS specification:

| Section | Rules |
|---------|-------|
| §13.1 Structural Integrity | Required fields, component ID uniqueness, reference integrity, connection integrity |
| §13.2 Consistency | inputs/outputs bidirectional consistency, connections consistency |
| §13.3 Parameter Validity | Type checking, null/nested-object rejection |
| §13.4 Soft Validation | Warnings for custom ops with empty params, missing scope, non-standard param names, missing description |
| §25.11 Block Templates | Unique template IDs, block_ref resolution, node uniqueness, edge references, repeat directives, $paramName resolution, $expr syntax, circular reference detection |

## License

Apache-2.0
