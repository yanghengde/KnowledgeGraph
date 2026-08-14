# src/graphstudio_sync 核心同步模块代码评审报告

**审查范围**：src/graphstudio_sync/ 全部 26 个文件（约 13,300 行），并交叉验证 sql/graphstudio_sync_control_postgres.sql。
**结论日期**：本次评审会话

## 一、整体架构评价（优点）

1. **不可变发布 + 指针激活 + 常量时间回滚**是最出色的设计（materialization.py:1092-1164）：新 release 在隔离中构建，curated_release_activation 保存 active_release_id/previous_release_id 指针，激活/回滚只是两行 UPDATE + 状态翻转。
2. **防重叠控制到位**：materialize（materialization.py:543）、preview（preview.py:1093）、curation（curation.py:387）、incremental-preview（incremental_preview.py:168）、continuous（continuous_sync.py:206）均使用 pg_try_advisory_lock 会话锁，finally 中释放；进程崩溃由 PostgreSQL 会话终结自动释放。
3. **先验证后提交 checkpoint 落实在事务边界**：deployment.py:1171-1242 在同一事务内完成 status='active'、target_release_activation upsert、checkpoint ON CONFLICT DO UPDATE、增量窗口 verified→committed。
4. **控制面 SQL 全部参数化**：repository.py 未发现 SQL 注入，text() + 绑定参数贯穿始终。
5. **标识符白名单校验是亮点**：preview.py:197、curation.py:36、attribute_projection.py:63、change_capture.py:26 均先 SAFE_IDENTIFIER 正则校验再引号化，fail-closed。
6. **治理流程完整**：Action 双人审批（reviewer≠approver，actions.py:182-183）、幂等键 + 请求哈希回放（actions.py:317-325）、补偿 Action 模式、Schema 变更兼容性分类与回滚、本体发布内容哈希去重（publish_ontology.py:860-870）。
7. **密码不落库**：PostgreSQL 只存 secret_ref（database.py:81,95,119），真实密码全部来自环境变量。
8. **本体固定不变量**（continuous_sync.py:145-148）防止数据同步期间本体切换导致错配发布。
9. RDF 产物有确定性序列化、round-trip 三元组计数校验、ZIP CRC 校验（preview.py:181-194, 987-992）。

## 二、问题清单（按严重度分级）

### 🔴 严重

**S1. SQL 注入：增量探测/水位读取路径对标识符只引号化、不校验**
- 位置：incremental.py:184-187（Oracle flashback 探测）、incremental.py:257-259（read_watermark_upper_bound）
- 代码：f"SELECT MAX({quote_identifier(watermark_column, ...)}) ..." — 直接拼接 quote_identifier 结果。SQL Server 的 [x] 遇到 ]、Oracle 的 "x" 遇到 " 均可逃逸闭合。
- 为什么是问题：watermark_column 是用户可通过 Web UI 配置的 table_sync_policy 字段（repository.py:330-400 原样落库），没有经过 SAFE_IDENTIFIER 校验——而同模块 change_capture.py:26 的 _identifier 是先校验后引号化。从 UI 到业务源库（Camstar 生产库）的注入链，且与模块自身防御标准不一致。
- 修复：统一改用 change_capture._identifier 式「正则校验 + 引号化」，或写入策略时强制校验 watermark_column 格式。

**S2. 任意文件读取/数据注入：materialization 信任 DB 中的 changeFile 路径**
- 位置：materialization.py:773-775
- 代码：change_path = Path(contract_plan["incrementalWindow"]["changeFile"]); change_path.open("r")
- 为什么是问题：changeFile 来自 incremental_window.metadata（DB 数据），未校验其必须位于 INCREMENTAL_PREVIEW_ROOT 之下。能写 incremental_window 的角色可指向任意可读文件（如 .env，含全部密码），文件被按 JSONL 解析写入 object_version → 密钥外泄 + 数据注入。
- 修复：resolve() 后校验 change_path.is_relative_to(INCREMENTAL_PREVIEW_ROOT)，并校验 class_name 与 run_id 目录结构。

### 🟠 中等

