#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path

from .cli import error
from .toml import remove_pyproject_package


def main() -> None:
    parser = argparse.ArgumentParser(prog="rm-pkg", description="Remove a single NSO service package")
    parser.add_argument("package_name", help="Name of the package to remove")
    args = parser.parse_args()

    remove_pyproject_package(args.package_name)
    pkg_path = Path(f"packages/{args.package_name}")
    if pkg_path.exists():
        shutil.rmtree(pkg_path)
    else:
        error(f"package directory {pkg_path} not found!")


if __name__ == "__main__":
    main()
