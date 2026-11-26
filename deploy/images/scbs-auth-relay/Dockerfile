FROM docker-registry.itg.com.cn/mcp-gateway/auth-server@sha256:828194093445fd6a28ef853ea30b11951f1ccf6b6b9e330e69ee412f486ef60c
ARG SOURCE_REVISION=unknown
LABEL org.opencontainers.image.revision="${SOURCE_REVISION}" \
      cn.com.itg.scbs.base-digest="sha256:828194093445fd6a28ef853ea30b11951f1ccf6b6b9e330e69ee412f486ef60c"
COPY patch_relay.py test_relay.py /tmp/scbs-relay/
RUN python /tmp/scbs-relay/patch_relay.py \
    && python /tmp/scbs-relay/test_relay.py /app/server.py \
    && rm /tmp/scbs-relay/patch_relay.py /tmp/scbs-relay/test_relay.py
