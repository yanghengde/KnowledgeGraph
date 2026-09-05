# Graph Studio HTTPS 直传发布

## 当前配置与验证

- API 入口：`https://gs.siemens-icx.com.cn:8443`。浏览器的 `/sdl/index.html#/...` 不是 API 路径，配置加载时会自动规范化。
- 已验证 REST API `6.3.2.r202607081222`。
- `.env` 中设置 `GRAPHSTUDIO_PUBLISH_TRANSPORT=inline_query`。旧的 `shared_store` 模式仍可显式配置。
- 自签名证书使用 `GRAPHSTUDIO_TLS_FINGERPRINT` 配置 SHA-256 指纹，校验仅作用于指定 Graph Studio 地址。其他 HTTPS 请求继续使用标准 CA 校验。首次记录指纹后，证书变化将拒绝连接；换证时需核实后更新指纹。
- 2026-09-05：开发环境部署 `ceb6fe6a-c994-4dd0-8347-86c40249020a` 已成功。新数据层查询结果为 26 个对象、17 条关系，失败层/步骤/Dataset 均为 0。原 Dataset 保留。

## 实现

从已批准版本的 RDF ZIP 读取数据，核对模型与 ZIP 的组合校验值，生成 `INSERT DATA` Query Step，通过 HTTPS 保存到 Graph Studio。Graph Studio 激活数据层时执行保存的查询，不需要 Graph Lakehouse 访问本机下载地址或该版本的 FLDS 文件。

API 6.3.2 使用 `QueryStep.transformQuery`；保存后通过 `GET /api/steps/{uri}?expand=transformQuery` 逐字核对查询。已有 LoadDatasetStep 不能变更类型，因此迁移创建独立的 HTTPS 数据层，停用原失败层，保留其 Dataset、模型及制品。相同路由遗留的失败层也会被停用，记录在 validation_plan，避免它们继续触发文件权限错误。其他路由及活动版本不按此规则停用。

数据库 advisory lock 防止多个进程重叠发布。数据中的空白节点转换为确定性 URI，重试不会增加重复节点。查询保存在 Graph Studio，数据层重新加载时可以重放。仅在加载完成且目标数据层对象数、关系数与期望一致后提交发布 checkpoint。

默认大小上限为 2,000,000 字节，分别检查解压前声明的数据长度及展开后的查询长度，超限拒绝发布，不自动退回已知有权限问题的共享存储。此方式适合当前小型制品；更大规模应接入文件直读或修复共享存储。平台其他使用共享存储的功能并未因此得到修复。

## 官方依据

- [Query Step](https://docs.cambridgesemantics.com/anzo/v5.3/userdoc/step-query.htm)：在数据层保存和运行更新查询；具体 REST 字段以上述实例实测为准。
- [图存储机制](https://docs.cambridgesemantics.com/anzo/userdoc/data-storage.htm)：Graph Studio 管理图谱重新加载。此实现保存加载步骤，不依赖一次性的数据库直接写入。
- [IO Load](https://docs.cambridgesemantics.com/anzograph/userdoc/load-io-service.htm)：后续大文件路线可从 HTTP/HTTPS 或对象存储读取 RDF。
