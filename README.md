# Pyndev

Python wrapped NSO development environment

## Getting Started

### Dependencies

- Cisco NSO

  pyndev uses Cisco's official NSO containers both "build" and "prod". This
  environment is built with the context that NSO runs as a non-root user which
  was introduced in NSO 6.5 and thus is the minimally supported version of NSO.

- Docker

  The fundamental building block of this environment is containerization. It is
  assumed you have a registry setup with any official Cisco NSO build and prod
  images already present for the versions declared in this project. CI and
  testing may have additional setup and conditions. The developer should have
  access to readily pull images prior to any project commands, eg.

  ```
  docker login container-registry.example.com
  ```

  This project leans heavily into modern docker plugins and features. Tested
  with:

  - buildx v0.26.1
  - Compose version v2.39.1

  Generally these are available in updated runtimes such as Docker Desktop
  and Orbstack.

- uv python manager

  This project utilizes the concept of a python wheel as a means of
  distributing and managing NSO packages and respective code. This model is
  facilitated by the use of of `uv` as the project manager. uv provides first
  class support for workspaces, managing and running tooling, and effecient
  caching and speed. This provides extended support for NSO package service
  logic written exlusively with python components. uv documentation and
  installation instructions can be found [here][uv].

- Install "just" command line runner in your environment.

  just documentation and installation instruction can be found
  [here][just]. Day to day work in this environment should consist of fairly
  straightforward commands and tools but often we need to chain many commands
  together or pass lots of special options as flags. `just` is a tool that
  allows defining these common commands into a make like "recipe" simplifying
  these long but repetitive commands. The recipes should be thought of as
  aliases and should be mostly self documenting in the local `justfile`.

- pre-commit

  This project uses pre-commit hooks to manage linting. uv provides a means for
  installing and managing the pre-commit environment if needed:

  ```
  uv tool -q install pre-commit
  uv tool update-shell
  ```

  With pre-commit available one can do one off checks with:

  ```
  just lint
  ```

  To have these hooks run automagically at the recommended stage of "pre-push":

  ```
  pre-commit install --hook-type pre-push
  ```

### Local Development

- `just init`

  This command installs project dev dependencies and other setup. This
  re-initializes the project with a clean .venv and should be ran whenever
  the `NSO_VERSION` environment variable is updated.

- `just sync`

  This command will update and build all locally defined packages and pull
  in any remote packages. At this point the .venv should be populated with
  with all declared NSO packages and needs to be ran at least once before
  NSO will run locally.

- `just up`

  This will bring up a local `prod` instance of NSO with the local .venv NSO
  package directory being sync'd. This utilizes the Docker compose `watch`
  feature to handle synchronization between .venv and NSO runtime packages. The
  intention here is to have an interactive environment that supports hot
  reloading of NSO packages for rapid development and feedback.

  > Watch does require running the NSO process in the foreground and it is up
  > to the developer to monitor when the container is fully up and healthy.

  A few interfactive commands:

  - `just redeploy`

    This command runs `just sync` to rebuild packages with any recent
    modifications and then issues a `request packages package redeploy` inside
    the NSO cli. With no arguments all packages are redeployed but a single
    package name can be passed to the `just redeploy [package]` command to
    limit the scope similar to `request packages package [package] redeploy`.
    Redeploy is useful for applying updates to either templates or python code
    but otherwise do not require a system or package upgrade.

  - `just reload`

    This command runs `just sync` to rebuild packages with any recent
    modifications and then issues a `request packages reload force` command.
    NSO does not support reloading individual packages so this is a global
    command with no package arguments. Reload is useful for applying updates
    to yang files or other changes that require NSO system udgrades.

  - `just test`

    If your test system supports API based integration tests, these can now
    be ran against the local instance of NSO.

- `Ctrl-C` and `just down`

  The live environment can be interrupted with `Ctrl-C` and then the docker
  environment can be cleaned up with `just down`.

For more information on just commands, you can review the [complete justfile
documentation][justfile_doc].

## Dev Environment Overview

This is a summary explanation of the pyndev NSO development environment. For
comprehensive documentation refer to the
[pyndev reference documentation][reference].

### Configuration

The project is managed as a `uv` workspace with multiple packages. The
configuration is managed in the top level pyproject.toml file in fairly normal
pythonic declarations.

- dev dependencies

  pyproject.toml

  ```
  [dependency-groups]
  dev = [
      "ncs_py3",
      "pkg_mgmt",
      "ruff>=0.14.13",
      "pyang>=2.7.1",
      "mdformat>=1.0.0",
      "mdformat-gfm>=1.0.0",
  ]
  ```

  uv will manage these packages along with normal dependencies during sync
  operations. Having an explicit group also allows us to install these with the
  `just init` stage.

  - pkg_mgmt

    pkg_mgmt is a local python package that contains specialized tooling to
    handle the pecularities of a NSO package wrapped in a python wheel. Details
    will be pointed out throughout the documentation but these tools need to be
    installed at the init stage and remain available for all additional
    project operations.

- private python indexes

  pyproject.toml

  ```
  [[tool.uv.index]]
  name = "private"
  url = "http://interal-pypi"
  publish-url = "http://internal-pypi"
  explicit = true
  ```

  While functional and useful, wrapping NSO packages into a wheel is still a
  bit of an unorthodox binary distribution method and probably violates some end
  user agreement terms if you were to use public pypi. You should create and
  use private indexes for NSO package distribution.

  > This project uses environment variables to store authentication secrets for
  > private pypi access. An example file `./.env.local.example` should be
  > updated with a developers personal secrets and saved as `./.env.local`.
  > The just command runner will load this into it's context for all uv
  > commands and no other overhead such as sourcing or variable management is
  > required. The non-example filename is in `./.gitignore` to reduce the
  > chance for secret publishing.

