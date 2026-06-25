\[[Contents](./README.md)\]

# Pyndev Package Configuration

## Versioning

The pyndev environment is managing multiple NSO versions with active
development between a python wheel version and an internal NSO package version
so management of the version metadata becomes a central construct to pyndev. As
a first step all python package versions track the appropriate NSO version in a
local version annotation so that a developer is sure a given package was
compiled for the NSO version under test.

```
uv pip list
Package                           Version
--------------------------------- -----------------------------
arista-dcs-cli-5-30               5.30.7+nso6.6.3
bbl                               1.82.0+nso6.6.3.0
bfd                               1.82.0+nso6.6.3.0
bgp-neighbor                      1.85.0+nso6.6.3.0
```

Next we have the package version itself which pyndev synchornizes the python
version with the NSO version presented in the cli. Existing python versioning
tools bring in some additonal enhancements to a local developer environment.

```
arista-dcs-cli-5-30               5.30.7+nso6.6.3
bbl                               1.82.0+nso6.6.3.0fce640.dirty
bfd                               1.82.0+nso6.6.3.0fce640.dirty
bgp-neighbor                      1.85.0+nso6.6.3.0fce640.dirty
```

```
arista-dcs-cli-5-30               5.30.7+nso6.6.3
bbl                               1.82.0+nso6.6.3.76d8b7d
bfd                               1.82.0+nso6.6.3.76d8b7d
bgp-neighbor                      1.85.0+nso6.6.3.76d8b7d
```

As you can see packages can be in few different states based on the state of
the local repo. You can see a package version gets tied to a local commit that
has moved away from the `main` branch release tag. Then even when there are
uncommitted local changes the package gets annotated as `dirty`. This helps
facilitate preview environments and artifacts to be shared prior to an official
release.

This setup takes up a good chunk of a package's pyproject.toml:

```
[project]
name = "bbl"
dynamic = ["version"]
description = "Backbone link service"

[build-system]
requires = [
    "hatchling==1.28.0",
    "versioningit==3.3.0",
]

[tool.hatch.version]
source = "versioningit"

[tool.versioningit]
default-version = "0.0.0"

[tool.versioningit.vcs]
default-tag = "0.1.0"
method = "git"

[tool.versioningit.tag2version]
pkg-version = "1.82.0"

[tool.versioningit.tag2version.method]
module = "build_hook"
value = "nso_version"

[tool.versioningit.format]
distance = "{base_version}.{rev}"
dirty = "{base_version}.{rev}.dirty"
distance-dirty = "{base_version}.{rev}.dirty"

[tool.versioningit.write]
file = "_version.py"
```

The package is configured for a "dynamic" version and then relies on the python
build system and helper `versioningit` to track and setup the actual version.
There are a couple of edge case issuse when the git repo has just been
initialized or a package is brand new and not in git tracking. The
default-version and default-tag configurations handle these edge cases but are
largely unused in normal development with long running packages. We use git as
the source for local repo state but since this environment acts like a mono
repo with independent package versions from the project version then we must
manually set and and managed the `base_version` with the pkg-version parameter.
The actual version format can be modified and updated per specific environments
requirements.

> The python package version is synchronized to the NSO package version minus
> the local `+nso6.6.3` version tag. The `+` character is illegal in the
> package-meta-data.xml schema so you should verify any modifications are
> likewise supported.

The remaining config is just showing the supporting logic for version discovery
and synchronizing.

## Pyndev configuration

```
[tool.pyndev.build]
python-requirements = false
unmanaged = false
```

Relating back to the versioning topic, if a package is `unmanaged = true` then
the NSO package-meta-data.xml file is not modified and requires manual updating
and synchronizing with the `pkg-version` configuration. The python version is
still dynamic per the topic above for development uses. There is quite a bit
more context for the `unmanaged` parameter, for the full scope see
[package-management](./package-management.md) documentation.

The `python-requirements` parameter determines if the NSO package has a
separate requirements.txt file to install third party python packages inside of
a NSO package itself. As of NSO version 6.6.x the recommended approach is to
simply pip install dependencies into the package's `python/` directory and
NSO's python-vm handling will keep different packages python envs isolated.
This project is setup to support this style. It's not much effort to augment
the pyndev code to support true venv installs during package build if that
is necessary. It is expected that the requirements.txt resides in the NSO
package's own `src/` directory.

## Dependencies

Pyndev package pyproject.toml supports two kinds of dependencies. In either
case since uv is managing the project as workspace NSO packages can be
declared much more simply and uv will find the source based on the top level
pyproject.toml configuration for sources and inherit private repository
settings.

### Build Dependencies

```
[build-system]
requires = [
    "hatchling==1.28.0",
    "versioningit==3.3.0",
    "esnet-common",
    "routing-domain",
    "bgp-neighbor",
    "port",
]
```

This follows the standard python patterns for build dependencies. For the NSO
package case this declaration kicks a bit more logic in the the pkg-sync
script. Package specific Dockerfiles are updated to include dependency source
yang and the package Makefile is dynamically generated to include these in the
yang path. These actions satisfy the idea of a NSO build time dependency for
sharing yang models. The NSO as a python package construct ensures that
dependencies have to successfully build themselves prior to the local
build thus isolating failures a bit more cleanly.

### Runtime Dependencies

```
[dependency-groups]
pyndev-nso = [
    "esnet-common",
    "nokia-sros_nc-22.10-gen-1.0",
    "port",
    "juniper-junos-nc-4.18",
    "routing-domain",
    "bgp-neighbor",
    "bridge",
]
```

These dependencies are mapped the NSO package's package-meta-data.xml file's
required-package list. This ensures the packages dependency tree during package
loading and allows the sharing of intra package python modules per normal NSO
functions. This dependency group does not really impact the overall python
workspace and thus are truly just runtime artifacts.

> Similar to versioning, when a package has `unmanaged = true` configuration
> the NSO package files such as the package-meta-data.xml and the Makefile are
> not updated or dynamically generated.

## Python Components

If it hasn't been made clear the package-meta-data.xml is being dynamically
generated in it's entirety. This means we will typically also declare our NSO
package python components in the pyproject.toml.

```
[[tool.pyndev.python.components]]
name = "main"
project = "bbl"
module = "main"
application = "Main"

[[tool.pyndev.python.components]]
name = "upgrade"
project = "bbl"
module = "main"
upgrade = "UpgradePortList"
```

You can configure multiple components that match up the NSO component schema.
The pkg_mgmt package-meta-data.xml.j2 template is the best source to see the
needed structure for a python-class-name value. This above configuration maps
to:

```
  <component>
    <name>main</name>
    <application>
      <python-class-name>bbl.main.Main</python-class-name>
    </application>
  </component>
  <component>
    <name>upgrade</name>
    <upgrade>
      <python-class-name>bbl.main.UpgradePortList</python-class-name>
    </upgrade>
  </component>
```

______________________________________________________________________

\[[Top](#pyndev-package-configuration)\]\[[Contents](./README.md)\]
