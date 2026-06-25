import re
from dataclasses import dataclass
from pathlib import Path

import tomlkit
from tomlkit.toml_document import TOMLDocument

from .cli import error


@dataclass
class Component:
    """Type for processing pyndev python components"""

    name: str
    module: str
    project: str | None = None
    application: str | None = None
    upgrade: str | None = None

    def __post_init__(self):
        if self.name == "":
            error("Python component: missing name")
        if self.module == "":
            error(f"Python component {self.name}: missing module")
        application = self.application not in (None, "")
        upgrade = self.upgrade not in (None, "")
        if application == upgrade:
            error(f"Python component {self.name}: Exactly one of 'application' or 'upgrade' must be set")


def load_pyproject(pkg_name: str | None = None) -> TOMLDocument:
    """Load either project or package pyproject"""
    if pkg_name is not None:
        pyproject_path = Path("packages") / pkg_name / "pyproject.toml"
    else:
        pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        error(f"{pyproject_path} not found!")

    with open(pyproject_path, "r") as f:
        doc = tomlkit.load(f)

    return doc


def write_pyproject(document: TOMLDocument, pkg_name: str | None = None) -> None:
    """Write a document to either a project or package pyproject file"""
    if pkg_name is not None:
        pyproject_path = Path("packages") / pkg_name / "pyproject.toml"
    else:
        pyproject_path = Path("pyproject.toml")

    with open(pyproject_path, "w") as f:
        tomlkit.dump(document, f)


def create_pyproject(
    pkg_name: str,
    version: str,
    description: str,
    build_dependencies: list[str] = [],
    runtime_dependencies: list[str] = [],
    unmanaged: bool = False,
    python: bool = False,
    python_requirements: bool = False,
) -> None:
    """Create package pyproject.toml for a new package"""
    config = tomlkit.document()

    project = tomlkit.table()
    project["name"] = pkg_name
    project["dynamic"] = tomlkit.array()
    project["dynamic"].append("version")
    project["description"] = description
    config["project"] = project

    dependency_groups = tomlkit.table()
    pyndev_nso = tomlkit.array()
    pyndev_nso.multiline(True)
    for dep in runtime_dependencies:
        pyndev_nso.append(dep)
    dependency_groups["pyndev-nso"] = pyndev_nso
    config["dependency-groups"] = dependency_groups

    build_system = tomlkit.table()
    requires = tomlkit.array()
    requires.multiline(True)
    requires.append("hatchling==1.28.0")
    requires.append("versioningit==3.3.0")
    for dep in build_dependencies:
        requires.append(dep)
    build_system["requires"] = requires
    build_system["build-backend"] = "hatchling.build"
    config["build-system"] = build_system

    tool = tomlkit.table()
    hatch = tomlkit.table()
    build = tomlkit.table()
    targets = tomlkit.table()
    wheel = tomlkit.table()
    force_include = tomlkit.table()

    nso_pkg = f"{pkg_name}.tar.gz"
    force_include[nso_pkg] = f"pyndev-nso/{nso_pkg}"

    wheel["force-include"] = force_include
    targets["wheel"] = wheel
    build["targets"] = targets

    hooks = tomlkit.table()
    custom = tomlkit.table()
    custom["path"] = "build_hook.py"
    hooks["custom"] = custom
    build["hooks"] = hooks

    hatch["build"] = build
    tool["hatch"] = hatch

    hatch_version = tomlkit.table()
    hatch_version["source"] = "versioningit"
    hatch["version"] = hatch_version

    versioningit = tomlkit.table()
    versioningit["default-version"] = "0.0.0"
    vcs = tomlkit.table()
    vcs["default-tag"] = "0.1.0"
    vcs["method"] = "git"
    tag2version = tomlkit.table()
    tag2version["method"] = {"module": "build_hook", "value": "nso_version"}
    tag2version["pkg-version"] = version
    format = tomlkit.table()
    format["distance"] = "{base_version}.{rev}"
    format["dirty"] = "{base_version}.{rev}.dirty"
    format["distance-dirty"] = "{base_version}.{rev}.dirty"
    write = tomlkit.table()
    write["file"] = "_version.py"
    versioningit["vcs"] = vcs
    versioningit["tag2version"] = tag2version
    versioningit["format"] = format
    versioningit["write"] = write
    tool["versioningit"] = versioningit

    pyndev = tomlkit.table()
    pyndev_build = tomlkit.table()
    pyndev_build["python-requirements"] = python_requirements
    pyndev_build["unmanaged"] = unmanaged
    pyndev["build"] = pyndev_build

    if not unmanaged and python:
        python_section = tomlkit.table()
        components = tomlkit.aot()  # Array of tables

        component = tomlkit.table()
        component["name"] = "main"
        # Convert pkg-name to pkg_name for project field
        component["project"] = (
            re.sub(r"_+", "_", re.sub(r"^[0-9_]+|[^a-zA-Z0-9_]", "_", pkg_name)).strip("_") or "module"
        )
        component["module"] = "main"
        component["application"] = "Main"

        components.append(component)
        python_section["components"] = components
        pyndev["python"] = python_section

    tool["pyndev"] = pyndev
    config["tool"] = tool

    write_pyproject(config, pkg_name)