- workspaces, packages, and sources

  pyproject.toml

  ```
  dependencies = [
      "interface",
  ]

  [dependency-groups]
  dev = [
      "pkg_mgmt",
  ]

  [tool.uv.sources]
  pkg_mgmt = {workspace = true}
  interface = {workspace = true}
  "arista-dcs-cli-5.30" = {index = "private"}

  [tool.uv.workspace]
  members = [
      "pkg_mgmt",
      "interface",
  ]
  ```

  Local workspace NSO packages are added the top level pyproject.toml
  dependencies array in addition to the uv workspace configuration. uv controls
  where the workspace looks for the source of any specific package with sources
  configuration. In this example, pkg\_mgmt is local pure python package listed
  as a dev dependency, interface is local NSO package, and the arista NED is a
  remote NSO package available on our private index.

  > The pkg\_mgmt helper utilities `add-pkg` and `rm-pkg` automatically manages
  > these parent pyproject.toml package declarations. See
  > [package-management docs][package-mgmt] for details.

- Modular pyndev environments

  pyndev supports a single workspace with multiple packages but also can use
  external repositories as a source of packages. For more information see the
  [modular pyndev workspace][modular] section in the documentation.

  pyproject.toml

  ```
  [dependency-groups]
  pyndev-nso = [
      "arista-dcs-cli-5.30==5.30.7+nso6.6.3",
  ]
  ```

  The pyndev-nso dependency group is a special placeholder for pyndev NSO
  packages that are external to the current workspace. This separate group is
  needed for the pyndev specific synchronization process and this array is
  manually populated.

- NSO_VERSION

  pyndev supports managing multiple NSO versions in python through the use of
  PEP 440 "local version identifiers". During build all NSO packages are
  appended with the version that was used for the package build. Internally
  this is all driven by the top level `.env` variable `NSO_VERSION`. If your
  repository only supports one version of NSO this identifier can be ignored
  and left off of dependency version matching. If you are concurrently
  developing towards multiple NSO releases the full identifier should be
  specified in the version.

  > As previously mentioned, the pkg\_mgmt tooling does some special handling
  > for the NSO project. One of the tricks that impacts the top level
  > pyproject.toml is that during a `just sync` the `NSO_VERSION` variable is
  > read and any NSO versions are updated to be synchronized with the declared
  > project version. Eg. the arista NED above has a local version tag specific
  > to set NSO version and a sync function will update that package version
  > automatically to ensure consistency.

  > Anytime the NSO_VERSION is updated locally the project needs to be
  > re-initialized with a `just init` and a `just sync` to setup to the proper
  > context.

  This feature can be utilized in CI platforms with tools such as Github's
  strategy matrix and Gitlabs parallel matrix. This skeleton has a
  `.gitlab-ci.yml.example` at the root demonstrating this for two NSO versions.

### Packages

NSO packages are a combination both python and NSO components

Directory tree

```
packages
├── interface
│   ├── _version.py
│   ├── interface.tar.gz
│   ├── build_hook.py
│   ├── CHANGELOG.md
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── src
│   ├── README.md
│   └── target
└── bfd
    ├── _version.py
    ├── bfd.tar.gz
    ├── build_hook.py
    ├── CHANGELOG.md
    ├── Dockerfile
    ├── pyproject.toml
    ├── src
    ├── README.md
    └── target
```

The traditional NSO package with it's own meta data and structure are placed
into the top level package src.

The configuration for a package is represent by the following files.

```
pyproject.toml
```

The following files are build artifacts that typically ignored from version
control.

```
_version.py
[package].tar.gz
target/
```

- pkg_mgmt.sync_pkg

  Based on different parameters for dependencies and settings declared in the
  package pyproject.toml the following files are dynamically generated.

  ```
  build_hook.py
  Dockerfile
  ```

Package configurations get complex pretty fast for complete documentation refer
to the [full package configuration reference][package-config]

## Contributing

This project is a skeleton intended to be forked and customized to fit your own
needs. With that in mind, contributions should focus on improving the core
logic of the wrapper rather than any environment specific details.

Please keep IDE configurations, editor settings, and other environment specific
requirements out of the skeleton itself. Alternatively, these optimizations can
be submitted as example files and documentation describing such specifics are
very much welcome. Pyndev should help others adapt the project without baking
assumptions into the base.

When opening a pull request, aim to keep changes general-purpose and broadly 
applicable so the skeleton stays clean and easy to fork.

## Copyright Notice

pyndev Copyright (c) 2026, The Regents of the University of California,
through Lawrence Berkeley National Laboratory (subject to receipt of
any required approvals from the U.S. Dept. of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software,
please contact Berkeley Lab's Intellectual Property Office at
IPO@lbl.gov.

NOTICE.  This Software was developed under funding from the U.S. Department
of Energy and the U.S. Government consequently retains certain rights.  As
such, the U.S. Government has been granted for itself and others acting on
its behalf a paid-up, nonexclusive, irrevocable, worldwide license in the
Software to reproduce, distribute copies to the public, prepare derivative 
works, and perform publicly and display publicly, and to permit others to do so.

[just]: https://just.systems/man/en/introduction.html
[justfile_doc]: ./docs/just-recipes.md
[package-config]: ./docs/package-configuration.md
[package-mgmt]: ./docs/package-management.md
[reference]: ./docs/README.md
[modular]: ./docs/README.md#modular-pyndev-workspace
[uv]: https://docs.astral.sh/uv/getting-started/installation/
