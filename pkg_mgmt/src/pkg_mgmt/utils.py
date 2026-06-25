import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .cli import error
from .toml import (
    get_pkg_build_dependencies,
    get_pkg_dependencies,
    get_pyndev_description,
    get_pyndev_python_components,
    get_pyndev_requirements,
    get_pyndev_unmanaged,
)


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command"""
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result


def write_template(file: str, template_name: str, template_type: str, data: dict[any]) -> None:
    """Writes a template to file with some jinja2 formatting"""
    pkg_mgmt = Path(__file__).parent
    env = Environment(
        loader=FileSystemLoader(f"{pkg_mgmt}/{template_type}"),
        extensions=["jinja2.ext.do"],
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_name)
    doc = template.render(**data).rstrip()
    # shakes fist at jinja2 whitespace rules
    if doc[-1] != "\n":
        doc = f"{doc}\n"
    try:
        with open(file, "w") as f:
            f.write(doc)
    except Exception as e:
        error(f"Failed to write {file}: {e}")


def sync_build_hook(pkg_name: str, dependencies: list[str], unmanaged: bool = False) -> None:
    """Sync pyndev package build_hook script"""
    script_path = Path("packages") / pkg_name / "build_hook.py"
    data = {"dependencies": dependencies, "unmanaged": unmanaged}
    write_template(str(script_path), "build_hook.py.j2", "templates", data)


def sync_dockerfile(
    pkg_name: str, dependencies: list[str] = [], unmanaged: bool = False, py_requirements: bool = False
) -> None:
    """Sync pyndev package Dockerfile"""
    dockerfile_path = Path("packages") / pkg_name / "Dockerfile"
    data = {"name": pkg_name, "dependencies": dependencies, "unmanaged": unmanaged, "py_requirements": py_requirements}
    write_template(str(dockerfile_path), "Dockerfile.j2", "templates", data)


def sync_package_meta_data(pkg_name: str, dependencies: list[str] = []) -> None:
    """Sync pyndev package package-meta-data.xml"""
    pkg_path = Path("packages") / pkg_name
    nso_path = pkg_path / "src"
    pkg_meta_data = nso_path / "package-meta-data.xml"
    ncs_version = os.environ.get("NSO_VERSION", "0.0.0")
    pkg_namespace = {}
    version_file = pkg_path / "_version.py"
    if version_file.exists():
        exec(version_file.read_text(), pkg_namespace)
    pkg_version = pkg_namespace.get("__version__", "0.0.0")
    pkg_version = re.sub(r"\+nso[^.]+\.[^.]+(\.[^.]+)?", "", pkg_version)
    meta_data = {
        "name": pkg_name,
        "description": get_pyndev_description(pkg_name),
        "version": pkg_version,
        "ncs_version": ncs_version,
        "dependencies": dependencies,
        "python": {"components": get_pyndev_python_components(pkg_name)},
    }
    write_template(str(pkg_meta_data), "package-meta-data.xml.j2", "templates", meta_data)


def sync_makefile(pkg_name: str, dependencies: list[str] = []) -> None:
    """Sync pyndev package src/Makefile"""
    nso_src = Path("packages") / pkg_name / "src" / "src"
    makefile = nso_src / "Makefile"
    make_data = {"dependencies": dependencies}
    write_template(str(makefile), "Makefile.j2", "templates", make_data)


def sync_gitignore(pkg_name: str) -> None:
    """Syng managed package gitignore to skip dynamic meta data"""
    pkg_meta_data = "src/package-meta-data.xml"
    gitignore_path = Path("packages") / pkg_name / ".gitignore"
    if gitignore_path.exists():
        gitignore = gitignore_path.read_text()
        gitignore_lines = gitignore.splitlines()
        if pkg_meta_data not in gitignore_lines:
            with gitignore_path.open("a") as f:
                if gitignore and not gitignore.endswith("\n"):
                    f.write("\n")
                f.write(f"{pkg_meta_data}\n")
    else:
        gitignore_path.write_text(f"{pkg_meta_data}\n")


def sync_managed_files(pkg_name: str) -> None:
    """Sync package package-meta-data.xml and package Makefile"""
    runtime_dependencies = get_pkg_dependencies(pkg_name)
    build_dependencies = get_pkg_build_dependencies(pkg_name)
    unmanaged = get_pyndev_unmanaged(pkg_name)
    py_requirements = get_pyndev_requirements(pkg_name)

    sync_build_hook(pkg_name, build_dependencies, unmanaged)
    sync_dockerfile(pkg_name, build_dependencies, unmanaged, py_requirements)
    if not unmanaged:
        sync_gitignore(pkg_name)
        sync_package_meta_data(pkg_name, runtime_dependencies)
        sync_makefile(pkg_name, build_dependencies)


def create_skeleton(pkg_name: str, python: bool, template: bool, empty: bool) -> None:
    """Create example files for a new NSO package"""
    sync_managed_files(pkg_name)
    if empty:
        return

    pkg_path = Path("packages") / pkg_name / "src"

    if python or template:
        yang_path = pkg_path / "src/yang"
        yang_path.mkdir(exist_ok=True)
        yang = yang_path / f"{pkg_name}.yang"
        if not yang.exists():
            data = {"name": pkg_name, "date": date.today().strftime("%Y-%m-%d")}
            write_template(str(yang), "example.yang.j2", "examples", data)

    if template:
        template_path = pkg_path / "templates"
        template_path.mkdir(exist_ok=True)
        template = template_path / f"{pkg_name}-template.xml"
        if not template.exists():
            data = {"name": pkg_name, "python": python}
            write_template(str(template), "example-template.xml.j2", "examples", data)

    if python:
        # New package, assume there is only one default component
        component = get_pyndev_python_components(pkg_name)[0]
        class_name = "".join(word.capitalize() for word in component["project"].split("_"))
        python_path = pkg_path / "python" / component["project"]
        python_path.mkdir(parents=True, exist_ok=True)
        init_file = python_path / "__init__.py"
        init_file.touch()
        python_file = python_path / "main.py"
        if not python_file.exists():
            data = {
                "name": component["name"],
                "application": component["application"],
                "class_name": class_name,
                "template": template,
                "package": pkg_name,
            }
            write_template(str(python_file), "example.py.j2", "examples", data)
