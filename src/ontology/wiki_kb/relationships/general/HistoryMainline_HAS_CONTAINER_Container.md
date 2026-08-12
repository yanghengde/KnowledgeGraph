# HistoryMainline → HAS_CONTAINER → Container

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-08-04
> **来源**: 物理 Schema + LLM

## 关系说明

HistoryMainline 是 Opcenter (Camstar) 中记录车间事务（Transaction）主数据的核心实体，它承载了每次业务操作的类型、时间、执行者、备注以及操作前后的状态快照。而 Container 则是车间中物料流转的实际载体，小到一个单品（Unit），大到一个批次（Batch）、托盘（Pallet）或整箱（Box）。HAS_CONTAINER 关系将每一次历史事务与其作用的物理 Container 绑定起来，从而形成一条完整的“容器生命周期”审计链。

从业务视角看，这个关系的本质是 **把“发生了什么”与“发生在哪个对象上”进行关联**。由于基数为 MANY_TO_ONE，即一个 Container 在其生命周期中会对应大量 HistoryMainline 记录（每个记录是一次事务），这使得业务人员可以随时通过 Container 反查其完整历史轨迹，也可以从某条历史记录追溯到当时涉及的容器。在通用（无产品线）场景中，无论是离散制造还是流程制造，这个关系都是车间追溯（Traceability）和审计合规（Compliance）的基石。

该关系在物理实现上由 HistoryMainline 侧持有 Container 的引用（外键），但在业务语义上，它表达的是“容器 - 历史”之间的主从关系：容器是主数据，历史是附属的明细事务。系统中所有涉及容器状态变化、属性变更、位置移动、质量处理的操作，都会在 HistoryMainline 中生成记录并通过此关系与容器绑定，这保证了任何时刻都能回答“这个容器经历过什么”的问题。

## 业务场景

### 何时需要配置此关系？

**场景 1：容器全生命周期追溯**
当质量部门需要排查某批次产品是否受到某个工艺参数异常影响时，需要从一个已知的 Container 编号出发，查询其从投产到入库的所有事务历史。此时必须依赖 HAS_CONTAINER 关系，通过 Container 反查与之关联的全部 HistoryMainline 记录，还原每一步操作的时间、操作员、设备、工艺参数快照，从而精确圈定受影响的范围。

**场景 2：车间异常分析与返工跟踪**
当工人在生产过程中发现某个容器（如托盘）上的物料有质量瑕疵，执行返工（Rework）或报废（Scrap）操作时，系统会在 HistoryMainline 中记录本次返工事务，并通过 HAS_CONTAINER 与此容器关联。业务人员可以通过查询该容器的历史记录，分析返工原因、追溯返工前后状态差异，并进一步评估同类容器是否存在相同风险。

**场景 3：审计合规与客户投诉处理**
在医疗器械、汽车零部件等法规严苛的行业，客户投诉某批次产品时，需要提供该批次对应 Container 的全套生产履历。通过 HAS_CONTAINER 关系，可以完整列出该 Container 的所有 HistoryMainline 记录（包括加工、检验、转移、包装等事务），形成不可篡改的证据链，满足监管审计要求。

### 通用 (无产品线) 典型示例

以一条通用的离散装配线为例（无特定产品线绑定），容器类型为“托盘（Pallet）”，每个托盘装载 10 个产品单品。

**示例背景：**
- 容器编号：PLT-20250607-008
- 产品：某通用机械部件
- 工艺路线：操作 10（上料）→ 操作 20（装配）→ 操作 30（测试）→ 操作 40（包装）
- 当前状态：已完成操作 20，等待进入操作 30

**操作步骤：**

1. **在 Opcenter 客户端打开“容器查询”界面**，输入容器编号 PLT-20250607-008，回车查询。
2. **点击“事务历史”标签页**，系统会通过 HAS_CONTAINER 关系自动检索该 Container 关联的所有 HistoryMainline 记录，默认按时间倒序排列。
3. 浏览历史记录列表，可以看到：
   - 操作 10 上料事务：记录操作员“Zhang San”、时间 09:12、设备“SMT-Line-01”、事务类型“Container Start”。
   - 操作 20 装配事务：记录操作员“Li Si”、时间 10:45、设备“Assembly-Station-03”、事务类型“Move/Complete”，并包含装配参数快照。
   - 每条记录中均可看到 Container 的引用，即 HAS_CONTAINER 关系扮演的角色。
4. **点击某条历史记录的“查看详情”**，可以在 HistoryMainline 详情中看到与该事务关联的完整数据（注释、状态变迁、属性变更等），同时确认该事务对应的是哪一个 Container。

**参数说明：**
- 事务类型（Transaction Type）：Move / Complete、Container Start、Scrap、Rework 等
- 容器状态（Container Status）：InProcess / Completed / Held / Scrapped 等，每条 HistoryMainline 记录会保存操作后的容器状态快照
- 操作员（Owner）：执行该事务的用户账号
- 备注（Comments）：操作员手工录入或系统自动写入的批注

