# Contributing to NAXS

Thank you for your interest in improving the Neural Architecture Exchange Specification! NAXS is in **Draft for Public Review**, and community feedback is essential to making it a useful standard.

## Ways to Contribute

- **Report issues** — ambiguities, contradictions, or gaps in the specification
- **Propose clarifications** — editorial improvements and better examples
- **Register operator types** — new types for the standard registry (see below)
- **Improve `pynaxs`** — the reference Python validator
- **Add examples** — real-world architectures in NAXS format

## Getting Started

1. Read the [specification](specification.md) and the [documentation site](https://neuroarchitectures.github.io).
2. Search [existing issues](https://github.com/neuroarchitectures/naxs/issues) to avoid duplicates.
3. Open a new issue using one of the issue templates (spec feedback or operator registration).

## Proposing Changes to the Specification

1. Fork the repository and create a branch from `main`.
2. Make your change to `specification.md` (and `naxs/v1.0/schema.json` if structural).
3. If your change affects validation behavior, update `pynaxs` and its tests accordingly.
4. Ensure the test suite passes:

   ```bash
   cd pynaxs && pip install -e . && python -m pytest tests/
   ```

5. Open a pull request with a clear description and motivation. Reference any related issues.

## Registering a New Operator Type

The operator type registry (§7 of the specification) grows through community proposals. Per §11.2:

1. Define the type name, description, expected parameters, and input/output arity.
2. Provide **at least 3 real-world architecture examples** using the type.
3. Open an issue with the **operator registration** template.
4. If accepted, the type is added in the next minor version of the specification.

## Versioning & Stability

- **Major** versions may break compatibility and require broad consensus.
- **Minor** versions add optional fields, operator types, and metadata keys.
- **Patch** versions are clarifications and corrections only.

## License

- Specification text: **CC-BY-4.0**
- JSON Schema, examples, and `pynaxs`: **Apache-2.0**

By contributing, you agree that your contributions will be licensed under these terms.
