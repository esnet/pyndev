#!/usr/bin/env python3
import os
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

from .toml import sync_pyproject
from .utils import sync_managed_files


def process_package(pkg: Path, nso_version: str) -> None:
    """Sync individual package managed files"""
    sync_pyproject(nso_version, pkg.name)
    sync_managed_files(pkg.name)


def main() -> None:
    nso_version = os.getenv("NSO_VERSION", "0.0.0")
    sync_pyproject(nso_version)
    packages = Path("packages")
    if packages.is_dir():
        with ProcessPoolExecutor() as executor:
            list(executor.map(partial(process_package, nso_version=nso_version), packages.iterdir()))


if __name__ == "__main__":
    main()