def update_nso_version(nso_version: str, deps: list[str]) -> None:
    """Swap NSO version strings in package declarations"""
    for i, dep in enumerate(deps):
        deps[i] = re.sub(r"\+nso[^.]+\.[^.]+(\.[^.]+)?", f"+nso{nso_version}", dep)


def sync_pyproject(nso_version: str, pkg_name: str | None = None) -> None:
    """Synchronize pyproject.toml with .env state"""
    config = load_pyproject(pkg_name)

    if "build-system" in config and "requires" in config["build-system"]:
        update_nso_version(nso_version, config["build-system"]["requires"])

    if "project" in config and "dependencies" in config["project"]:
        update_nso_version(nso_version, config["project"]["dependencies"])

    if "dependency-groups" in config:
        for group_deps in config["dependency-groups"].values():
            update_nso_version(nso_version, group_deps)

    write_pyproject(config, pkg_name)


def update_pyproject(pkg_name: str, version: str) -> None:
    """Update pyndev pyproject.toml with pkg_name"""
    config = load_pyproject()

    dependencies = config.setdefault("project", {}).setdefault("dependencies", [])
    dependencies.multiline(True)
    if pkg_name not in dependencies:
        dependencies.append(pkg_name)

    sources = config.setdefault("tool", {}).setdefault("uv", {}).setdefault("sources", {})
    source_config = tomlkit.inline_table()
    source_config["workspace"] = True
    if pkg_name not in sources:
        sources[pkg_name] = source_config

    members = config.setdefault("tool", {}).setdefault("uv", {}).setdefault("workspace", {}).setdefault("members", [])
    members.multiline(True)
    pkg_member = f"packages/{pkg_name}"
    if pkg_member not in members:
        members.append(pkg_member)

    write_pyproject(config)


def remove_pyproject_package(pkg_name: str) -> None:
    """Removes a package reference from pyndev pyproject.toml"""
    config = load_pyproject()

    # tomlkit data is not quite the same as normal python types
    # cludgy loop to keep tomlkit happy while mutating the list
    dependencies = config.get("project", {}).get("dependencies", [])
    for i in range(len(dependencies) - 1, -1, -1):
        # fuzzy match pkg_name and ignore versions
        if pkg_name in dependencies[i]:
            del dependencies[i]

    sources = config.get("tool", {}).get("uv", {}).get("sources", {})
    if pkg_name in sources:
        del sources[pkg_name]

    members = config.get("tool", {}).get("uv", {}).get("workspace", {}).get("members", [])
    if f"packages/{pkg_name}" in members:
        members.remove(f"packages/{pkg_name}")

    write_pyproject(config)


def get_pyndev_description(pkg_name: str) -> str:
    """Pull out package description"""
    config = load_pyproject(pkg_name)
    description = config.get("project", {}).get("description", "")

    return description


def get_nso_dependencies() -> str:
    """Pull out project NSO package dependencies"""
    config = load_pyproject()
    deps = [dep.split("==")[0] for dep in config.get("project", {}).get("dependencies", [])]
    pyndev_nso = [dep.split("==")[0] for dep in config.get("dependency-groups", {}).get("pyndev-nso", [])]

    return deps + pyndev_nso


def get_pkg_dependencies(pkg_name: str) -> str:
    """Pull out package project.dependencies"""
    config = load_pyproject(pkg_name)
    pyndev_nso = [dep.split("==")[0] for dep in config.get("dependency-groups", {}).get("pyndev-nso", [])]
    nso_deps = get_nso_dependencies()

    return [dep for dep in pyndev_nso if dep in nso_deps]


def get_pkg_build_dependencies(pkg_name: str) -> str:
    """Pull out package build-system.requires"""
    config = load_pyproject(pkg_name)
    deps = [dep.split("==")[0] for dep in config.get("build-system", {}).get("requires", [])]
    nso_deps = get_nso_dependencies()

    return [dep for dep in deps if dep in nso_deps]


def get_pyndev_python_components(pkg_name: str) -> list[Component]:
    """Pull out package pyndev.python.components"""
    config = load_pyproject(pkg_name)
    components = config.get("tool", {}).get("pyndev", {}).get("python", {}).get("components", [])

    return [Component(**comp) for comp in components]


def get_pyndev_unmanaged(pkg_name: str) -> bool:
    """Pull out package pyndev.build.unmanaged"""
    config = load_pyproject(pkg_name)
    try:
        unmanaged = config["tool"]["pyndev"]["build"]["unmanaged"]
    except KeyError:
        error(f"[tool.pyndev.build] unmanaged config missing for {pkg_name} pyproject.toml")

    return unmanaged


def get_pyndev_requirements(pkg_name: str) -> bool:
    """Pull out package pyndev.build.python-requirements"""
    config = load_pyproject(pkg_name)
    try:
        requirements = config["tool"]["pyndev"]["build"]["python-requirements"]
    except KeyError:
        error(f"[tool.pyndev.build] python-requirements config missing for {pkg_name} pyproject.toml")

    return requirements
