# Pyndev Development Environment

Full reference documentation for pyndev internal tooling

## Table of Contents

- [Environment](#environment)
  - [Just Recipes](./just-recipes.md)
  - [Gitlab Setup](./gitlab-configuration.md)
- [Packages](#packages)
  - [Package Configuration](./package-configuration.md)
  - [Package Management](./package-management.md)
- [Appendix](#appendix)
  - [Multi Arch Docker Images](./container-registry-setup.md)

## Overview

Pyndev is a NSO development environment centered around the concept that NSO
packages can be built, managed, and distributed as if they were a python wheel.
The project uses `uv` and modern and extremely fast python package and project
manager. The project management is simplified through the use of the `just`
command runner. `just` follows the patterns of a `make` recipe while avoiding
a full build system's complexity and annoyances.

## Environment

The project's root [README.md](../README.md) gives a pretty good explanation
for dependencies required to work in pyndev. However it does gloss over some
of the internal underpinings that represent the full dev environment.

### `.env`

The top level project file defines two basic variables and tracks them in git
version control.

- `NSO_VERSION`

This is the mainline version of Cisco NSO that are wanting to develop against.
Artifacts such as yang models can be version specific and a developer should
always re-init the environment with `just init` whenver this variable is
modified.

- `REGISTRY`

This variable tracks the source for both a `prod` and `build` NSO image.
Current project is based on and tested with Cisco's officially published and
released containers. This variable is not used for any type of container
publishing and requires other explicit configuration.

### `.env.local`

This is a file that is not tracked in git version as it's purpose is to house
personal secrets for the project.

- `UV_INDEX_PRIVATE_USERNAME`
- `UV_INDEX_PRIVATE_PASSWORD`

These variables are for uv pip pull functions where `PRIVATE` matches the
top level pyproject.toml private index name value.

- `UV_PUBLISH_TOKEN`

This is an additional variable required for authentication to push local python
wheels to the private registry.

### Just

`just` is a convenient tool to alias multiple commands or long drawn out flags
and arguments. It also serves as a convenient way for controlling the
environment. If you inspect the top level `justfile` two things highlight this
behavior.

```
set dotenv-load := true
```

With this configuration the local `.env` variables are always present in the
context where "recipes" are ran. At the time of this writing `just` only
supports loading a single `.env` file so the second configuration is in
individual recipes that need the local secrets:

```
# Initialize the workspace
init:
  #!/usr/bin/env bash
  set -euo pipefail
  if [ -f .env.local ]; then
    source .env.local
  fi
```

The commands are wrapped in a bash script that can then source the `.env.local`
as needed. This can be simplified after a couple of open PRs and conversations
are resolved around loading multiple different `.env` files.

The final trick with `just` is that it can recurse back from any child
directory to find the top level `justfile` and run commands from the project's
root context. This makes is convenient if a developer is working within a NSO
package directory the available `just` commands all work with no impacts to the
working directory of the individual commands they all run as if they were from
the project root.

For detailed context of the currently defined `just` commands see the
[just-recipe](./just-recipes.md) documentation.

### CI

Some other sought after features such as managing multiple versions of NSO in
the same project are handled directly in the CI pipelines. The current version
of pyndev was developed on Gitlab and it's internal CI systems. As an example,
`.gitlab-ci.yml.example` has been documented with explanations.

- [Gitlab Setup](./gitlab-configuration.md)

## Packages

Packages are split into two subsections. Package configuration is all about the
pyproject.toml components and how they impact the building of a NSO package.

- [Package Configuration](./package-configuration.md)
- [Package Management](./package-management.md)

### Modular pyndev workspace

pyndev facilitates working with packages in a modular fashion that supports
both monorepo or polyrepo archetectures. pyndev utilizes docker buildx and uv
caching for efficient builds. In general this works really well but there are
some real world limitations. The fact that NSO packages are not pure python
code means uv cannot detect per package modifications with it's internal build
system. To overcome this pyndev's `just sync` will rebuild all packages in the
current workspace with each synchronization call. While complex operations such
as yang compilation are cached simple operations such as file copying and I/O
become cost prohibitive in large a workspace.

While design of the pyndev repositories are largely up to the user, here are
some common boundaries to break up packages into multiple repositories:

- NEDs, these packages are typically developed less frequently with large
  amounts of internal yang schema
- Packages with a large amount of small files that rarely change. A example of
  this case is Cisco's provided "observability-exporter" package.
- Library packages or resources that don't change with the same frequency as
  other dependent service packages.

> Many of the packages that meet the criteria for breakout into a separate
> workspace fall in the "unmanaged" category of package configuration. A simple
> architecture is having one service repository supported by a single external
> "unmanaged" repository.

## Appendix

A primary motivator for pyndev as a project was the support for a multi arch
development environment for NSO. As a predicated we need NSO base images
published to support this feature. A detailed guide for deploying Cisco's
official images supporting Apple Silicon and x86 hardware can be found here:

- [Multi Arch Docker Images](./container-registry-setup.md)

______________________________________________________________________

\[[Top](#pyndev-development-environment)\]
