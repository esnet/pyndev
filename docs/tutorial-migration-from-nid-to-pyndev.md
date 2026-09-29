# Migration from NID to Pyndev

## Setup

### Source Environment

```
source
├── esnet-nso
├── esnet-nso-neds
├── nso-docker
├── nso-observability-exporter
└── nso-phased-provisioning
```

ESnet's NID environment consisted of many parts absed on the NSO in docker
skeleton. `nso-docker` repo is the direct NID fork for underlying image and
version support. `esnet-nso` is the core business logic and service packages
for ESnet network automation. `esnet-nso-neds` contains all of the device NEDs
specific to the ESnet network. `nso-observability-exporter` and
`nso-phased-provisioning` are Cisco provided third party packages placed into
NID skeletons for easy inclusion to the core `esnet-nso` project.

### Git Handling

ESnet is using internal gitlab to maintain and develop all NSO projects. There
are few options for migrating the NSO repositories or even updating the
existing repository directly. In this case, ESnet choose to do a project export
from existing `esnet-nso` and `esnet-nso-neds` projects and then created new
repositories based on the exports. This process carries over all branches,
references, gitlab settings, and gitlab data while creating a new environment
to migrate to the pyndev stucture.

### Target Environment

```
target
├── esnet-nso
├── esnet-unmanaged
├── nso-migration
└── unmanaged-migration
```

`esnet-nso` and `esnet-unmanaged` are just an independent copies of the 
original repositories as described above. The older third party source repos
will be consolidated into the unmanaged repo. The `*-migration` repos are forks
of the pyndev skeleton to build out pyndev specific structure and artifacts to
be copied into the existing repos in a later step.

> The migration repositories are for local staging and will be later tossed out

#### migration branches

```
cd target/esnet-nso
git switch -c pyndev-migration
cd ../esnet-unmanaged
git switch -c pyndev-migration
cd ../..
```

## Target pyndev staging

To start, we will build out the pyndev migration repos.

### esnet-unmanaged

Initialize the uv environment:

```
cd target/unmanaged-migration
just init
```

The init command will install pyndev dependencies and the local `pkg-mgmt`
cli utilities. With this installed we can now run the `add-pkg` command via
`just`.

```
just add-pkg -h
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

This command will need to be adapted and ran against all third party packages
expected to live in the `nso-unmanaged` repository.

source:

```
source/esnet-nso-neds/packages
├── arista-dcs-cli-5.30
├── ciena-waveserver-nc-2.2
├── cisco-ios-cli-6.109
├── cisco-nx-cli-5.27
├── infinera-g30-nc-4.7
├── infinera-g40-nc-6.1
├── juniper-junos-nc-4.18
├── juniper-junos-nc-4.19
├── nokia-sros_nc-24.10.r5-gen-1.0.25
└── nokia-sros_nc-25.10.r7-gen-1.0.33
source/nso-observability-exporter/packages
└── observability-exporter
source/nso-phased-provisioning/packages
└── phased-provisioning
```

Example:

```
just add-pkg -u -v 5.30.7 --description 'NED package for the Arista DCS 7100 Series' arista-dcs-cli-5.30
```

#### -u, --unmanaged

This flag is special to pyndev in that it tells the workspace that the NSO
package code is entirely manually and untouched by pyndev helpers. NEDs and
third party packages will largely not be compliant with the pyndev templates
and this configuration puts more responsibility on the developer with more
control over the file such as `package-meta-data.xml`. This configuration is
written to the package's `pyproject.toml` and can later be adjusted as needed.

> `add-pkg` can create a lot of boilerplate files and example files for a
> complete package similar to Cisco's `ncs-make-package`. The -u or -e, --empty
> flags skips these files for the cases were we merging into fully functional
> packages.

#### -v, --version and --description

These values are pulled directly from a package's `package-meta-data.xml` and
these values are written to the package's `pyproject.toml`.

#### -p, --python and --python-requirements

The -p, --python flags indicate a package will have python components. For
unmanaged packages this is largely ornamental but is required to then allow the
--python-requirements flag that is more useful in this context. This flag is
associated with packages that require installing python packages directly into
NSO package. This configuration is written into the `pyproject.toml` and from
there it is used during the build to run additional pip commands during build.
pyndev follows the recommendation from NSO documentation from NSO 6.6 and
greater that installs dependencies directly into the NSO packages 
`packages/[pyndev-package-name]/src/python/` that is then unique to each
packages python process (NSO Python VM).

> While not documented this method has been tested to function on NSO 6.5.x
> with the builtin python startup scripts.

The third party `observability-exporter` follows this pattern:

```
just add-pkg -up --python-requirements -v 1.8.0 observability-exporter --description 'Export NSO progress-trace using OpenTelemetry'
```

#### NSO package result

```
packages
├── arista-dcs-cli-5.30
│   ├── build_hook.py
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src
│       └── src
└── observability-exporter
    ├── build_hook.py
    ├── Dockerfile
    ├── pyproject.toml
    └── src
        └── src
