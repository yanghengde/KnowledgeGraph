# Ubuntu 26.04 Docker 部署

该部署包含三个运行阶段：

- `neo4j`：Neo4j 数据库，数据、日志和插件保存在 Docker 命名卷。
- `app-data-init`：首次部署时将当前 `data/` 和 `logs/` 复制到 Docker 命名卷；已有文件不会被覆盖。
- `ontology-init`：Neo4j 就绪后，从 `src/ontology/wiki_kb/` 幂等加载全部本体和索引。
- `app`：FastAPI、G6 前端、SQL 助手、Chroma 向量库和会话存储。

应用镜像内预缓存了 Chroma 查询所需的多语言 Embedding 模型，因此保留
`HF_HUB_OFFLINE=1` 和 `TRANSFORMERS_OFFLINE=1` 也可离线运行。镜像因此会较大，
首次构建需要下载 Python AI 依赖和模型。

## 1. 准备 Ubuntu 26.04

以下命令均在 Ubuntu 26.04 服务器执行。先更新系统并安装 Git、curl：

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git ca-certificates curl
```

建议配置：

- 4 核或更多 CPU
- 8 GB 或更多内存
- 20 GB 或更多可用磁盘
- 能访问 GitHub、Docker Hub、PyPI、`download.pytorch.org`、Microsoft 软件源和 Hugging Face

应用固定使用 PyTorch 官方 CPU wheel，不需要安装 NVIDIA 驱动、CUDA Toolkit
或 `nvidia-cuda-*` Python 运行包。

## 2. 安装 Docker Engine 和 Compose

添加 Docker 官方软件源：

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

sudo apt update
sudo apt install -y \
  docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
```

启动 Docker 并验证：

```bash
sudo systemctl enable --now docker
sudo docker run --rm hello-world
sudo docker version
sudo docker compose version
```

可选：允许当前用户不加 `sudo` 使用 Docker：

```bash
sudo usermod -aG docker "$USER"
newgrp docker
docker version
```

Docker 用户组等同于较高的主机权限，只应加入可信用户。

## 3. 从 GitHub 获取源码

创建部署目录并克隆 `main` 分支：

```bash
sudo mkdir -p /opt/camstar-ontology
sudo chown "$USER":"$USER" /opt/camstar-ontology

git clone --branch main --single-branch \
  https://github.com/yanghengde/CamstarSemiOntology.git \
  /opt/camstar-ontology

cd /opt/camstar-ontology
git log -1 --oneline
```

确认仓库中存在 Docker 文件：

```bash
ls -l Dockerfile compose.yaml
```

当前 Docker 部署首次加入的提交为
`dbb8ab9 feat: add Docker containerization support...`；后续提交号变化是正常的。

## 4. 创建运行配置

从示例生成 `.env`：

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

至少修改：

```dotenv
NEO4J_PASSWORD='请替换为至少16位的强密码'

APP_BIND=0.0.0.0
APP_PORT=5050

DEEPSEEK_API_KEY='使用智能问答时填写'
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

如果暂时只使用图谱浏览、不使用 AI 问答，可以暂不配置有效的
`DEEPSEEK_API_KEY`。SQL Server 连接参数也只在运行 ETL 或访问源数据库时需要。

创建运行目录并验证 Compose：

```bash
mkdir -p backups data logs
docker compose config --quiet
```

容器内应用固定使用 `bolt://neo4j:7687`，所以 `.env` 中原有的 `NEO4J_URI` 不需要手工修改。

## 5. 构建并启动

```bash
docker compose build
docker compose up -d
docker compose ps
```

首次构建会下载 Python 依赖和 Embedding 模型，耗时取决于网络。跟踪初始化：

```bash
docker compose logs -f neo4j ontology-init app-data-init app
```

看到 `ontology-init` 状态为 `Exited (0)` 是正常的，它是一次性初始化容器。
按 `Ctrl+C` 只会退出日志查看，不会停止服务。

部署完成后访问：

- Web：`http://服务器IP:5050`
- 健康检查：`http://服务器IP:5050/healthz`
- Neo4j Browser：默认仅服务器本机可访问 `http://127.0.0.1:7474`

服务器本机验证：

```bash
curl -fsS http://127.0.0.1:5050/healthz
docker compose ps
```

健康检查应返回：

