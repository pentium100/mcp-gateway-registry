# ITG-SCBS personal identity relay hotfix

The company-owned ITG-SCBS MCP validates the caller's personal Gateway JWT to attribute community contributions. The existing auth-server 1.29.0 strips both Authorization and X-Authorization for ordinary upstreams. This patch adds exactly itg-scbs to the existing internal relay exception keyed by the verified, path-validated server claim. Administrators must keep this registration routed to the trusted company MCP service.

All other upstreams continue stripping personal authorization. Cookie, hop-by-hop and internal routing headers retain existing filtering. No alternate credential header or global passthrough setting is introduced.

The image uses the exact company 1.29.0 base digest and patches one allowlist expression. It preserves that release's dependencies and runtime, rather than copying the newer main branch server into an older image. A changed base fails the build. The local main source has the same narrow exception for future builds.

Build from this directory, with the committed source revision:

```powershell
docker build --compress --build-arg SOURCE_REVISION=<git-commit> -t docker-registry.itg.com.cn/mcp-gateway/auth-server:1.29.0-scbs.1 .
```

The build runs four regression checks against the actual image's proxy selector and header filter: SCBS relay, unrelated and spoofed-name denial, original internal relay, and continued hop-header filtering. The test parses those functions from the source to avoid starting databases or external identity services.

Deploy only the auth-server image as 1.29.0-scbs.1; registry/mcpgw/Keycloak images are unchanged. ITG-SCBS MCP also needs its FastMCP Authorization extraction fix (source f55962f or later). Preserve existing environment and Secret values. Restart/rollout the respective workloads and retry scbs-community-skills list through Gateway. Image publication alone does not update Kubernetes.

2026-11-26: the existing base image reproduced the missing X-Authorization failure (one of four checks failed); local source now includes the narrow exception. Production Gateway header arrival and authenticated directory lookup remain deployment acceptance steps. No real tokens were read during the build.


Publication (2026-11-26): `docker-registry.itg.com.cn/mcp-gateway/auth-server:1.29.0-scbs.1`, digest `sha256:2a5c0cdb84d685a8e7d05452691f634a3cc82dcdf14720f25ac42ffeec43aae9`, source `88143c279d317e7f822ec51b84e1d2fa4979e6a1`. Push output and remote registry manifest match. The resulting server.py was compared to the pinned base and differs only in the allowlist expression. Tests: four actual selector/filter checks during the image build; combined checks using the extracted Gateway image source and MCP HTTP endpoint passed for both auth header forms, Cookie removal, unrelated-route denial and expired JWT rejection. MCP full regression: 348 passed. This does not claim a live Gateway/Keycloak deployment or a real-token GitLab query.
