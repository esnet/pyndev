import re
import sys


def error(msg: str):
    """Simple CLI error handling"""
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def validate_package_name(name: str) -> None:
    """
    Validate package name

    ncs-make-package validation plus a few extras
    """
    if not name:
        error("Package name cannot be empty")

    if re.search(r'[\'"\t\r\n /\\]', name):
        error(f"Illegal package name characters in name '{name}'")
