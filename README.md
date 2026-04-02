# AgentFi Runtime

一个单机托管版 `agent runtime`，把 `NFT` 和 `Agent` 的控制权彻底绑定：

- FastAPI：提供控制面接口
- MySQL：存 `agent / nft / runs / listings / schedules / checkpoints`
- Redis：做锁、热缓存和 Celery 队列
- Celery：异步执行 agent run
- APScheduler：扫描并派发定时任务
- web3.py：监听 NFT 合约 `Transfer` 事件，同步链上 owner
- OpenAI / 兼容模型 API：负责 agent 推理
- Docker Compose：把整套 runtime 打包成单机可跑的多进程服务
- Vue + Vite：提供真正按路由拆分的控制台前端

## 当前功能总览

### 鉴权与钱包

- MetaMask challenge + signature 登录
- runtime session 鉴权，所有写操作默认要求登录
- 本地 `wallet` 与链上 `chain_address` 映射
- 目标地址未入库时自动创建 shadow wallet

### Agent 与 NFT

- 创建 agent，并绑定唯一 `agent_nft`
- 支持自动链上 mint `AgentOwnershipNFT`
- 支持绑定已有 `contract_address + chain_token_id`
- 提供 `tokenURI` metadata JSON 和动态 SVG 图片资源
- 支持 `LOCAL_ONLY / CHAIN_MAPPED_INACTIVE / CHAIN_SYNCED` 三种 ownership mode

### 交易与控制权

- 创建 listing、购买 listing、取消 listing
- 本地 transfer NFT
- 链上模式下优先使用 MetaMask 发起 `safeTransferFrom`
- 监听 ERC-721 `Transfer` 事件并同步 owner
- 监听链上 marketplace 事件并同步 listing 状态、事件和交易记录

### Runtime 执行

- 手动 queue run
- Celery 异步执行
- Redis 锁避免同一 agent 并发执行
- worker 执行前再次校验 owner，防止排队期间控制权变化
- 支持 `retry / cancel / timeout / dead-letter`
- 支持 `runs metrics` 和 `runtime logs`
- APScheduler 负责 interval schedule 派发

### 控制台前端

- `Vue + Vite` 管理后台
- 按真实路由拆分，不再是单页锚点
- 支持 Runtime、Launchpad、Wallets、Agents、Market、Runs 六个域
- 支持列表页、详情页、操作页三类后台页面

## 合约与部署

仓库现在包含一个最小可用的 ERC-721 合约：

- [AgentOwnershipNFT.sol](/Users/honey/AgentFi/contracts/AgentOwnershipNFT.sol)
- [AgentMarketplace.sol](/Users/honey/AgentFi/contracts/AgentMarketplace.sol)

它支持：

- `mintTo(address to, string uri)`
- `setMinter(address account, bool allowed)`
- 标准 `Transfer / approve / safeTransferFrom`
- 每个 token 独立 `tokenURI`

本地链推荐直接走 Foundry 脚本：

```bash
./scripts/deploy_agent_nft_local.sh
```

如果你要部署到测试网，或者想继续使用 Python 版部署器：

先确保镜像已经包含最新依赖：

```bash
docker compose build api
```

如果你是在宿主机跑 `anvil`，并且部署脚本是通过 Docker Compose 执行的，`DEPLOY_RPC_URL` 应该写成 `http://host.docker.internal:8545`，不要写容器内的 `127.0.0.1`。本地开发下，如果 Docker 里的 `py-solc-x` 下载到的 `solc` 二进制和宿主机架构不兼容，优先改用上面的 Foundry 本地脚本。

```bash
docker compose run --rm api python scripts/deploy_agent_nft.py --env-file deploy/local.anvil.env.example
```

或者：

```bash
docker compose run --rm api python scripts/deploy_agent_nft.py --env-file deploy/sepolia.env.example
```

脚本会：

- 编译合约
- 部署 `AgentOwnershipNFT`
- 可选授权 runtime minter
- 生成 `contracts/artifacts/AgentOwnershipNFT.json`
- 输出一段可直接抄进 runtime `.env` 的配置

相关文件：

