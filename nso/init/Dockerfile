ARG NSO_VERSION=latest
ARG REGISTRY=registry

FROM ${REGISTRY}cisco-nso-prod:${NSO_VERSION}
COPY --chown=998:998 --from=packages . /nso/run/packages
COPY --chown=998:998 ncs.conf /nso/etc/
COPY --chown=998:998 aaa_init.xml /nso/run/cdb_defaults/
COPY --chown=998:998 add_admin_user.xml /nso/run/cdb_defaults/
