"""Entry point for ``python -m pynaxs``; delegates to the CLI."""
import sys
from .cli import main

sys.exit(main())
