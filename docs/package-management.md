\[[Contents](./README.md)\]

# Pyndev Package Management

The pyndev environment comes with a local `pkg_mgmt` python module that serves
the purpose of bridging the gap between a pure python and NSO package. It also
provides helper functions to improve the ergonomics of managing multiple
pyproject.toml files and name references. `pkg_mgmt` exposes it's entry points
as a series of scripts that can be referenced with `uv run`. Most if not all of
the scripts expect pyndev environment variables it is then expected that the
python scripts are wrapped in `just` commands to provide the necessary context.

> In most cases `pkg_mgmt` is perfoming updates that are required before `uv`
> can run it's normal management prcoesses. It is typical to see these commands
> run with the flag `uv run --no-sync` to prevent `uv` from trying to update
> the internal python state before the pyndev state update.

```
[project.scripts]
add_pkg = "pkg_mgmt.add_pkg:main"
publish_pkg = "pkg_mgmt.publish_pkg:main"
release = "pkg_mgmt.release:main"
rm_pkg = "pkg_mgmt.rm_pkg:main"
sync_pkg = "pkg_mgmt.sync_pkg:main"
```

| just command  | python script |
| ------------- | ------------- |
| just add-pkg  | add_pkg       |
| just publish  | publish_pkg   |
| just rm-pkg   | rm_pkg        |
| just sync-pkg | sync_pkg      |

> `release` is a pretty specialized tool that only works in the context of
> a gitlab repository with the gitflow workflow as described in
> [gitlab configuration](./gitlab-configuration.md) documentation.

## add-pkg

```
usage: add-pkg [-h] [-b NAME] [-d NAME] [--description DESCRIPTION] [-e] [-p] [--python-requirements] [-r NAME] [-t] [-u] [-v VERSION] package_name

Create NSO service packages and update project support files

positional arguments:
  package_name          Name of the package to create

options:
  -h, --help            show this help message and exit
  -b NAME, --build-dependency NAME
                        Specify a package that is a build dependency to the new package, can be declared multiple times for additional dependencies
  -d NAME, --dependency NAME
                        Specify a package that is a both a build and runtime dependency to the new package, can be declared multiple times for additional dependencies
  --description DESCRIPTION
                        Specify a package desription to be used in package meta data
  -e, --empty           Skips example files for a new package
  -p, --python          Create Python service skeleton
  --python-requirements
                        Install python requirements.txt in NSO package context
  -r NAME, --runtime-dependency NAME
                        Specify a package that is a runtime dependency to the new package, can be declared multiple times for additional dependencies
  -t, --template        Create template service skeleton
  -u, --unmanaged       Indicate the src package should not be modified by the python sync process, implies --empty
  -v VERSION, --version VERSION
                        Specify the package version at creation
```

This function is a macro to update the existing project pyproject.toml with a
new dependency while creating a skeleton for the actual package in
`./packages`. Many of the arguments are intented to pre-populate the
pyproject.toml configuration with seed data. This command can create demo files
much like the NSO internal `ncs-make-package` but with simpler options. The
seed files are jinja templates located at `pkg_mgmt/src/pkg_mgmt/examples/` and
the intention is your project customizes these files for custom needs versus
adding even more complex arguments to the funtion.

### Migrating an existing package to pyndev example

```
just add-pkg \
    -ep \
    -v 1.82.0 \
    bbl \
    -d esnet-common \
    -d port \
    -d routing-domain \
    -d bgp-neighbor \
    -r bridge \
    -r nokia-sros_nc-22.10-gen-1.0 \
    -r juniper-junos-nc-4.18 \
    --description 'Backbone link service'
```

In human terms we create a new package with python components but leave the
package empty as we will be copying existing code over. We declare a series
of dependencies with differing combinations of build and runtime needs. We set
the package version and description to existing values. Next, we would manually
copy the existing package in:

```
cp -r ../nid-repo/packages/bbl/* packages/bbl/src
```

The python components can be fairly complex depending on the packages history.
The `add-pkg -p` only creates a very generic single component. You will most
likely need to manually update the pyproject.toml components by hand.

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

### Adding a third party package

```
just add-pkg \
    -epu \
    --python-requirements \
    -v 1.2.0 \
    observability-exporter \
    --description 'Export NSO progress-trace using OpenTelemetry'
```

This creates an empty package that is unmanaged, we don't want to dynamically
update any NSO package files they are provided by Cisco and stable. In this
package's case it does require additional python packages pip installed into
the package itself. We declare the Cisco version and description for the
pyproject.toml meta data. Similarly copy the actual package in.

```
cp -r ../nid-repo/packages/observability-exporter/* packages/observability-exporter/src
```

## publish

One of the advantages of python packages is that they are tracked and managed
as an immutable hash, review the `uv.lock` file as an example. The current
implementation of pyndev makes a conscious choice in convenience over
efficiency in that a NSO package in continually rebuilt without much state
tracking of the actual package code. The NSO build process generates a new and
unique .tar.gz for every call to the build system. This creates an real world
issue where the python wheel has a constantly revolving door of a hash. Pyndev
treats the first publish version hash as the one true package and will ignore
new wheels with an updated hash but same version string. This behavior is
contrary to normal python tools included `uv publish`. For this reason there is
a custom python script to handle this package logic as described above.

## rm-pkg

This function is just a macro to delete the contents in `./packages/` and clean
up the top level pyproject.toml references.

## sync-pkg

This function is the foundation for dynamic file management in the pyndev
environment. The first step is scan pyproject.toml dependecies and synchronize
the `NSO_VERSION` value with the configurations. This allows the simple
variable to be the main driver for the project as a whole. The next step reads
the packages pyproject.toml configuration and udpates the python package
`build_hook.py` and `Dockerfile` files. This allows a developer to update the
configuration such as dependencies and have those propagated at build time.
Finally, if a package is `unmanaged = False` the script will regenerate the NSO
package files `package-meta-data.xml` and `src/Makefile`. These package updates
are considered preqrequisites to `uv sync` so that files are up to date prior
to any python builds.

### just build

While not strictly a python `pkg_mgmt` function, `just build` is a crucial step
for generating external and publishable python wheels. It is equivalent to the
builtin `uv build --wheel` command. This `uv` command runs serially for any or
all specified packages.

> `sync-pkg` will internally rebuild all local NSO packages in parallel. These
> builds are cached in the docker buildx caching system. Due to the dynamic
> file updates and this efficient build process, `sync-pkg` should be
> considered prerequisite to `just build` but is left decoupled for flexibility.

______________________________________________________________________

\[[Top](#pyndev-package-management)\]\[[Contents](./README.md)\]