```json
{"status":"ok"}
```

## 6. 配置防火墙

若已启用 UFW，只开放 SSH 和 Web：

```bash
sudo ufw allow OpenSSH
sudo ufw allow 5050/tcp
sudo ufw status
```

不要将 7474/7687 直接开放到公网。远程维护可使用 SSH 隧道：

```bash
ssh -L 7474:127.0.0.1:7474 -L 7687:127.0.0.1:7687 user@server
```

建立隧道后，在本机浏览器访问 `http://127.0.0.1:7474`，用户名为
`neo4j`，密码为服务器 `.env` 中的 `NEO4J_PASSWORD`。

## 7. GitHub 中的数据范围

从 GitHub 克隆后，仓库中已跟踪的 `data/vector_store/` 会由
`app-data-init` 自动复制到 Docker 的 `app_data` 命名卷。本体 JSON 会由
`ontology-init` 自动写入新的 Neo4j。

以下内容不会保存在 GitHub，需要单独从旧环境迁移：

- `.env` 和其中的密码、API Key
- `logs/`
- 未提交的聊天会话或其他 `data/` 文件
- 旧 Neo4j 中无法通过本体 JSON 重建的实例数据

可从旧机器复制文件数据：

```bash
rsync -a old-user@old-server:/旧项目路径/data/ ./data/
rsync -a old-user@old-server:/旧项目路径/logs/ ./logs/
docker compose run --rm app-data-init
docker compose restart app
```

数据初始化只复制目标卷中尚不存在的文件，不会覆盖已存在的数据。

## 8. 迁移已有 Neo4j 数据库

默认的 `ontology-init` 会从 JSON 重建项目本体。如果旧库还包含无法由仓库重建的实例数据，应在旧 Neo4j 主机上使用相同主版本的 `neo4j-admin database dump` 导出。

将导出的 `neo4j.dump` 放到新服务器的 `backups/` 后，在首次导入前执行：

```bash
docker compose down
docker compose run --rm --no-deps --user 0 neo4j \
  neo4j-admin database load neo4j \
  --from-path=/backups --overwrite-destination=true
docker compose up -d
```

导入旧数据库后，数据库中的旧认证信息会优先于 `NEO4J_AUTH`；此时应继续使用旧密码，或按 Neo4j 官方流程重置密码。若旧库仅含本体节点，不需要 dump，直接让 `ontology-init` 重建即可。

## 9. 数据位置与备份

查看命名卷：

```bash
docker volume ls --filter name=camstar-ontology
docker compose exec app python -c \
  "from pathlib import Path; print(list(Path('/app/data').iterdir()))"
```

备份 Neo4j 前先停止写入和数据库，然后用一次性容器生成 dump：

```bash
docker compose stop app neo4j
docker compose run --rm --no-deps --user 0 neo4j \
  neo4j-admin database dump neo4j \
  --to-path=/backups --overwrite-destination=true
docker compose up -d
```

应用文件数据可从命名卷导出：

```bash
docker run --rm \
  -v camstar-ontology_app_data:/source:ro \
  -v "$PWD/backups:/backup" \
  alpine tar czf /backup/app-data.tar.gz -C /source .
```

## 10. 从 GitHub 更新和日常操作

```bash
# 查看状态和日志
docker compose ps
docker compose logs --tail=200 app neo4j

# 从 GitHub 更新源码
git pull --ff-only origin main

# 重建应用；命名卷不会被删除
docker compose build app ontology-init app-data-init
docker compose up -d

# 手工重新加载本体
docker compose run --rm ontology-init

# 停止但保留数据
docker compose down
```

不要执行 `docker compose down -v`，除非确定要删除全部 Neo4j、Chroma、会话和日志卷。

若启动失败：

```bash
docker compose ps -a
docker compose logs --tail=300 neo4j ontology-init app
docker system df
free -h
df -h
```

## 11. 容量调优

默认 Neo4j 配置为 512 MB 初始堆、2 GB 最大堆、1 GB page cache。可在 `.env` 中调整：

```dotenv
NEO4J_HEAP_INITIAL=1g
NEO4J_HEAP_MAX=4g
NEO4J_PAGECACHE=2g
```

修改后执行 `docker compose up -d` 使 Neo4j 重建容器。生产环境建议在 5050 前部署 Nginx/Caddy 和 TLS。
