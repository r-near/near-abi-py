"""
Command-line interface for NEAR Python ABI Builder.
"""

import sys

from .commands import cli


def main():
    """Entry point for the command-line interface."""
    return cli()


if __name__ == "__main__":
    sys.exit(main())