```

The package's top level directory is considered the "python" package. The
artifacts generated are for pyndev's build system or general python management.
The `build_hook.py` and `Dockerfile` are dynamically generated based on the
configuration present in `pyproject.toml`. The `pyproject.toml` file is
generated for a new package but then is expected to be manually maintained
during the life cycle of the package. It is intended for organizational level
documentation such as READMEs and CHANGELOGs be kept in the top level package
directory. The top level `src` will contain the full NSO package itself. The
nested `src` is a reflection of the fact that NSO packages have that name in
their own structure. With NEDs and third party packages this nested structure
supports keeping vendor documentation segmented from the operators
documentation.

> pyndev expects that a package name matches the corresponding directory name.
> Running through the `add-pkg` command will ensure this in the migration
> directory but you will want to verify the target packages conforms to this
> structure.

#### pyndev workspace result

pyndev has parent level workspace `pyproject.toml` that manages the project as
any ordinary `uv` python workspace. With many packages there becomes quite a
bit of boilerplate configuration to track. The cli functions from `pkg-mgmt`
all typically interact with the parent `pyproject.toml` to do this boilerplate
as part of the life cycle.

Automated population of configuration based on the above `add-package`
commands:

```
dependencies = [
    "arista-dcs-cli-5.30",
    "observability-exporter",
]

[tool.uv.sources]
pkg_mgmt = {workspace = true}
"arista-dcs-cli-5.30" = {workspace = true}
observability-exporter = {workspace = true}

[tool.uv.workspace]
members = [
    "pkg_mgmt",
    "packages/arista-dcs-cli-5.30",
    "packages/observability-exporter",
]
```

> Without actual package code the pyndev environment is non functional but we
> a file structure to start modifying the real repository towards so that we
> can copy in the pyndev artifacts. The tutorial expects that all "unmanaged"
> packages are now populated in the skeleton via `add-pkg`.

### esnet-nso

The setup for the core business logic services follows the same pattern as the
unmanaged repository but introduces a few more flags to customized the NSO
package build.

Initialize the uv environment:

```
cd ../nso-migration
just init
```

An example package add:

```
just add-pkg -ep -v 1.82.0 \
  -d esnet-common \
  -d port \
  -d routing-domain \
  -b bgp-neighbor \
  -r bridge \
  -r nokia-sros_nc-22.10-gen-1.0 \
  -r juniper-junos-nc-4.18 \
  --description 'Backbone link service' \
  bbl
```

#### -e, --empty

This flag is very similar the -u unmanaged in that it squelches the creation
of example files but leaves the package "managed" where pyndev will dynamically
update NSO package files such as `package-meta-data.xml` and the `Makefile`.

#### -b, --build-dependency and -d, --dependency and -r, --runtime-dependency

pyndev can manage NSO package dependencies. With NSO this comes in two classes,
run time and build time dependecies. Build time dependencies are essentially
yang dependencies where a package imports another packages yang definitions and
are needed to be present at the time of NSO yang compiling. Run time
dependencies match up to NSO's `package-meta-data.xml` `required-package` list.
This list provides template namespace references and python code sharing
between NSO packages. These declarations are written to the NSO packages
`pyproject.toml` file in unique ways. The `-d, --dependency` flag is just a
short hand for decaring both run time and build at the same time.

##### Build time pyproject.toml

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

To take advantage of the inherent `uv` build tools the build time dependencies
are placed in the python native build dependency structure.

> A common pitfall with NSO yang dependencies is nested relationships. In this
> example `bgp-neighbor` is not used directly in `bbl` but is chained from 
> imports eg. `bbl` needs `routing-domain` which then needs `bgp-neighbor`. This
> constaint comes from NSO ncsc and is independent of `pyndev`.

##### Run time pyproject.toml

```
[dependency-groups]
pyndev-nso = [
    "esnet-common",
    "nokia-sros_nc-24.10.r5-gen-1.0.25",
    "nokia-sros_nc-25.10.r7-gen-1.0.33",
    "port",
    "juniper-junos-nc-4.19",
    "routing-domain",
    "bridge",
]
```

Since the run time dependencies are exclusive to pyndev and NSO package use, a
custom dependency-group is created to track these dependencies.

#### -p, --python

For managed packages the python declaration does quite a bit more work under
the hood. This writes a generic component to the pacakges' `pyproject.toml`:

```
[[tool.pyndev.python.components]]
name = "main"
project = "bbl"
module = "main"
application = "Main"
```

pyndev assumes a generic stucture similar to `ncs-make-package` and this toml
values directly correspond to a package's `package-meta-data.xml` config:

```
  <component>
    <name>main</name>
    <application>
      <python-class-name>bbl.main.Main</python-class-name>
    </application>
  </component>
