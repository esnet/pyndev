set dotenv-load := true
set positional-arguments

# List all available commands
list:
  @just --list

# Create a new NSO package for development
add-pkg +args:
  @uv run --no-sync add_pkg "$@"

# Remove a NSO package from the project
rm-pkg package:
  @uv run --no-sync rm_pkg {{package}}

# pyndev sync managed package files
sync-pkg:
  @uv run --no-sync sync_pkg

# Copy yang from NSO_VERSION build image to project
load-yang:
  @docker buildx build \
    --build-arg NSO_VERSION \
    --build-arg REGISTRY \
    --output type=local,dest=nso/ncs_yang \
    nso/ncs_yang

# Initialize the workspace
init:
  #!/usr/bin/env bash
  set -euo pipefail
  if [ -f .env.local ]; then
    source .env.local
  fi
  # uncomment the load-yang step when .env is accurate
  # just load-yang
  uv venv -c
  exec uv pip install --group dev

# Sync packages and environment
sync quiet='':
  #!/usr/bin/env bash
  set -euo pipefail
  if [ -f .env.local ]; then
    source .env.local
  fi
  just sync-pkg
  uv sync --reinstall {{ if quiet != '' { '--quiet' } else { '' } }}
  uv sync --group pyndev-nso {{ if quiet != '' { '--quiet' } else { '' } }}

# Build local packages, default is '--all-packages', optionally specify one or more package names to build serially
build *args:
  #!/usr/bin/env bash
  set -euo pipefail
  if [ -f .env.local ]; then
    source .env.local
  fi
  if [ -z "{{args}}" ]; then
    uv build --all-packages --wheel
  else
    for arg in {{args}}; do
      uv build --package "$arg" --wheel
    done
  fi

# Publish local packages, default is all nso packages, optionally specify a wheel package name or general prefix
publish package='':
  #!/usr/bin/env bash
  set -euo pipefail
  if [ -f .env.local ]; then
    source .env.local
  fi
  if [ -z "{{package}}" ]; then
    exec uv run --no-sync publish_pkg
  else
    exec uv run --no-sync publish_pkg --package "{{package}}"
  fi

# Bring up a local instance of NSO
up service='nso':
  @docker compose --profile {{service}} up -w --build --quiet-build

# Tear down a local instance of NSO
down service='nso':
  @docker compose --profile {{service}} down --rmi local

# Enter the NSO cli as user admin
cli service='nso':
  @docker compose exec {{service}} bash -lc 'ncs_cli -u admin'

# Enter the NSO container bash shell
shell service='nso':
  @docker compose exec {{service}} bash -l

load env='dev' service='nso':
  #!/usr/bin/env bash
  set -euo pipefail
  if [ -d nso/{{env}} ]; then
    docker compose cp nso/{{env}}/. {{service}}:/tmp/load
    if [ -f nso/{{env}}/config.xml ]; then
      docker compose exec {{service}} /bin/sh -c 'ncs --mergexmlfiles /tmp/load/config.xml'
    fi
    if [ -f nso/{{env}}/capabilities.txt ]; then
      docker compose exec {{service}} /bin/sh -c 'ncs_cli -J --stop-on-error -u admin < /tmp/load/capabilities.txt'
    fi
  fi

# Issue a ncs_cli 'request packages package [package] redeploy' (no package sync)
re-deploy target='all' service='nso':
  #!/usr/bin/env bash
  set -euo pipefail
  TARGET={{target}}
  WILD="${TARGET//all/*}"
  echo "Redeploying package ${TARGET}..."
  exec docker compose exec {{service}} /bin/sh -c 'echo "request packages package '"${WILD}"' redeploy" | ncs_cli -u admin'

# Sync packages and redeploy NSO packages
redeploy target='all' service='nso':
  @just sync quiet
  @sleep 1
  @just re-deploy {{target}} {{service}}

# Sync packages and reload all NSO packages
reload service='nso':
  @just sync quiet
  @sleep 1
  @echo "Reloading {{service}} packages..."
  @docker compose exec {{service}} /bin/sh -c 'echo "request packages reload force" | ncs_cli -u admin'

# Run NSO tests
test:
  @echo "Fill in your test framework here"

# Run NSO container in background and run all test, auto CI test command
auto-test:
  @docker compose --profile auto-nso up -d --build --quiet-build --wait
  @just test

# Make sure auto-test nso container is brought down
auto-test-down:
  @just down auto-nso

# One off lint everything
lint:
  @pre-commit run -a --hook-stage pre-push

# Build a NSO prod image with local packages
build-nso-image version='pyndev-nso':
  @docker buildx build \
    --build-arg NSO_VERSION \
    --build-arg REGISTRY \
    --build-arg PROJECT_VERSION={{version}} \
    --build-context packages=.venv/lib/python3.12/site-packages/pyndev-nso \
    -t "container-registry.example.com/nso/pyndev/nso:${NSO_VERSION}-{{version}}" \
    -f nso/prod/Dockerfile \
    nso/prod
