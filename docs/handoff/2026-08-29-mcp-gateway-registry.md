# MCP Gateway & Registry 部署交接记录

日期：2026-08-29

## 目标

在公司 Rancher 管理的 Kubernetes 集群中部署 `mcp-gateway-registry`，供公司内部注册、发现和访问 MCP Server。

## 已完成的本地验证

- 使用 WSL Ubuntu-22.04 + Docker Compose 启动项目。
- Registry 前端曾通过 `http://localhost:8081` 访问。
- Keycloak 使用 `http://localhost:8080`。
- WSL/Docker 网络代理使用过 Windows 地址 `192.168.1.7:7890`。
- 本地配置中生成过密钥和密码；这些敏感信息不得提交到 Git。
- Keycloak Realm 使用 `mcp-gateway`。
- Registry 管理权限与 Keycloak 用户组有关，管理员用户需要加入相应的 Registry 管理组。

## 公司 Kubernetes 环境

- Kubernetes 管理平台：Rancher
- Ingress：NGINX
- 计划使用内置 Keycloak
- 计划使用内置 MongoDB
- 镜像仓库：`docker-registry.itg.com.cn/itg`
- 计划域名：`mcp-gateway.itg.it.org`
- 当前部署目标：HTTP，不启用 TLS

## 本次新增文件

- `deploy/helm/values.company.yaml`
  - 公司环境 Helm Values
  - 使用公司私有镜像仓库
  - 启用内置 Keycloak/MongoDB
  - Registry/Auth Server 副本数配置
  - NGINX Ingress 适配配置

- `deploy/helm/ingress-nginx.yaml`
  - Rancher NGINX Ingress
  - 当前使用 HTTP
  - 后端服务为 Helm 部署的 `registry` Service

## 重要地址说明

当前 Values 使用 Chart 的 subdomain 路由模式，因此实际地址为：

```text
http://mcpregistry.mcp-gateway.itg.it.org
```

如果公司要求地址必须是：

```text
http://mcp-gateway.itg.it.org
```

需要改为 path 路由模式，或者进一步修改 Chart 的 Ingress/外部 URL计算方式。

## 镜像

Chart 的全局镜像前缀主要覆盖三个核心镜像：

```text
docker-registry.itg.com.cn/itg/registry:<tag>
docker-registry.itg.com.cn/itg/auth-server:<tag>
docker-registry.itg.com.cn/itg/mcpgw:<tag>
```

推送镜像前必须先确认本地 Chart 中的实际版本 Tag，不要直接使用 `latest`。Keycloak、PostgreSQL、MongoDB Operator 等依赖镜像可能仍需从各自的公共仓库拉取；如果公司集群不能访问公共仓库，还要单独镜像这些依赖，并在 Values 中覆盖对应镜像地址。

## Helm 部署流程

在仓库根目录执行：

```powershell
cd charts/mcp-gateway-registry-stack

helm dependency build
helm lint .

helm template mcp-gateway . `
  -n mcp-gateway `
  -f ../../deploy/helm/values.company.yaml `
  > ../../deploy/helm/rendered.yaml
```

确认渲染结果中没有本地密码、Token 或错误的公共镜像后，再通过 Rancher Apps 安装，或使用：

```powershell
kubectl create namespace mcp-gateway

helm upgrade --install mcp-gateway . `
  -n mcp-gateway `
  -f ../../deploy/helm/values.company.yaml

kubectl apply -n mcp-gateway `
  -f ../../deploy/helm/ingress-nginx.yaml
```

## Rancher UI 方式

Rancher 通常通过 Helm Repository 部署，不是直接上传任意本地 Chart 文件。

推荐流程：

1. 执行 `helm dependency build`。
2. 打包 Chart，或推送为 OCI Helm Artifact。
3. 在 Rancher 的 `Apps > Repositories` 中添加 HTTP/OCI Chart Repository。
4. 在 `Apps > Charts` 中安装 `mcp-gateway-registry-stack`。
5. 在 Values YAML 中使用 `deploy/helm/values.company.yaml` 的内容。
6. 单独导入 `deploy/helm/ingress-nginx.yaml`。

## 待办事项

- 确认公司私有 Registry 是否支持 OCI Helm Artifact。
- 确认 Rancher 集群的 StorageClass。
- 确认 DNS 是否将 `mcpregistry.mcp-gateway.itg.it.org` 指向 NGINX Ingress。
- 确认 HTTP 是否仅限公司内网；生产环境建议恢复 HTTPS。
- 确认私有镜像仓库认证方式和 Kubernetes imagePullSecret。
- 在目标环境中确认 Helm Chart 版本与镜像版本一致。
- 首次部署后检查 Keycloak 管理员凭据 Secret，不要在 Git 中记录密码。
- 使用测试用户验证 Registry 管理权限、MCP Server 注册和服务访问权限。

## 安全边界

以下内容禁止提交：

- `.env`、`.env.*`
- Keycloak/MongoDB 密码
- JWT、SECRET_KEY、OAuth Client Secret
- kubeconfig
- Docker Registry 登录凭据
- Helm 渲染后包含 Secret 明文的文件