```

pyndev supports optional components such as "upgrade" type of components with
manual additions to a package's `pyproject.toml`:

```
[[tool.pyndev.python.components]]
name = "upgrade"
project = "bbl"
module = "main"
upgrade = "UpgradePortList"
```

mapping to:

```
  <component>
    <name>upgrade</name>
    <upgrade>
      <python-class-name>bbl.main.UpgradePortList</python-class-name>
    </upgrade>
  </component>
```

The fields are template valuess following this rough pattern:

```
  <component>
    <name>{{ name }}</name>
    <{{ component type key [application/upgrade]}}>
      <python-class-name>{{ project }}.{{ module }}.{{ component type value }}</python-class-name>
    </upgrade>
  </component>
```

> The stucture of the python class-name and it's path can vary based on an
> organization's internal patterns and standards. Similar to unmanaged packages
> the `add-pkg` only does an initial file creation and then customization and
> the life cycle of `pyproject.toml` is then manual after creation.

#### nso-migration result

New package structure:

```
packages
└── bbl
    ├── build_hook.py
    ├── Dockerfile
    ├── pyproject.toml
    └── src
        ├── package-meta-data.xml
        └── src
            └── Makefile
```

Workspace parent `pyproject.toml`:

```
dependencies = [
    "bbl",
]

[tool.uv.sources]
pkg_mgmt = {workspace = true}
bbl = {workspace = true}

[tool.uv.workspace]
members = [
    "pkg_mgmt",
    "packages/bbl",
]
```

In the "managed" version you can see a few more NSO package artifacts being
written based on the additional configuration in a package's `pyproject.toml'.

> Similar to the "unmanaged" section, the tutorial expects all service packages
> have been populated via `add-pkg` and all python components are properly
> configured.

### pyndev external dependencies

We are now at a point where we can look at interconnecting the pacakges from
"unmanaged" into the normal service repository.

#### common workspace configuration for all environments

pyndev project structure:

```
unmanaged-migration
├── .env
├── .env.local.example
├── .git
├── .gitignore
├── .gitlab-ci.yml.example
├── .pre-commit-config.yaml
├── .python-version
├── .venv
├── compose.yaml
├── docs
├── justfile
├── LICENSE
├── nso
├── packages
├── pkg_mgmt
├── pyproject.toml
├── README.md
└── uv.lock
```

##### .env

```
NSO_VERSION=6.7.2
REGISTRY=wharf.es.net/nso/cisco/
```

pyndev expects a default version of NSO for the current workspaces and a Docker
registry that has the Cisco official NSO containers for both `cisco-nso-prod`
and `cisco-nso-build` images. pyndev expects a private container registry where
these images are available. The population of base images and Docker registry
authentication are out of the scope of this tutorial.

##### .env.local.example

```
export UV_INDEX_PRIVATE_USERNAME=token-name
export UV_INDEX_PRIVATE_PASSWORD=secret
export UV_PUBLISH_TOKEN=secret
```

pyndev is based on the `uv` and thus the configuration for pypi access follows
standard patterns. This tutorial assumes a gitlab private access token with api
permissions. Write these secrets locally to `.env.local` and ensure this file
along with the example .gitignored are paired to keep this out of the git
repository. The above configuration can be amended based on your environment
and secret management but the above three variables are typically required.

