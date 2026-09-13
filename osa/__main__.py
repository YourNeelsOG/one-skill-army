"""Allow running the engine as `python3 -m osa`."""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
