"""pynaxs — validator for NAXS v0.1 architecture documents.

NAXS (Neural Architecture Exchange Specification) is a JSON format for
describing neural network architectures as directed graphs of typed,
parameterized components, with optional block templates and repetition.

This package validates JSON documents against the NAXS v0.1 rules:

* Structural integrity — required fields, non-empty component list,
  unique component/connection IDs, and resolvable cross-references.
* Consistency — inputs/outputs listings agree in both directions and
  match the declared connections.
* Parameter validity — parameter values must be flat JSON scalars or
  arrays of integers/strings (no nulls or nested objects).
* Soft validation — warnings for suboptimal but conforming documents,
  such as missing descriptions or scopes, or parameter names outside
  the standard catalog.
* Block templates — unique template IDs, resolvable block references
  and edges, valid repeat directives, and resolvable ``$param`` /
  ``$expr`` references without circular template nesting.
"""

from .validator import NaxsValidator, ValidationResult, ValidationError, ValidationWarning
from .registry import OPERATOR_REGISTRY, STANDARD_PARAMS

__version__ = "0.1.0"
__all__ = [
    "NaxsValidator",
    "ValidationResult",
    "ValidationError",
    "ValidationWarning",
    "OPERATOR_REGISTRY",
    "STANDARD_PARAMS",
]