##### pyproject.toml

```
[[tool.uv.index]]
name = "private"
url = "https://gitlab.es.net/api/v4/groups/10/-/packages/pypi/simple"
publish-url = "https://gitlab.es.net/api/v4/projects/15/packages/pypi"
explicit = true
```

This example is using gitlab as an internal pypi provider. Gitlab's api uses
the nonintuitive integer id based uri. We publish NSO packages directly to the
source repository, in this case `15` would be the `esnet-unmanged` repository
id. All NSO repositories are put into a `nso` group with id `10`. We read the
pypi registry at the group level so that we get an aggregate package list for
all specific repositories at once. Eg. would potentially get access to
`esnet-nso` or other new repositories with no configuration udpates. Other
artifact registries may have a different hierchy but `uv` and thus pyndev is
agnostic to these changes and customize as needed.

##### workspace pyproject.toml name and version

The parent `pyproject.toml` version is largely cosmetic as there is no parent
python package. ESnet tracks and tags aggregate versions with it's releases and
this configuration follows the git tags. Similarly, the name is cosmetic and
matches the git repository name.

#### esnet-nso unmanaged dependencies

With the boilerplate pypi config we can now declare some "unmanaged"
dependencies in our `nso-migration` skeleton.

Workspace parent pyproject.toml:

```
[dependency-groups]
"pyndev-nso-6.7.2" = [
    "arista-dcs-cli-5.30==5.30.7+nso6.7.2",
    "waveserver-nc-2.2==2.2.0+nso6.7.2",
    "infinera-g30-nc-4.7==4.7+nso6.7.2",
    "infinera-g40-nc-6.1==6.1.1+nso6.7.2",
    "juniper-junos-nc-4.18==4.18.18+nso6.7.2",
    "juniper-junos-nc-4.19==4.19.5+nso6.7.2",
    "nokia-sros_nc-24.10.r5-gen-1.0.25==1.0.25+nso6.7.2",
    "nokia-sros_nc-25.10.r7-gen-1.0.33==1.0.33+nso6.7.2",
    "observability-exporter==1.2.0+nso6.7.2",
    "phased-provisioning==1.1.0+nso6.7.2",
]
"pyndev-nso-6.7.3" = [
    "arista-dcs-cli-5.30==5.30.7+nso6.7.3",
    "waveserver-nc-2.2==2.2.0+nso6.7.3",
    "infinera-g30-nc-4.7==4.7+nso6.7.3",
    "infinera-g40-nc-6.1==6.1.1+nso6.7.3",
    "juniper-junos-nc-4.18==4.18.18+nso6.7.3",
    "juniper-junos-nc-4.19==4.19.5+nso6.7.3",
    "nokia-sros_nc-24.10.r5-gen-1.0.25==1.0.25+nso6.7.3",
    "nokia-sros_nc-25.10.r7-gen-1.0.33==1.0.33+nso6.7.3",
    "observability-exporter==1.2.0+nso6.7.3",
    "phased-provisioning==1.1.0+nso6.7.3",
]

[tool.uv]
conflicts = [
    [
        { group = "pyndev-nso-6.7.2" },
        { group = "pyndev-nso-6.7.3" },
    ],
]
```

We use pyndev specific dependency groups appended with the NSO versions
expected to be supported and developed on. Packages are typically built for a
specific version of NSO and are not always cross compatible with new versions
of NSO. pyndev uses PEP 440 "local version identifiers" to append this state to
a package version. The `uv` conflicts allow all versions to be populated and
tracked in a single `uv.lock` file for reproducible environments while only
allowing a single version to be installed locally based on `$NSO_VERSION`
variable. A project that only supports a single version of NSO still requires
the `pyndev-nso-${NSO_VERSION}` dependency-group naming.

> The workspace parent `pyproject.toml` becomes the system of record for
> package version matching and thus specific versions can be left out of
> per package child `pyproject.toml` configurations for brevity and pyndev
> packages use the generic `pyndev-nso` dependency group. All dependencies in
> child packages should be present the parent `pyproject.toml` for this
> convenient behavior.

### esnet-nso and esnet-unmanaged prep

We can now start modifying the existing NID repositories to match the pyndev
structure.

#### NID system skeleton

