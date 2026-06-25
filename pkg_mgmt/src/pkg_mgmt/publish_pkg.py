#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

from .utils import run


def is_nso_wheel(file: str, filter: str | None = None) -> bool:
    """Match wheels with nso local version

    call with optional package name with some fuzzy matching
    """
    if filter is None:
        if "+nso" in file and file.endswith(".whl"):
            return True
    else:
        normal_name = re.sub(r"[-_.]+", "_", filter).lower()
        if file.startswith(normal_name) and "+nso" in file and file.endswith(".whl"):
            return True

    return False


def publish(package: str | None = None) -> None:
    """Publish wheels from dist directory

    the NSO generated wheel will always generate a new and unique
    package hash regardless if there were or were not any source
    updates and uv publish will throw an error when attempting
    to publish a duplicate packged with a unique hash
    pyndev treats the first published package version as the
    authoritative source and will silently skip hash differences
    """
    dist_path = Path("dist")
    if not dist_path.exists():
        print("ERROR: dist directory does not exist")
        sys.exit(1)

    wheels = [wheel for wheel in dist_path.iterdir() if is_nso_wheel(wheel.name, package)]
    for wheel in wheels:
        result = run(f"uv publish --index private {wheel}", check=False)
        if result.returncode != 0 and "Local file and index file do not match" not in result.stderr:
            sys.exit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish nso packages to private index PyPI",
    )
    parser.add_argument(
        "--package",
        help="Fuzzy filter on package name (e.g., nokia-sros_nc-24.10 or nokia-sros for all versions)",
    )
    args = parser.parse_args()

    publish(args.package)


if __name__ == "__main__":
    main()
