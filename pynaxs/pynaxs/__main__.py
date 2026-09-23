"""Allow `python -m pynaxs validate ...`"""
import sys
from .cli import main

sys.exit(main())
