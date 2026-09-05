# 项目精简记录（2026-09-05）

本轮以 CSV → PostgreSQL → Graph Studio 为主线检查引用，移除不参与运行的内容。

## 已移除

- `scratch/` 中 17 个一次性调试脚本和结果文件：仓库运行代码不引用该目录；其中的路径算法探针不属于正式测试套件。
- 根目录 `check_site.py`：仅打印固定本体 JSON 中的 Site 关系，没有调用入口。
- `frontend/src/pages/OntologyGovernancePage.tsx`：没有 import 或路由引用；原 `ontology-governance` 地址已重定向至 `ontology-model`，继续使用 `SemanticModelPage` 和现有工作区组件。
- `outputs/camstar_presentation_build/` 中 74 个受版本控制的临时制作文件，包括旧目录硬编码制作脚本、临时 FFmpeg 依赖、截图和中间视频。最终 PPTX、MP4、字幕和旁白文件保留；旧制作材料可从 Git 历史恢复。本轮未清扫未跟踪的本地文件。
- `get_shortest_path_details`：仅由已删除的 scratch 探针使用。实际问答使用的路径检索函数保留。
- `web/shared.py` 中未使用的 `_chat_sessions`：当前会话由专用 session store 管理。

合计删除 93 个文件、约 112.33 MiB 受版本控制的文件内容。Git 历史没有重写，因此现有 `.git` 体积不会随本轮删除立即缩小。

## 防止再次膨胀

Git 忽略 scratch、tmp、pytest 缓存、临时演示制作目录及各层 node_modules。Docker 构建排除本机 node_modules、前端旧构建产物、测试及缓存；前端仍在独立构建阶段通过 `npm ci` 和 `npm run build` 生成。

## 保留原因

- `src/graphstudio_sync/`、CSV 事实源、本体 JSON、模型版本和发布审计产物是当前主链路资产。
- SQL Builder、Wiki、问答仍有实际页面/API 入口；发布编译器也直接依赖 `src.qa.sql_query_builder`。不能按旧目录名称整批删除。
- Neo4j 兼容加载器、迁移工具、旧 ETL 暂时保留。Graph Studio 服务当前关机，真实发布观察尚未完成。
- 未修改数据库内容、发布 checkpoint、连接配置或运行服务。

## 验证

- 发布模型、PostgreSQL 后端、SQL Builder、本体权威/导入和制造问答测试：61 通过，1 项需显式开启的 PG 集成测试跳过。
- 前端 TypeScript 检查和 Vite 生产构建通过。
- `git diff --check` 通过；删除的页面及函数在剩余运行代码中无引用。
