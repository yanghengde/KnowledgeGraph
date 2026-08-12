# Camstar SQL 学习图谱清理分析

## 目标

本图谱用于 IT 人员理解 Camstar 后台业务对象、物理字段和外键路径，并据此编写 SQL。清理遵循以下边界：

- 保留制造业务主数据、生产事务、质量、设备、物料、工艺、人员组织和历史查询对象。
- 排除访问控制、CIO 集成、消息通知、UI/门户和通用后台配置等技术对象。
- 排除类节点及其图关系，但不删除保留业务类上的真实物理字段。业务表中的 `SetupAccessId`、`ChangeHistoryId` 等列仍会显示，避免 SQL 字段信息丢失。
- `Database_Tables.csv` 与 `Database_Fields.csv` 始终保持只读、完整，仍是物理事实来源。

## 主要复杂度来源

清理前共有 579 个类节点、7,749 个属性节点和 2,163 条本体关系。

| 技术对象 | 连接数 | 判断 |
|---|---:|---|
| `ChangeStatus` | 398 | 建模发布与变更审计公共表，不代表制造业务关系 |
| `A_SetupAccess` | 355 | 半导体建模访问控制公共表，对大量业务对象形成无差别辐射 |
| `WIPMsgDefMgr` | 60 | 车间消息定义和分发配置 |
| CIO 三个模块 | 约 162 个关联端点 | 连接、通道、消息映射、模板和编排属于系统集成传输层 |
| `A_EmailGroup` | 27 | 邮件通知配置 |

## 审核后的排除范围

排除范围保存在 `src/ontology/sql_learning_scope.json`，共 69 个精确类名：

| 类别 | 节点数 | 说明 |
|---|---:|---|
| CIO 集成与消息编排 | 34 | CIO 连接、通道、映射、模板、工作流和协议参数 |
| 访问控制与权限 | 5 | SetupAccess、权限定义和安全组 |
| 建模变更审计状态 | 1 | ChangeStatus |
| 界面与门户配置 | 7 | 菜单、Portal 页面、UI 偏好和显示资源 |
| 消息、邮件与通知配置 | 13 | WIP 消息、邮件、通知变量和 SignalR |
| 电子签名技术配置 | 5 | 签名含义、角色和建模认证要求 |
| 通用后台与查询配置 | 4 | 过滤标签、字典、用户查询和汇总展示定义 |

`Employee`、`Role`、`Approval`、`Activity`、`HistoryMainline`、打印、标签、KPI 和业务告警等对象保留，避免把业务操作、合规流程或实际查询路径误判为纯技术配置。

## 预期结果

清理后保留 510 个类节点、6,807 个属性节点和 1,196 条关系；删除 69 个类节点、942 个仅属于排除类的属性节点及 967 条相关关系。关系数量下降约 44.7%，图的公共辐射中心被移除。

清理脚本默认为预览模式：

```powershell
python scripts/maintenance/apply_sql_learning_scope.py
```

执行写入时会先在 `data/ontology_backups/` 下创建时间戳备份：

```powershell
python scripts/maintenance/apply_sql_learning_scope.py --apply
```
