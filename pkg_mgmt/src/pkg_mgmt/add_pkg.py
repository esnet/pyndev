#!/usr/bin/env python3
import argparse
from pathlib import Path

from .cli import validate_package_name
from .toml import create_pyproject, update_pyproject
from .utils import create_skeleton, sync_managed_files


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="add-pkg", description=("Create NSO service packages and update project support files")
    )
    parser.add_argument("package_name", help="Name of the package to create")
    parser.add_argument(
        "-b",
        "--build-dependency",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "Specify a package that is a build dependency to the new package, "
            "can be declared multiple times for additional dependencies"
        ),
    )
    parser.add_argument(
        "-d",
        "--dependency",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "Specify a package that is a both a build and runtime dependency "
            "to the new package, can be declared multiple times for additional"
            " dependencies"
        ),
    )
    parser.add_argument(
        "--description",
        type=str,
        default="pyndev generated nso package",
        help="Specify a package desription to be used in package meta data",
    )
    parser.add_argument("-e", "--empty", action="store_true", help="Skips example files for a new package")
    parser.add_argument("-p", "--python", action="store_true", help="Create Python service skeleton")
    parser.add_argument(
        "--python-requirements", action="store_true", help="Install python requirements.txt in NSO package context"
    )
    parser.add_argument(
        "-r",
        "--runtime-dependency",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "Specify a package that is a runtime dependency to the new "
            "package, can be declared multiple times for additional "
            "dependencies"
        ),
    )
    parser.add_argument("-t", "--template", action="store_true", help="Create template service skeleton")
    parser.add_argument(
        "-u",
        "--unmanaged",
        action="store_true",
        help=("Indicate the src package should not be modified by the python sync process, implies --empty"),
    )
    parser.add_argument("-v", "--version", type=str, default="0.1.0", help="Specify the package version at creation")
    args = parser.parse_args()
    if args.python_requirements and not args.python:
        parser.error("--python-requirments requires --python")
    build_deps = list(set(args.dependency) | set(args.build_dependency))
    runtime_deps = list(set(args.dependency) | set(args.runtime_dependency))

    validate_package_name(args.package_name)
    update_pyproject(args.package_name, args.version)

    pkg_path = Path(f"packages/{args.package_name}")
    pkg_path.mkdir(parents=True, exist_ok=True)

    nso_pkg = pkg_path / "src"
    nso_pkg.mkdir(exist_ok=True)
    nso_src = nso_pkg / "src"
    nso_src.mkdir(exist_ok=True)

    pyproject = pkg_path / "pyproject.toml"
    if not pyproject.exists():
        create_pyproject(
            args.package_name,
            args.version,
            args.description,
            build_deps,
            runtime_deps,
            args.unmanaged,
            args.python,
            args.python_requirements,
        )

    sync_managed_files(args.package_name)
    if not args.unmanaged:
        create_skeleton(args.package_name, args.python, args.template, args.empty)


if __name__ == "__main__":
    main()
