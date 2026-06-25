\[[Contents](./README.md)\]

# Just Recipes

## add-pkg

Create a new NSO package for development

### arguments

- +args

This calls the pkg_mgmt.add_pkg script. You can pass multiple arguments as
defined by the script help. See [package management][pkg-mgmt] for details.

## auto-test

Run NSO container in background and run all test, auto CI test command

## build

Build local packages, default is '--all-packages', optionally specify one or more package names to build serially

### arguments

- \*args

This calls `uv build` for one or more packages depending on args. Creates a
python wheel per package in project root `./dist` for publishing. `uv build`
runs serially but with build caching you can optimize this by issuing a
`just sync` first that runs internal builds in parallel.

## build-nso-image

Build a NSO prod image with local packages

### arguments

- version='pyndev-nso'

This generates a docker image based on the cisco-nso-prod image. This is carry
over from NID in that the end result should be a runable container of NSO. Will
need to customize the configuration in `./nso/prod` or may not be needed at
all.

## cli

Enter the NSO cli as user admin

### arguments

- service='nso'

Helper command to hop into the ncs_cli via `docker compose exec`.

> With the defaults the service parameter can be ignored but if your compose is
> modified to support multiple local instances of NSO, a virtual lab instance
> for example, then you have a choice to select an instance.

## down

Tear down a local instance of NSO

### arguments

- service='nso'

> With the defaults the service parameter can be ignored but if your compose is
> modified to support multiple local instances of NSO, a virtual lab instance
> for example, then you have a choice to select an instance.

## init

Initialize the workspace

Run this for a new clone of the project or if the NSO version is updated.
Removes existing .venv so subsequent `just sync` is also required after this
command.

## lint

One off lint everything, developers would typically rely on hooks running
during the appropriate git stage and this is more for CI or troubleshooting.

## list

List all available commands, default command to offer simple help if user only
types `just`.

## load

### arguments

- env='dev'
- service='nso'

This command facilitates seeding an NSO instance with initial data. The `env`
argument is a directory that sits in the `./nso/` directory. It currently
supports two files, `config.xml` and `capabilities.txt`. The `config.xml` file
is loaded via `ncs --mergexmlfiles` and capabilities.txt is way to run ncs_cli
commands one per line. In the demo data, device capabilities are set with the
`copy-capabilities` feature to ensure working device yang model profiles
created in the `config.xml`.

> With the defaults the service parameter can be ignored but if your compose is
> modified to support multiple local instances of NSO, a virtual lab instance
> for example, then you have a choice to select an instance.

## load-yang

Copy yang from NSO_VERSION build image to project. Part of the `just init` to
facilitate linting and any other development support for package yang
development.

## publish

Publish local packages, default is all nso packages, optionally specify a wheel
package name or general prefix

### arguments

- package=''

The `package` argument supports a fuzzy matching to pick up a subset of many
packages or just one. It should loosely match a prefix,
`uv publish ./dist/[package]*` with some extra python normalization, eg.
converting `-` to `_`.

## re-deploy

Issue a ncs_cli 'request packages package [package] redeploy' (no package sync)

### arguments

- target='all'
- service='nso'

This hyphenated command `re-deploy` represents the actual NSO
`request packages package [package] redeploy`. With this version no other
side-effects such as packaging syncing or updates are ran. This command is more
for troubleshooting and separating concerns. The expected user ran command is
the non-hyphenated `redeploy`. The argument `target` will accept `all` or one
specific package name. The NSO redeploy command is a serial operation so
specifying the package under test will be more effecient. NSO redeploys restart
the package specific python process and reloads the package templates. These
updates are quick and simple for NSO to complete.

> With the defaults the service parameter can be ignored but if your compose is
> modified to support multiple local instances of NSO, a virtual lab instance
> for example, then you have a choice to select an instance.

## redeploy

Sync packages and redeploy NSO packages

### arguments

- target='all'
- service='nso'

This redeploy command includes a `just sync` to ensure all package files are
up to date and synchronized prior to issueing the redeploy. This is standard
command for developers doing hot redeploys on their local instance of NSO. The
argument `target` will accept `all` or one specific package name. The NSO
redeploy command is a serial operation so specifying the package under test
will be more effecient. NSO redeploys restart the package specific python
process and reloads the package templates. These updates are quick and simple
for NSO to complete.

> With the defaults the service parameter can be ignored but if your compose is
> modified to support multiple local instances of NSO, a virtual lab instance
> for example, then you have a choice to select an instance.

## reload

Sync packages and reload all NSO packages

### arguments

- service='nso'

This command includes a 'just sync' to ensure all package files are up to date
and synchronized prioer to issueing a `request packages reload force`. Package
reloading is required for updates to the yang models or changes taht would
otherwise trigger an upgrade in NSO. This operation can take some time
depending on the changes and the amount of other NSO packages loaded.

> With the defaults the service parameter can be ignored but if your compose is
> modified to support multiple local instances of NSO, a virtual lab instance
> for example, then you have a choice to select an instance.

## rm-pkg

Remove a NSO package from the project

### arguments

- package

This command is part of pyndev's package management. It will delete the
contents of `./packages/[package]` and update the top level pyproject.toml to
ensure consistency in the uv workspace.

## shell

Enter the NSO container bash shell via `docker compose exec`

### arguments

- service='nso'

> With the defaults the service parameter can be ignored but if your compose is
> modified to support multiple local instances of NSO, a virtual lab instance
> for example, then you have a choice to select an instance.

## sync

Sync packages and environment

### arguments

- quiet=''

This command combines a pyndev package management sync_pkg with normal
`uv sync` operations. The `sync_pkg` updates any dynamically generated package
files. Due to the fact that NSO packages are not really python we must issue a
reinstall with the `uv sync` to pick up all updated files.

## sync-pkg

pyndev sync managed package files, updates dynamically generated files based on
individual package pyproject.toml configurations. Typically ran under the
`just sync` umbrella and not often called in isolation.

## test

Run NSO tests, this will need be setup and largely implementation specific far
as arguments go.

## up

Bring up a local instance of NSO

### arguments

- service='nso'

Defaults with the compose `--watch` feature to enable package update
sychronization and "hot" updating the local NSO instance.

> With the defaults the service parameter can be ignored but if your compose is
> modified to support multiple local instances of NSO, a virtual lab instance
> for example, then you have a choice to select an instance.

______________________________________________________________________

\[[Top](#just-recipes)\]\[[Contents](./README.md)\]

[pkg-mgmt]: ./package-management.md