- [deploy_agent_nft_local.sh](/Users/honey/AgentFi/scripts/deploy_agent_nft_local.sh)
- [deploy_agent_nft.py](/Users/honey/AgentFi/scripts/deploy_agent_nft.py)
- [deploy_agent_marketplace_local.sh](/Users/honey/AgentFi/scripts/deploy_agent_marketplace_local.sh)
- [deploy_agent_marketplace.py](/Users/honey/AgentFi/scripts/deploy_agent_marketplace.py)
- [local.anvil.env.example](/Users/honey/AgentFi/deploy/local.anvil.env.example)
- [sepolia.env.example](/Users/honey/AgentFi/deploy/sepolia.env.example)

链上 marketplace 现在也已经包含在仓库里。它是一个最小可用的固定价 escrow 合约：

- 卖家调用 `createListing(tokenId, price)` 挂单
- 买家调用 `buyListing(listingId)` 购买
- 卖家调用 `cancelListing(listingId)` 撤单
- runtime listener 会索引 `ListingCreated / ListingCancelled / ListingPurchased`

部署链上 marketplace：

```bash
./scripts/deploy_agent_marketplace_local.sh
```

或者：

```bash
docker compose run --rm api python scripts/deploy_agent_marketplace.py --env-file deploy/local.anvil.env.example
```

部署脚本会输出可直接写回 `.env` 的：

- `MARKETPLACE_CONTRACT_ADDRESS`

## 进程拓扑

1. `api`
   FastAPI 控制面，负责 MetaMask 鉴权、runtime wallet 映射、agent、NFT、交易和 run 入队。
2. `worker`
   Celery worker，真正执行 queued run。
3. `scheduler`
   APScheduler 轮询 `agent_schedules`，到点后自动派发 run。
4. `listener`
   web3.py 监听链上 ERC-721 `Transfer` 事件，把 owner 同步回 MySQL 和 Redis。
5. `mysql`
   业务事实库。
6. `redis`
   锁、队列、owner cache、事件流。

## 控制权模型

- 每个 `agent` 对应一个唯一 `agent_nft`
- `agent_nft.owner_wallet_id` 是当前控制权来源
- 所有写操作都要求当前浏览器 MetaMask 先完成 challenge + signature 登录
- 手动运行 agent 时，API 会检查当前 wallet 是否是 NFT owner
- run 进入 Celery 队列后，worker 开始执行前还会再检查一次 owner
- 如果 run 排队期间 NFT 已经转手，run 会被拒绝执行
- 链上 `Transfer` 事件一旦发生，listener 会回写 owner，并自动撤销该 NFT 的开放挂单

NFT 在 runtime 里有 3 种模式：

- `LOCAL_ONLY`
  没有链上映射，所有权和交易都在 runtime 内完成
- `CHAIN_MAPPED_INACTIVE`
  记录了 `contract_address / chain_token_id`，但当前 runtime 没有监听这个合约
- `CHAIN_SYNCED`
  当前 runtime 正在监听该 ERC-721 合约，owner 以链上 `Transfer` 事件为准

当 NFT 处于 `CHAIN_SYNCED`：

- 可以继续 run agent，因为控制权会随链上 owner 同步
- 不允许本地 marketplace 直接成交
- 不允许本地 transfer 改 owner
- 前端会优先走 MetaMask 发起真实链上转移

## 数据模型

- `wallets`
  本地钱包，支持可选 `chain_address`
- `agents`
  agent 本体、prompt、记忆
- `agent_nfts`
  agent 的 NFT 映射，包含可选 `contract_address / chain_token_id`
- `market_listings`
  交易挂单
- `market_listing_chain_states`
  链上 listing 状态、价格、tx hash、链上 listing id
- `market_order_events`
  链上市场事件索引
- `transaction_records`
  runtime 关联的链上交易记录
- `agent_runs`
  异步执行记录，状态包含 `QUEUED / RUNNING / COMPLETED / FAILED / CANCELLED / TIMED_OUT`
- `agent_schedules`
  定时任务定义
- `runtime_checkpoints`
  web3 listener 的区块同步位点

## 启动

```bash
docker compose up --build
```

启动后可用服务：