- **M1** materialization.py:918-946 关系物化 SQL 用手工单引号转义拼接（chr(39) 双写与反斜杠风格不一致），难审计易回归；建议参数化 JSONB 路径访问（#>）或 SAFE_IDENTIFIER 白名单。
- **M2** materialization.py:1108-1125 activate_release 指针切换竞态：并发激活各锁自己的 release 行，previous_release_id 可能被覆盖，回滚链破坏；CLI/API 独立调用路径无 advisory lock。修复：FOR UPDATE 或对 graphsync:activate:{profile_key} 加锁。
- **M3** deployment.py:934-960,1037-1107 apply_deployment 无并发锁 + uploading/loading 中间态无重试入口，进程被杀后状态卡死。修复：原子抢占 UPDATE ... SET status='applying' ... RETURNING。
- **M4** preview.py:627,760 全量预览对未解析类必然 KeyError（list_table_policies 只返回 resolved 类，而目录含 unresolved 类）；应跳过并记录。
- **M5** schema_evolution.py:373-376 依赖键生成 "None.<field>"：全仓没有任何代码写 data_contract.config.targetTable，血缘数据被污染。
- **M6** materialization.py:372-383 字段回填无法表达「值变为 NULL」（None 被跳过 + jsonb 合并），增量升级后与源不一致，静默数据正确性缺陷。
- **M7** incremental_preview.py:196 类名直拼文件名未消毒（preview.py:794 同类做了清洗），可越界写文件，且与 S2 形成传递链。
- **M8** deployment.py:1125-1139 SPARQL 验收拼接未校验 URI 合法性（targetName 只校验非空），含空格/'>' 可破坏 SPARQL 语法。
- **M9** deployment.py:448-540 蓝绿发布与 RDF 构建全量驻留内存（object_version 全量 SELECT + rdflib Graph + zip bytearray），亿级大表下是伸缩性瓶颈。
- **M10** actions.py:317-325 Action 幂等检查 TOCTOU：先 SELECT 后 INSERT，并发同键抛 IntegrityError 而非重放；改 INSERT ... ON CONFLICT DO NOTHING RETURNING。
- **M11** materialization.py:460-461 物化计划硬编码 job_name "camstar-full"，与入参 profile_key 无关；profile 绑定其他 job 时策略/窗口取错。
- **M12** attribute_projection.py:275-289 类型转换异常（int/float 抛 ValueError）中断整个 release，应 quarantine 而非回滚。
- **M13** repository.py:1437-1462 update_data_contract 升版本但不更新 data_contract_field 的 field_role/required，契约列与字段明细漂移。

### 🟡 轻微（摘要）

L1 ZIP 字节手术两份重复实现（deployment.py:532-540 与 preview.py:203-212），偏移写死 +38/+46，Zip64 下错位；L2 repository.py 7 处 locals() 作绑定参数；L3 continuous_sync.py:54-62 用中文前缀字符串过滤 blocker；L4 requests.Session 两处未关闭；L5 observability.py 非法规则配置 KeyError/ValueError；L6 create_data_contract 无 ON CONFLICT；L7 进程被杀遗留孤儿运行记录（materialization/deployment/run_manager/preview 四处）；L8 inventory.py normalize_identifier 归一化碰撞（A_B 与 AB 同键）；L9 publish_ontology.py:19 依赖 src 命名空间包，打包受限；L10 actions.py:533-538 补偿失败把原调用改回 succeeded 状态机混乱；L11 preview.py:913-922 采样 O(n²)；L12 失败产物目录永久累积；L13 compile_catalog 无并发锁；L14 incremental_preview.py:211-213 写后重读全文件翻倍 I/O。

## 三、重点安全边界核查结论

| 关注点 | 结论 |
|---|---|
| SQL 注入 | 控制面（repository.py）无；incremental.py:184/257 漏检（S1）；materialization 关系 SQL 手工转义（M1）；SPARQL 拼接（M8） |
| 密码/密钥泄露 | 密码仅环境变量、内存持有，DB 只存 secret_ref ✅；S2 任意文件读取是唯一密钥外泄路径 |
| 事务一致性 | checkpoint 与激活同事务 ✅；update_data_contract 字段漂移（M13） |
| 幂等性 | 物化/发布整体幂等设计好；Action 幂等键 TOCTOU（M10） |
| 并发控制 | 主通道 advisory lock 完整；激活（M2）、发布（M3）、编译目录（L13）三个独立路径缺锁 |
| 路径穿越 | 预览/物化输出目录基于 UUID ✅；incremental_preview.py:196 类名未消毒（M7）+ materialization.py:773 信任 DB 路径（S2） |
| 资源泄漏 | 连接均 with/finally 关闭 ✅；requests.Session 两处未关（L4）；ZIP 全量驻留（M9） |

**优先级建议**：先修 S1（注入）、S2（任意文件读）；再修 M2/M3（并发与状态机，直接威胁发布安全边界）和 M4/M5/M6/M7（数据正确性）；其余按影响排期。
