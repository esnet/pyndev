ARG PROJECT_VERSION=pyndev-nso
ARG NSO_VERSION=latest
ARG REGISTRY=registry

FROM ${REGISTRY}cisco-nso-prod:${NSO_VERSION}
ARG PROJECT_VERSION
USER root
RUN echo "${PROJECT_VERSION}" > /VERSION
USER 998
COPY --chown=998:998 --from=packages . /nso/run/packages
COPY --chown=998:998 ncs.conf /nso/etc/
