"""pynaxs — NAXS v1.0 validator.

Validates JSON documents against the Neural Architecture Exchange Specification.

Covers:
  - §13.1 Structural Integrity
  - §13.2 Consistency
  - §13.3 Parameter Validity
  - §13.4 Soft Validation (warnings)
  - §25.11 Block Template validation
"""

from .validator import NaxsValidator, ValidationResult, ValidationError, ValidationWarning
from .registry import OPERATOR_REGISTRY, STANDARD_PARAMS

__version__ = "1.0.0"
__all__ = [
    "NaxsValidator",
    "ValidationResult",
    "ValidationError",
    "ValidationWarning",
    "OPERATOR_REGISTRY",
    "STANDARD_PARAMS",
]
