name: 📋 Specification feedback
description: Report an ambiguity, gap, or contradiction in the NAXS specification
labels: ["spec", "triage"]
body:
  - type: dropdown
    id: feedback-type
    attributes:
      label: Feedback type
      options:
        - Ambiguity (the spec is unclear)
        - Gap (something is missing)
        - Contradiction (two parts of the spec disagree)
        - Editorial (typo, formatting, clarity)
        - Enhancement (new optional feature)
    validations:
      required: true
  - type: input
    id: spec-section
    attributes:
      label: Specification section
      description: Which section(s) does this concern? (e.g. §7, §13.2, Appendix A)
      placeholder: "§7.1"
    validations:
      required: true
  - type: textarea
    id: description
    attributes:
      label: Description
      description: What is the issue, and what would you propose instead?
    validations:
      required: true
  - type: textarea
    id: example
    attributes:
      label: Example
      description: A JSON snippet, document, or scenario that demonstrates the issue
      render: json
  - type: checkboxes
    id: checks
    attributes:
      label: Checks
      options:
        - label: I searched existing issues and found no duplicates
          required: true
