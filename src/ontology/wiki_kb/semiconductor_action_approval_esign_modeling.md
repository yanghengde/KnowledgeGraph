# 动作审批与电子签名 / Action, Approval, and Electronic Signature

## 中文

补齐动作规则、活动阶段、审批和电子签名相关的物理配置实体。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `ActionCategory`（动作类别）：动作定义的分类主数据。
- `ActionDef`（动作定义）：可由业务规则或流程触发的动作配置。
- `ActionRule`（动作规则）：动作执行条件与规则定义。
- `ActionsMenu`（动作菜单）：操作和界面可用动作的菜单配置。
- `Activity`（活动）：业务过程中的活动配置。
- `ActivityPlan`（活动计划）：活动执行顺序和计划配置。
- `Phase`（阶段）：业务过程或计划中的阶段定义。
- `ApprovalDecision`（审批决定）：审批流程可选决定的主数据。
- `ApprovalDecisionList`（审批决定列表）：审批决定的分组列表配置。
- `ApprovalSheet`（审批表）：审批参与者、路由和决定的配置载体。
- `AlarmDefinition`（告警定义）：告警消息、优先级、动作和通知配置。
- `AttachedDocs`（附件文档配置）：建模对象所附文档集合的配置实体。
- `ModelingESigReq`（建模电子签名要求）：建模变更所需电子签名规则。
- `ESigMeaning`（电子签名含义）：电子签名业务含义的主数据。
- `ESigCosignReason`（电子签名会签原因）：电子签名会签场景使用的原因代码。

## English

Adds physical configuration entities for actions, activities, approvals, alarms, and electronic signatures.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
