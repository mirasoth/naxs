name: 🧩 Register an operator type
description: Propose a new operator type for the NAXS standard registry (§7)
labels: ["operator-registration", "triage"]
body:
  - type: input
    id: type-name
    attributes:
      label: Proposed type name
      description: camelCase identifier (e.g. `axialAttention`)
      placeholder: "axialAttention"
    validations:
      required: true
  - type: input
    id: category
    attributes:
      label: Category
      description: Core/I-O, Linear, Convolution, Attention, Normalization, Activation, Feed-Forward, Structural, Specialized, or a new category
      placeholder: "Attention"
    validations:
      required: true
  - type: textarea
    id: description
    attributes:
      label: Description
      description: What does this operator compute? Which architectures use it?
    validations:
      required: true
  - type: textarea
    id: parameters
    attributes:
      label: Expected parameters
      description: Parameter names, types, and meanings (e.g. `numHeads: integer`)
    validations:
      required: true
  - type: textarea
    id: arity
    attributes:
      label: Input/output arity
      description: How many inputs/outputs does this operator typically have?
    validations:
      required: true
  - type: textarea
    id: examples
    attributes:
      label: Real-world examples (at least 3)
      description: "Per §11.2, at least 3 real-world architectures using this type. Include papers, model cards, or NAXS JSON snippets."
    validations:
      required: true
  - type: checkboxes
    id: checks
    attributes:
      label: Checks
      options:
        - label: The type name does not conflict with an existing registry entry (§7.1)
          required: true
        - label: I searched existing issues and found no duplicates
          required: true
