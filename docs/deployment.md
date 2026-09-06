# 部署

应用依赖现有 PostgreSQL、Camstar SQL Server/Oracle 和 Graph Studio，不再启动独立建模图数据库。

1. 配置 `.env` 中的源库、PG 和 Graph Studio 参数。容器中 `127.0.0.1` 指向容器自身，需使用容器可达的数据库地址。
2. 如需本机 PostgreSQL，使用 `deploy/graphstudio-sync/` 下的 compose 文件；连接现有数据库时无需启动新实例。
3. 运行 `docker compose build`，镜像在构建阶段生成前端；不安装本地嵌入模型和 GPU/向量检索依赖。
4. 初始化控制面后运行 `docker compose up -d app`。命令参数见 `python scripts/graphstudio_sync.py --help`。
5. 检查 `/healthz`，再在控制台测试源库和 Graph Studio 连接。

`data/`、`logs/` 和 `outputs/graphstudio/` 通过宿主机目录保存。升级不清空 PG、活动版本或发布制品。

部署模板不会自动发布到 Graph Studio。启用计划任务前先完成数据校验、Dev 发布与回滚验证。