```
source/nso-docker/skeletons/system
├── Dockerfile.in
├── extra-files
├── includes
├── Makefile
├── nid
├── nidcommon.mk
├── nidsystem.mk
├── nidvars.mk
├── packages
├── README.nid-system.org
└── testenvs
```

#### NID NED skeleton

```
source/nso-docker/skeletons/ned
├── Dockerfile.in
├── extra-files
├── includes
├── Makefile
├── nid
├── nidcommon.mk
├── nidned.mk
├── nidvars.mk
├── packages
├── README.nid-ned.org
├── run-netsim.sh
├── test
├── test-packages
└── testenvs
```

#### pyndev support files

```
nso-migration/nso
├── dev
│   ├── capabilities.txt
│   └── config.xml
├── init
│   ├── aaa_init.xml
│   ├── add_admin_user.xml
│   ├── Dockerfile
│   └── ncs.conf
├── ncs_yang
│   └── Dockerfile
└── prod
    ├── Dockerfile
    └── ncs.conf
```

The `init` and `dev`  subdirectories in the `nso` directory work as
environments. `init` is the barebones setup and configuration for the local
environment. `dev` is support data that can be loaded after NSO is up and
running to support adding complex seed or test data. ESnet also has a `test`
directory under NSO but the pyndev skeleton does not impose any test structure.
For the most part the NID `testenvs` and other meta data can be mapped directly
to this structure.

##### ncs.conf

pyndev does not have a concept of mangling the `ncs.conf`. In this environment
these are static artifacts that match the local `$NSO_VERSION`. The
`nso/prod/ncs.conf` is more for generating a working image but is typically
replaced by a production configuration with tools such as helm or ansible used
to make more dynamic configuration.

> This configuration scheme does limit cases with multi version NSO where there
> is a breaking ncs.conf API change. These updates are typically handled in git
> branches versus overly complex pyndev handlers.

##### esent-unmanaged

For NEDs and third party packages ESnet typically just verifies the packages
load and NSO boots without any additional tests. For this we just breakout the
NID aaa_init.xml into the pyndev `nso/init` directory. We don't build images
from the unmanaged alone so `nso/prod` is removed.

##### esent-nso

For ESnet service packages we do have more setup in the NID `testenvs`. In
addtion to the `init` files above, we copy our single testenv config to the
pyndev `nso/dev` directory.

#### nso environment migration

```
cd target
cp -r nso-migration/nso esnet-nso
cp -r unmanaged-migration/nso esnet-unmanaged
```

Update and copy in NID configuraiton as needed.

##### esent-unmanaged

Remove the NID skeleton files:

```
cd esnet-unmanaged
rm .dockerignore
rm Dockerfile.in
rm -rf extra-files
rm -rf includes
rm Makefile
rm -rf nid
rm nidcommon.mk
rm nidned.mk
rm nidvars.mk
rm README.nid-ned.org
rm run-netsim.sh
rm -rf test
rm -rf test-packages
rm -rf testenvs
git commit -am 'remove NID skeleton files'
```

Update the packages to the pyndev nested `package/src` structure:

```
for d in packages/*/; do d="${d%/}"; git mv "$d" "$d.tmp" && mkdir "$d" && git mv "$d.tmp" "$d/src"; done
```

This should result in packages being migrated into `[package_name]/src` as a
file rename that preserves git history and blame. At this point you can update
or move package READMEs.

```
git commit -am 'renamed files for pyndev structure'
```

Copy in the remaining "unmanaged-migration" pyndev files:

```
S=../unmanaged-migration
cp "$S"/{compose.yaml,justfile,LICENSE,pyproject.toml,uv.lock} .
cp -r "$S"/pkg_mgmt .
cp "$S"/docs/*.md docs/
for d in "$S"/packages/*/; do p=$(basename "$d"); [ -d "packages/$p" ] || continue; cp "$d"/{build_hook.py,Dockerfile,pyproject.toml} "packages/$p/"; done
```

A `git status` can show a quick check that we haven't over written any existing
files and everything should be "untracked". Next we can copy in the dot files,
depending on how you setup secrets previous this command could change. If these
files are used in your current repository there may be some conflicts or manual
merging required for your organization's standards.

```
cp "$S"/{.env,.env.local,.env.local.example,.gitignore,.gitlab-ci.yml.example,.pre-commit-config.yaml,.python-version} .
```

