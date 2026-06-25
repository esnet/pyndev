ARG NSO_VERSION=latest
ARG REGISTRY=registry

FROM ${REGISTRY}cisco-nso-prod:${NSO_VERSION} AS build

FROM scratch
COPY --from=build /opt/ncs/current/src/ncs/yang/*.yang /