通过这一流程，业务人员无需查阅纸质记录或自建 Excel 台账，即可直接获得该容器从创建到当前状态的全部事务履历，且每条履历都通过 HAS_CONTAINER 关系与容器精确关联。

## 配置要点

1. **不要在无实际业务需求时人为创建“孤儿”HistoryMainline 记录**：每条历史记录都应通过 HAS_CONTAINER 关系关联到一个真实存在的 Container，否则会破坏追溯链的完整性。

2. **理解 MANY_TO_ONE 的语义方向**：HistoryMainline 是关系的“多”侧，Container 是“一”侧。容器删除（如报废后清库）时，不应物理删除关联的历史记录，而应保留 Container 主数据（或在历史记录中冗余容器标识），确保审计可查。

3. **在建模时注意 Container 类型与 HistoryMainline 的匹配**：通用场景中，Container 可能细分为 Unit、Batch、Pallet、Box 等子类型，HAS_CONTAINER 关系在模型中应建立在 HistoryMainline 与 Container 基类上，子类型自动继承该关系，无需重复建立。

4. **关注历史数据的归档策略**：由于一个 Container 可能关联成百上千条 HistoryMainline 记录，长期运行后数据量会显著增长。应根据业务需要配置历史数据归档（Archive）方案，但归档后仍需保证通过 Container 查询历史的可用性。

5. **在 UI 导航（Navigation）配置中，重视“Container → HistoryMainline”的查询路径**：默认客户端提供了容器事务历史页面，但如果定制化了页面，需要确保从 Container 页面导航到历史列表时，过滤条件基于 HAS_CONTAINER 关系，而非手动拼接查询逻辑。

6. **利用 HistoryMainline 的静态属性（Info）存储业务关键快照**：例如在事务发生时将容器的批次号、工单号、工艺路线版本等属性写入 HistoryMainline 的扩展字段，这样即使 Container 关联关系断裂（如合并拆批），历史查询仍能通过静态属性还原业务上下文。

7. **注意权限控制**：HistoryMainline 中可能包含质量数据、返工原因等敏感信息，通过 HAS_CONTAINER 查询历史时，应配置对象级别的访问权限（如仅允许质量工程师查看完整历史），避免生产操作员看到超出权限的审计信息。

8. **不要在事务处理逻辑中手动维护 HAS_CONTAINER 关系**：该关系由 Opcenter 事务引擎在执行标准事务（如 Move、Complete）时自动创建。如果业务需要自定义事务代码，应继承标准事务处理模型，确保 HistoryMainline 与 Container 的关系由框架自动写入，避免因手工赋值导致的关联缺失或错误。

## 常见问题 FAQ

**Q: 一个 Container 在多次返工后，它的历史记录是全部保留，还是会覆盖之前的记录？**
A: 全部保留。HAS_CONTAINER 是 MANY_TO_ONE 关系，每一次返工事务都会生成一条新的 HistoryMainline 记录，并追加到该 Container 的历史列表中，不会覆盖前一次的记录。这也是追溯的核心理念：每次事务都是不可变的审计条目，历史记录只会追加，不会修改或删除。返工时通过不同的事务类型（如 Rework、Material Return）区分不同性质的操作，业务人员可以按事务类型过滤历史列表。

**Q: 如果我通过 Container 查询历史，发现某些 HistoryMainline 记录对应的容器不是当前看到的这个，这是怎么回事？**
A: 这种可能性有两种：一是容器发生过合并（Merge）或拆分（Split）操作，例如多个子容器合并为一个父容器后，子容器的一些历史记录可能通过事务关联到了父容器；二是历史记录所关联的 Container 对象已被物理删除或重新建模，导致 UI 显示时只展示容器标识符而无法展示完整容器信息。建议在查询时明确容器层级关系，并通过 HistoryMainline 中保存的事务描述（Transaction Description）和注释来分辨历史记录的上下文。如果确实发现关联错误，需要检查是否有自定义代码手动更改了该关系——标准系统中该关系由框架维护，不会自动变更。

**Q: 如何区分 HistoryMainline 中哪些事务是直接作用于 Container，哪些是作用于 Container 内的产品（如单品）？**
A: 这是一个重要的业务语义区分。在 Opcenter 中，HistoryMainline 关联的可能是 Container 本身，也可能是 Container 内部的某个具体对象（如 Container 内的单品、组件批次）。区分方法主要有三种：第一，查看 HistoryMainline 的记录类别（Category）和事务类型（Transaction Type）——例如“Container Start”“Container Complete”明确作用于 Container，而“Product Track In”“Component Consume”则作用于更细粒度的对象；第二，查看该事务关联的 Container 引用是否就是当前查询的容器——如果是，说明直接作用于该容器；第三，检查 HistoryMainline 的关联对象字段，通常 HistoryMainline 除了 HAS_CONTAINER 关系外，还有对其他对象（如 Product、Resource、Component）的关联关系。建议在查询历史时，同时查看这些关联对象来确定事务的作用层次。