You can copy in the packages for any additional packages you might be
aggregating into "unmanaged":

```
for p in observability-exporter phased-provisioning; do cp -r "$S/packages/$p" packages/; done
for p in observability-exporter phased-provisioning; do cp -r "../../source/nso-$p/packages/$p/." "packages/$p/src/"; done
```

At this point you should be able to test the local environment for a clean
build all the local packages.

```
just init
just sync
just lint
```

Make adjustments as needed and commit the final changes.

```
git add .
git commit -m 'import pyndev files and customization'
```

Update the .gitlab-ci.yaml.example, compose.yaml, and .pre-commit-config.yaml
if needed. For the ESnet repository we don't do yang linting on third party
packages and only publish pypi packages in CI. 

[Gitlab Setup](./gitlab-configuration.md) has specific examples for setting up
CI with the gitlab internal pypi registry but this should be customized to your
environment.

##### esnet-nso

The service package repository follows the same patterns as above with a few
exceptions called out here.

```
cd ../esnet-nso
rm nidsystem.mk
rm README.nid-system.org
S=../nso-migration
for d in "$S"/packages/*/; do p=$(basename "$d"); [ -d "packages/$p" ] || continue; cp "$d"/{.gitignore,build_hook.py,Dockerfile,pyproject.toml} "packages/$p/"; done
```

For "unmanaged" packages pyndev tracks everything in git but for "managed"
packages the `package-meta-data.xml` file is dynamically generated and not
tracked. After copying the per package `.gitignore` files you can clean up this
state.

```
git ls-files -zi -c --exclude-standard | xargs -0 git rm --cached
git commit -m 'remove package-meta-data.xml due to pyndev generation and ignore'
```

With all files moved and copied per the same steps for unmanaged this project
should be ready for development.

Review of the final steps:

```
just init
just sync
just lint
git add .
git commit -m 'import pyndev files and customization'
```

Gitlab CI setup will be a more involved with a test system but these steps will
be unique to your situation and thus justfiles, compose.yaml, and etc can be
customized as needed.

## Runtime

The `./nso/prod` directory has an example Dockerfile and ncs.conf to build a
full production image based on the package state of the local repository. At
ESnet we currently use ansible playbooks to deploy our production instance and
are looking at migrating towards a kubernetes based deployment in the future.
In both cases, we are able to utilized external templating engines, jinja2 for
ansible and helm for K8s. We were able to make a set of variables or values to
dynamically update ncs.conf much like NID's mangle conf with very little effort
or change from existing NID values.

Example docker deploy with new volume mounts:

```
- name: nso container
  docker_container:
    name: "{{ nso_container_name }}"
    image: "{{ nso_image }}/nso:{{ nso_revision }}"
    state: started
    network_mode: "host"
    recreate: yes
    log_driver: "json-file"
    log_options:
      max-size: "50m"
      max-file: "5"
    pull: yes
    restart_policy: "always"
    command: "{{ ncs_startup_options | default(omit) }}"
    volumes:
      - "{{ nso_defaults.config_path }}/ncs.conf:/nso/etc/ncs.conf"
      - "{{ nso_defaults.config_path }}/ncs.crypto_keys:/nso/etc/ncs.crypto_keys"
      - "{{ nso_defaults.ssh_key_path }}/id_rsa_nso:/nso/authgroups_ssh/id_rsa_nso"
      - "{{ nso_defaults.ssh_key_path }}/id_rsa_nso.pub:/nso/authgroups_ssh/id_rsa_nso.pub"
      - "{{ nso_defaults.ssh_key_path }}/id_rsa_nso_ro:/nso/authgroups_ssh/id_rsa_nso_ro"
      - "{{ nso_defaults.ssh_key_path }}/id_rsa_nso_ro.pub:/nso/authgroups_ssh/id_rsa_nso_ro.pub"
      - "{{ nso_defaults.cdb_path }}:/nso/run/cdb"
      - "{{ nso_defaults.log_path }}:/log"
    env:
      NCS_JAVA_VM_OPTIONS: "{{ ncs_java_vm_options }}"
      NCS_IPC_ADDR: "127.0.0.1"
      NCS_IPC_PORT: "4569"
```

We handle the secrets with standard tools outside the scope of this tutorial.
External `ncs.conf` was really the work involved for migrating prod deployments
to the pyndev image.