- Runtime Console: [http://localhost:8000/](http://localhost:8000/)
- API 文档: [http://localhost:8000/docs](http://localhost:8000/docs)
- MySQL: `localhost:3306`
- Redis: `localhost:6379`

首次启动时，API 会自动执行数据库初始化和 Alembic migration；后续 schema 变更也通过仓库内的迁移文件统一收敛。

## 控制台页面

控制台现在已经按后台信息架构拆成真实功能页：

- `Runtime`
  - `/runtime/overview`
- `Launchpad`
  - `/launchpad/session`
  - `/launchpad/create`
- `Wallets`
  - `/wallets/registry`
  - `/wallets/operator`
  - `/wallets/:walletId`
- `Agents`
  - `/agents/library`
  - `/agents/:agentId`
- `Market`
  - `/market/listings`
  - `/market/transfers`
  - `/market/listings/:listingId`
- `Runs`
  - `/runs/queue`
  - `/runs/history`
  - `/runs/history/:runId`
  - `/runs/schedules`
  - `/runs/schedules/:scheduleId`

## 云端 VPS 部署

仓库现在已经包含一套单机 VPS 生产部署文件：

- [docker-compose.prod.yml](/Users/honey/AgentFi/docker-compose.prod.yml)
- [Caddyfile](/Users/honey/AgentFi/deploy/Caddyfile)
- [vps.env.example](/Users/honey/AgentFi/deploy/vps.env.example)
- [deploy_vps.sh](/Users/honey/AgentFi/scripts/deploy_vps.sh)

这套生产版和本地开发版的差异是：

- 只对公网暴露 `80/443`
- `MySQL / Redis` 不再暴露公网端口
- 由 `Caddy` 负责自动 HTTPS 和反向代理
- `api / worker / scheduler / listener / mysql / redis` 都留在内网网络
- 适合单台云主机直接 `docker compose` 运行

### 部署前准备

1. 准备一台带公网 IP 的 Linux VPS
2. 安装 `Docker` 和 `Docker Compose Plugin`
3. 把域名 `A` 记录指向这台 VPS
4. 在云厂商安全组和系统防火墙中只开放：
   - `80/tcp`
   - `443/tcp`
5. 如果要启用链上模式，准备：
   - 公网 RPC
   - 已部署的 `AgentOwnershipNFT`
   - 已部署的 `AgentMarketplace`
   - 可选 runtime minter 私钥

### 生产环境变量

先复制模板：

```bash
cp deploy/vps.env.example .env.prod
```

至少要改这些值：

- `APP_DOMAIN`
- `CADDY_EMAIL`
- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `MODEL_BASE_URL`
- `MODEL_API_KEY`
- `MODEL_NAME`
- `PUBLIC_BASE_URL`

如果要启用链上：

- `WEB3_PROVIDER_URL`
- `NFT_CONTRACT_ADDRESS`
- `MARKETPLACE_CONTRACT_ADDRESS`
- `NFT_MINTER_PRIVATE_KEY`

注意：

- `PUBLIC_BASE_URL` 必须等于你的公网域名，例如 `https://agentfi.example.com`
- 不要继续使用当前本地 `.env` 里的 `127.0.0.1`、`host.docker.internal` 和 Anvil 测试私钥，见 [.env](/Users/honey/AgentFi/.env#L18)

### 启动生产栈

```bash
bash scripts/deploy_vps.sh .env.prod
```

或者手动执行：

```bash
ENV_FILE=.env.prod docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

查看状态：

```bash
ENV_FILE=.env.prod docker compose --env-file .env.prod -f docker-compose.prod.yml ps
```

查看日志：

```bash
ENV_FILE=.env.prod docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f caddy api worker
```

### 上线后的访问地址

- Console: `https://你的域名/`
- API Docs: `https://你的域名/docs`
- Health: `https://你的域名/v1/health`

### 生产部署建议

- 先用测试网合约验证一遍 `mint / listing / buy / transfer / listener sync`
- 给 `.env.prod` 做服务器级备份，不要提交到 git
- 开启云盘快照或至少备份 `mysql_data_prod`
- 如果要跑真实模型，把 `AGENT_EXECUTOR_MODE` 设成 `openai_compatible`
- 如果只是先演示，也可以先把链上相关变量留空，用 `LOCAL_ONLY` 模式跑后台和 agent runtime

控制台前端现在由 `Vue + Vite` 构建，导航会落到真实的功能页：

- `/launchpad`
- `/wallets`
- `/agents`
- `/market`
- `/runs`

如果你在宿主机本地直接调前端，也可以单独运行：

```bash
cd frontend
npm install
npm run build
```

构建产物会输出到 `app/ui/dist`，FastAPI 会优先分发这个 `dist`，只有在前端尚未构建时才回退到旧的静态页面。

链上接入状态可以通过：

- `GET /v1/runtime/config`

直接查看。接口会告诉你当前是：

- `DISABLED`
- `RPC_ERROR`
- `CONTRACT_MISSING`
- `READY`

如果你要让 runtime 在创建 agent 时直接链上 mint，还需要在 `.env` 里配置：

- `PUBLIC_BASE_URL`
- `WEB3_PROVIDER_URL`
- `NFT_CONTRACT_ADDRESS`
- `MARKETPLACE_CONTRACT_ADDRESS`
- `NFT_MINTER_PRIVATE_KEY`

如果 runtime 本身也是跑在 Docker 里，而你的本地链是宿主机上的 `anvil`，这里的 `WEB3_PROVIDER_URL` 同样应该写成 `http://host.docker.internal:8545`。

如果你希望链上钱包、浏览器或市场直接读取 `tokenURI` 的 JSON 和图片资源，`PUBLIC_BASE_URL` 还必须是一个公网可访问的地址，例如你自己的域名，或者本地开发时临时用 `ngrok` / `cloudflared` 暴露出来的地址。

## MetaMask 登录流

控制台现在默认走外接 MetaMask：

1. 点击 `Connect MetaMask`
2. 点击 `Sign In & Sync`
3. 前端会向 `/v1/auth/metamask/challenge` 申请 challenge
4. MetaMask 对 challenge 做 `personal_sign`
5. 后端在 `/v1/auth/metamask/verify` 验签并签发 runtime session
6. 所有创建 agent、run、挂牌、购买、转移、定时任务接口都要求该 session

这意味着：

- agent 控制权不再只是前端下拉框约束
- 后端会把接口调用者和当前 MetaMask 地址强绑定
- 大多数写接口不再要求你手动传内部 `wallet_id`
- 如果切换 MetaMask 账户，需要重新签名登录
- 当 NFT 带有链上映射且 listener 正在监听同一 ERC-721 合约时，前端会优先调用 MetaMask 发起真实链上转移

## 关键接口

### 1. 申请 MetaMask challenge

```bash
curl -X POST http://localhost:8000/v1/auth/metamask/challenge \
  -H "Content-Type: application/json" \
  -d '{
    "chain_address":"0x1111111111111111111111111111111111111111",
    "chain_id":"0x1",
    "label":"alice",
    "initial_balance":"1000"
  }'
```

### 2. 用签名换 session

```bash
curl -X POST http://localhost:8000/v1/auth/metamask/verify \
  -H "Content-Type: application/json" \
  -d '{
    "chain_address":"0x1111111111111111111111111111111111111111",
    "signature":"0x..."
  }'
```

返回里会包含：

- `access_token`
- `wallet`
- `expires_in`

后续所有写接口都要带：

```bash
-H "Authorization: Bearer <access_token>"
```

### 3. 创建 agent，并自动链上 mint 或绑定已有 token

如果 runtime 已经配置好：

- `WEB3_PROVIDER_URL`
- `NFT_CONTRACT_ADDRESS`
- `NFT_MINTER_PRIVATE_KEY`
- owner wallet 有 `chain_address`

那创建 agent 时会自动链上 mint 一个 `AgentOwnershipNFT`，并把返回的 `chain_token_id` 写回数据库。

如果你已经有现成 token，也可以手动传 `contract_address + chain_token_id` 做绑定。

```bash
curl -X POST http://localhost:8000/v1/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "name":"Research Agent",
    "description":"Tracks alpha and writes market notes",
    "system_prompt":"Act like a crypto research operator with strong trading discipline.",
    "seed_memory":[]
  }'
```

### 4. owner 调度 agent

```bash
curl -X POST http://localhost:8000/v1/agents/agent_xxx/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"task":"Research a new NFT collection and suggest a listing strategy."}'
```

这个接口现在返回的是一个 `QUEUED` run，真正执行由 Celery worker 完成。

### 5. NFT metadata / tokenURI

新 mint 的 NFT 会把 `tokenURI` 指向：

- `GET /v1/nfts/{token_id}/metadata`

metadata JSON 里会继续引用动态 SVG 图片：

- `GET /v1/nfts/{token_id}/image.svg`

兼容性上，老的：

- `GET /v1/nfts/{token_id}`

现在也会附带标准的 `name / description / image / attributes` 字段，避免已经 mint 的 token 因为旧 URI 失去可读性。

### 6. 查询 run

```bash
curl http://localhost:8000/v1/runs/run_xxx
```

### 6.1. 查询 runs metrics

```bash
curl http://localhost:8000/v1/runs/metrics
```

### 6.2. 查询 runtime logs

```bash
curl "http://localhost:8000/v1/runtime/logs?limit=50"
```

### 6.3. 取消 run

```bash
curl -X POST http://localhost:8000/v1/runs/run_xxx/cancel \
  -H "Authorization: Bearer <access_token>"
```

### 6.4. 重试 run

```bash
curl -X POST http://localhost:8000/v1/runs/run_xxx/retry \
  -H "Authorization: Bearer <access_token>"
```

### 7. 创建定时任务

```bash
curl -X POST http://localhost:8000/v1/agent-schedules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "agent_id":"agent_xxx",
    "task":"Write one market update.",
    "interval_seconds":300,
    "starts_in_seconds":30
  }'
```

### 8. 挂牌出售 agent

```bash
curl -X POST http://localhost:8000/v1/listings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"token_id":"nft_xxx","price":"250"}'
```

### 9. 购买 agent

```bash
curl -X POST http://localhost:8000/v1/listings/listing_xxx/buy \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{}'
```

买完后，当前登录的 MetaMask 对应 runtime wallet 会立刻成为新的 NFT owner；之后的手动调度和定时调度都会跟随新 owner。

### 10. 直接转移给另一个链上地址

```bash
curl -X POST http://localhost:8000/v1/nfts/nft_xxx/transfer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"to_chain_address":"0x2222222222222222222222222222222222222222"}'
```

如果目标地址还没有 runtime wallet 映射，系统会自动创建一个 shadow wallet 作为接收方。

控制台里的 `Transfer NFT` 现在有两种行为：

- 如果该 NFT 具备 `contract_address + chain_token_id`，并且和 runtime 当前监听的 `NFT_CONTRACT_ADDRESS` 一致，前端会直接调用 MetaMask 发起 ERC-721 `safeTransferFrom`
- 链上交易发出后，runtime 会等待 listener 根据 `Transfer` 事件回写 owner
- 如果没有链上映射，或者 listener 没有监听该合约，则回退到本地 runtime transfer

## 模型推理

默认 `AGENT_EXECUTOR_MODE=mock`，方便本地直接跑业务。

如果接真实模型，配置：

- `AGENT_EXECUTOR_MODE=openai_compatible`
- `MODEL_BASE_URL`
- `MODEL_API_KEY`
- `MODEL_NAME`

worker 在执行 run 时会把：

- 当前 owner 身份
- agent prompt
- agent 描述
- 最近记忆
- 当前 task

一起送到模型接口。

## Run 管理能力

这套 runtime 现在已经补齐了比较完整的运行控制：

- `max_attempts`
  每个 run 可配置最大尝试次数
- `timeout_seconds`
  每个 run 可配置单次执行超时
- `cancel_requested_at`
  已排队或未完成 run 可请求取消
- `dead_lettered_at`
  超过重试上限或显式失败后会进入 dead-letter
- `parent_run_id`
  retry 会生成新的 child run，并保留原始 run 链路

配套接口：

- `GET /v1/runs`
- `GET /v1/runs/{run_id}`
- `GET /v1/runs/metrics`
- `POST /v1/runs/{run_id}/cancel`
- `POST /v1/runs/{run_id}/retry`
- `GET /v1/runtime/logs`

## 链上同步

如果你要让 runtime 跟真实 NFT 合约同步，配置：

- `WEB3_PROVIDER_URL`
- `NFT_CONTRACT_ADDRESS`
- 可选 `WEB3_START_BLOCK`

listener 会持续轮询该合约的 `Transfer` 事件，并把链上 token owner 映射回本地钱包：

- 如果 `to` 地址还没有对应钱包，会自动创建一个 shadow wallet
- 如果该 NFT 本地正在挂牌，会自动撤单
- Redis owner cache 会同步刷新

## 业务约束

- agent 执行时会拿 Redis 锁，避免同一 agent 并发跑多次
- 买卖和转移时也会检查 Redis 锁，避免执行中途换 owner
- run 入队后到真正执行前，会再次校验 owner，保证“谁拥有 NFT，谁控制 agent”

## 迁移与运维

- 数据库 schema 通过 Alembic 管理
- 迁移文件位于 `migrations/versions`
- `docker compose` 启动 API 时会自动补齐到当前 head revision
- Runtime 还提供：
  - `GET /v1/health`
  - `GET /v1/runtime/config`
  - `GET /v1/runs/metrics`
  - `GET /v1/runtime/logs`
