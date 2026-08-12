# Siemens Opcenter MES 数字化本体 300 大应用场景蓝图目录 (Scenarios Catalog)

> [!IMPORTANT]
> 本文档基于 **Camstar / Opcenter MES 数字化本体图谱**，深度汇编了涵盖生产工单、在制品容器、工艺规范、物料配方、设备OEE、工装夹具、质量SPC等 15 大制造核心领域的 300 个数字化场景。
> 所有的场景设计采用**高度易读的业务痛点+数字化对齐设计**模式，支撑后续分批、安全、可回滚的逐步开发，为客户提供直观的数字化价值洞察。

## 15 大业务领域分类导航

1. [生产工单与排产调度 (Production Work Orders & Dispatch Scheduling)](#1-生产工单与排产调度-production-work-orders--dispatch-scheduling)
2. [ SPC 统计质控与判异 (Statistical Process Control & Nelson Rules)](#10-spc-统计质控与判异-statistical-process-control--nelson-rules)
3. [ 不良品审理与 NCR 控制 (Non-Conformance & NCR Workflows)](#11-不良品审理与-ncr-控制-non-conformance--ncr-workflows)
4. [ 现场工艺异常与返工 (Shopfloor Deviations & Rework Routes)](#12-现场工艺异常与返工-shopfloor-deviations--rework-routes)
5. [ 环境温湿度与公用工程 (Environmental Monitoring & Cleanroom Control)](#13-环境温湿度与公用工程-environmental-monitoring--cleanroom-control)
6. [ 包装称重与成品标签 (Packaging, Weighing & Finished Goods Labeling)](#14-包装称重与成品标签-packaging,-weighing--finished-goods-labeling)
7. [ 出货发运与退货 RMA (Shipping Log & Return Material Authorization)](#15-出货发运与退货-rma-shipping-log--return-material-authorization)
8. [在制品容器与追溯 (WIP Container Tracking & Genealogy)](#2-在制品容器与追溯-wip-container-tracking--genealogy)
9. [工艺路线与规范控制 (Process Routing & Spec Integrity)](#3-工艺路线与规范控制-process-routing--spec-integrity)
10. [物料控制与高级 BOM (Material Control & Advanced BOM)](#4-物料控制与高级-bom-material-control--advanced-bom)
11. [工厂结构与制造日历 (Factory Structure & Mfg Calendars)](#5-工厂结构与制造日历-factory-structure--mfg-calendars)
12. [现场数据采集与配方 (Data Collection & Recipe Management)](#6-现场数据采集与配方-data-collection--recipe-management)
13. [设备状态与 OEE 监控 (Equipment States & OEE Telemetry)](#7-设备状态与-oee-监控-equipment-states--oee-telemetry)
14. [工装治具与夹具控制 (Tooling & Life Cycle Tracking)](#8-工装治具与夹具控制-tooling--life-cycle-tracking)
15. [人员资质与安全合规 (Personnel & E-Sign Audit)](#9-人员资质与安全合规-personnel--e-sign-audit)

---

## 1. 生产工单与排产调度 (Production Work Orders & Dispatch Scheduling)

### 📌 SC_001: 多销售订单合并排产工单

- **本体模型映射**: `MfgOrder, BOM, Material, Spec, BusinessRule`
- **业务痛点 (Pain Point)**: 销售小订单散乱，计划员手工排产合单繁琐，导致换线频繁，产能浪费高达30%。
- **数字化映射方案 (Digital Solution)**: 将SalesOrder本体与MfgOrder工单动态合并。系统自动计算最佳经济批重，自动指派合并后工单，避免频繁调机换线。
- **客户易懂价值 (Value to Client)**: *销售订单一键合排，换线频率降低50%，工厂车间生产效率极大提升。*

<!-- slide -->

### 📌 SC_002: 工单多批次容器自动切割派发

- **本体模型映射**: `MfgOrder, Container, Spec, Resource`
- **业务痛点 (Pain Point)**: 大工单投产时，由于手工分批，导致现场条码打印错乱、首尾批次追溯链断档。
- **数字化映射方案 (Digital Solution)**: 在MfgOrder生成时，由系统自动生成对应的批量Container (在制品容器) 谱系，条码由系统原子化生成并绑定CdoId。
- **客户易懂价值 (Value to Client)**: *条码一气呵成，子母容器谱系彻底告别手工账，实现全过程数字化追踪。*

<!-- slide -->

### 📌 SC_003: 紧急插单工单优先级自动提权

- **本体模型映射**: `MfgOrder, BOM, Material, Spec, BusinessRule`
- **业务痛点 (Pain Point)**: 急单来临，纸质排程单无法通知现场，低优先级工单依然占用核心设备，交付延迟严重。
- **数字化映射方案 (Digital Solution)**: MfgOrder定义Priority等级，设备Resource进料时强制检索缓存区内高优先级Container，拒收低优先级Container抢占资源。
- **客户易懂价值 (Value to Client)**: *急单交付率提升35%以上，核心设备产能得到最科学的刚性利用。*

<!-- slide -->

### 📌 SC_004: 跨工厂生产工单动态工艺路线指派

- **本体模型映射**: `MfgOrder, Container, Spec, Resource`
- **业务痛点 (Pain Point)**: 集团多厂区工艺有细微差别，手工指派经常把南京厂的工单发去深圳厂，造成工艺不合。
- **数字化映射方案 (Digital Solution)**: 工艺路线定义为BillOfProcess。系统读取MfgOrder中的生产分厂Organization，自动匹配该区域的Spec子图进行派工。
- **客户易懂价值 (Value to Client)**: *彻底终结派单走错厂区的低级错误，跨厂区调度实现零差错高频运转。*

<!-- slide -->

### 📌 SC_005: 母子工单血统追踪与层级合并

- **本体模型映射**: `MfgOrder, BOM, Material, Spec, BusinessRule`
- **业务痛点 (Pain Point)**: 总装和部件子工单靠纸质单对账，无法追踪子母单进度，半成品积压库房严重。
- **数字化映射方案 (Digital Solution)**: 在MfgOrder间建立Parent-Child拓扑关系，子工单 Container 完工自动触发Move In入母单Container，谱系链条完美绑定。
- **客户易懂价值 (Value to Client)**: *子母工单进度实时可视，消除半成品库房积压，排产精准率大幅提升。*

<!-- slide -->

### 📌 SC_006: 工单BOM动态版本线上零延时切换

- **本体模型映射**: `MfgOrder, Container, Spec, Resource`
- **业务痛点 (Pain Point)**: 工程发布了BOM变更，但已下发的工单仍在用旧版BOM配料，造成大量呆滞料。
- **数字化映射方案 (Digital Solution)**: 使用Change_Management实体。一旦BOM变更审核通过，系统自动将生效工单下的BOM条目进行在线无感更新并锁版。
- **客户易懂价值 (Value to Client)**: *废除纸质变更通知，新BOM秒级生效，呆滞料产生率从源头上彻底清零。*

<!-- slide -->

### 📌 SC_007: 欠料工单自动锁定与上料缺料挂起

- **本体模型映射**: `MfgOrder, BOM, Material, Spec, BusinessRule`
- **业务痛点 (Pain Point)**: 欠料的工单被盲目投产，导致半成品在流水线上堆积，造成严重停线。
- **数字化映射方案 (Digital Solution)**: 工单投产前，BusinessRule检索Inventory库存。若配料缺料率超5%，工单状态自动锁定为Hold，禁止开立Container。
- **客户易懂价值 (Value to Client)**: *生产线只做‘备料充足’的工单，彻底消除停工待料与半成品在线堆积。*

<!-- slide -->

### 📌 SC_008: 工单完工数量超额自动拦截防损

- **本体模型映射**: `MfgOrder, Container, Spec, Resource`
- **业务痛点 (Pain Point)**: 由于操作员马虎，工单超产超做，超出的昂贵产品无法入账，造成企业物料流失。
- **数字化映射方案 (Digital Solution)**: MfgOrder定义PlanQty和MaxOverQty限值。Container完工Scan过站时累加计数，一旦超限，系统自动强行锁站禁止完工。
- **客户易懂价值 (Value to Client)**: *从软件逻辑卡死多做漏报，每年为企业挽回数万元的昂贵原材料损失。*

<!-- slide -->

### 📌 SC_009: 工单工期超时未完工报警预警

- **本体模型映射**: `MfgOrder, BOM, Material, Spec, BusinessRule`
- **业务痛点 (Pain Point)**: 工单生产进度滞后，全靠人工车间清点，等发现交期要超限时，早已无法挽回。
- **数字化映射方案 (Digital Solution)**: 在MfgOrder下挂载Timer。系统动态监控实际产出速度，一旦预估完工时间超过交期Timer设定，自动触发Alarm通知计划员。
- **客户易懂价值 (Value to Client)**: *进度延期提前预警，给计划员充足的调度调整时间，按期交付率提升至98%以上。*

<!-- slide -->

### 📌 SC_010: 定制化销售订单与特定工艺防错绑定

- **本体模型映射**: `MfgOrder, Container, Spec, Resource`
- **业务痛点 (Pain Point)**: 特殊大客户有定制工艺，手工派单极易混装普通工艺，导致整批被大客户拒收退货。
- **数字化映射方案 (Digital Solution)**: 销售订单SalesOrder中关联CustomSpec。在投产工序，系统校验Container所属SO是否绑定定制工艺，错配直接红字打回。
- **客户易懂价值 (Value to Client)**: *让定制化生产的安全防护固若金汤，客户拿到100%符合其定制规格的完美产品。*

<!-- slide -->

### 📌 SC_011: 客户特许工单(Deviation Order)特批校验

- **本体模型映射**: `MfgOrder, BOM, Material, Spec, BusinessRule`
- **业务痛点 (Pain Point)**: 特批偏离工单口头同意，事后没人承认，给工厂带来极大的质量赔偿诉讼风险。
- **数字化映射方案 (Digital Solution)**: 特批工单特定义为DeviationOrder。投产时，强迫进行多人电子签名ESignature确认，签名附带ECO变更编号。
- **客户易懂价值 (Value to Client)**: *偏离审批手续完备，不可篡改，给工厂财务与合规审计提供铜墙铁壁般的合规证据。*

<!-- slide -->

### 📌 SC_012: 多工单联合混料工步合并投产

- **本体模型映射**: `MfgOrder, Container, Spec, Resource`
- **业务痛点 (Pain Point)**: 多个同配方工单需要共用反应釜混料，手工记账经常算错分摊比例，造成损耗黑洞。
- **数字化映射方案 (Digital Solution)**: 多个Container的MfgOrder关联至同一个BatchJob。系统自动按重量比例计算Backflush物料扣减，精确分摊到各Container中。
- **客户易懂价值 (Value to Client)**: *混料公摊科学合理，配方对账精准到毫克级，彻底堵死物料损耗黑洞。*

<!-- slide -->

### 📌 SC_013: 工艺验证工单(Trial Run Order)强制隔离

- **本体模型映射**: `MfgOrder, BOM, Material, Spec, BusinessRule`
- **业务痛点 (Pain Point)**: 研发试跑新产品混入量产线，良率低下却没人发现，直接贴上合格证发货导致爆雷。
- **数字化映射方案 (Digital Solution)**: 实验工单定义为TrialMfgOrder。Container状态自动设为Trial，其工艺路线强制绑定独立质检 Spec 关卡，严禁混入普通放行流。
- **客户易懂价值 (Value to Client)**: *让实验批次绝对在雷达监控下运转，绝无可能混装出货，捍卫出厂良率。*

<!-- slide -->

### 📌 SC_014: 设备产能不足工单动态外协拆包

- **本体模型映射**: `MfgOrder, Container, Spec, Resource`
- **业务痛点 (Pain Point)**: 本厂产能不足需要外协，但手工拆包调拨外协数据极其混乱，进度完全失控。
- **数字化映射方案 (Digital Solution)**: 设备产能不足工单动态外协拆包。系统根据供应商资质动态生成外协Container并绑定ShipRequest出库核销。
- **客户易懂价值 (Value to Client)**: *外协流转进度全透明，外协件按期回厂率从70%提升至95%以上。*

<!-- slide -->

### 📌 SC_015: 工单标准工时比对效能分析

- **本体模型映射**: `MfgOrder, BOM, Material, Spec, BusinessRule`
- **业务痛点 (Pain Point)**: 工单实际工时手工记录水分大，无法评估真实OEE与瓶颈工序效率。
- **数字化映射方案 (Digital Solution)**: 工单Container绑定Employee与Resource的实际时间戳。系统自动比对StandardBOM工时，实时核算效率偏差。
- **客户易懂价值 (Value to Client)**: *告别水份手工账，现场工时效率真实透明，为OEE持续优化提供硬数据支撑。*

<!-- slide -->

### 📌 SC_016: 跨日历班次工单排期冲突防错

- **本体模型映射**: `MfgOrder, Container, Spec, Resource`
- **业务痛点 (Pain Point)**: 排产计划与工厂制造日历脱节，把工单排在设备停电保养期内，造成工人停工待料。
- **数字化映射方案 (Digital Solution)**: 工单排产调度实时与MfgCalendar (制造日历) 强关联。系统自动避开日历中的DownTime，实现日历冲突自动重排。
- **客户易懂价值 (Value to Client)**: *排产计划完美避开停电检修，工人不再停工待料，设备稼动率大幅提升。*

<!-- slide -->

### 📌 SC_017: 瓶颈设备负荷超额工单自动分流

- **本体模型映射**: `MfgOrder, BOM, Material, Spec, BusinessRule`
- **业务痛点 (Pain Point)**: 瓶颈机台前排长队，闲置机台没人管，排产调度全凭操作员心情，物流严重受阻。
- **数字化映射方案 (Digital Solution)**: 定义瓶颈工序Spec。系统实时监测各设备队列，当某设备排队Container超限时，自动将后续工单Container重定向至空闲Resource。
- **客户易懂价值 (Value to Client)**: *瓶颈工序队列平滑分流，车间拥堵程度下降30%，物流如行云流水。*

<!-- slide -->

### 📌 SC_018: 工单物料配比动态追溯

- **本体模型映射**: `MfgOrder, Container, Spec, Resource`
- **业务痛点 (Pain Point)**: 配方物料中含有贵重金属，手工领料对账账实不符，每月盘点差异额高达数万元。
- **数字化映射方案 (Digital Solution)**: 在BOM本体中定义贵金属物料追溯规则。领料时Material与MfgOrder强绑定，使用Backflush精细核销损耗。
- **客户易懂价值 (Value to Client)**: *贵重金属物料日盘点账实相符度提升至99.9%，领料浪费与贪污风险降为零。*

<!-- slide -->

### 📌 SC_019: OEM代工工单双向结算追溯

- **本体模型映射**: `MfgOrder, BOM, Material, Spec, BusinessRule`
- **业务痛点 (Pain Point)**: 代工客户要求物料和产品双向对账，手工整理报表极度缓慢，交货审计通不过。
- **数字化映射方案 (Digital Solution)**: 代工工单映射为OEMOrder。系统自动比对BOM物料投入Supplier批次与成品Container条码，一键输出双向批次Pedigree报告。
- **客户易懂价值 (Value to Client)**: *代工客户对物料追溯报表赞不绝口，一次性通过大客户最严苛的质量合规审计。*

<!-- slide -->

### 📌 SC_020: 工单状态(Draft/Release/Closed)级级审批

- **本体模型映射**: `MfgOrder, Container, Spec, Resource`
- **业务痛点 (Pain Point)**: 工单没有系统状态流转锁，已关闭的工单被员工二次刷条码投料，造成严重混乱。
- **数字化映射方案 (Digital Solution)**: 工单状态机定义严格状态锁。处于Closed状态的MfgOrder，系统底层逻辑直接禁止其接收任何投料及Container过站Move In。
- **客户易懂价值 (Value to Client)**: *历史工单彻底封存，绝对无法重复利用，消灭任何串单与错用工单的系统漏洞。*

<!-- slide -->


---

## 10. SPC 统计质控与判异 (Statistical Process Control & Nelson Rules)

### 📌 SC_181: SPC实时判异与OCAP - 单点超控制限

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 单点超控制限主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕单点超控制限建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_182: SPC实时判异与OCAP - 连续七点同侧

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 连续七点同侧主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕连续七点同侧建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_183: SPC实时判异与OCAP - 趋势漂移

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 趋势漂移主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕趋势漂移建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_184: SPC实时判异与OCAP - 周期性波动

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 周期性波动主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕周期性波动建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_185: SPC实时判异与OCAP - 批内极差异常

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 批内极差异常主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕批内极差异常建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_186: SPC实时判异与OCAP - 均值突变

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 均值突变主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕均值突变建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_187: SPC实时判异与OCAP - 首件数据偏移

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 首件数据偏移主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕首件数据偏移建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_188: SPC实时判异与OCAP - 设备换型后漂移

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 设备换型后漂移主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕设备换型后漂移建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_189: SPC实时判异与OCAP - 供应商批次偏移

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 供应商批次偏移主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕供应商批次偏移建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_190: SPC实时判异与OCAP - 温度补偿失效

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 温度补偿失效主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕温度补偿失效建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_191: SPC实时判异与OCAP - 测量系统偏差

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 测量系统偏差主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕测量系统偏差建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_192: SPC实时判异与OCAP - 抽样频次不足

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 抽样频次不足主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕抽样频次不足建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_193: SPC实时判异与OCAP - 高低限贴边

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 高低限贴边主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕高低限贴边建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_194: SPC实时判异与OCAP - 多线体均值差异

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 多线体均值差异主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕多线体均值差异建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_195: SPC实时判异与OCAP - 关键尺寸失控

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 关键尺寸失控主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕关键尺寸失控建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_196: SPC实时判异与OCAP - 良率突然下滑

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 良率突然下滑主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕良率突然下滑建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_197: SPC实时判异与OCAP - 异常点未闭环

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 异常点未闭环主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕异常点未闭环建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_198: SPC实时判异与OCAP - OCAP执行超时

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: OCAP执行超时主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕OCAP执行超时建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_199: SPC实时判异与OCAP - 复测数据冲突

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 复测数据冲突主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕复测数据冲突建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_200: SPC实时判异与OCAP - 报警后仍放行

- **本体模型映射**: `SPC, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 报警后仍放行主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕报警后仍放行建立数字化校验点，SPCChartDef、BusinessRule、AlarmDef、AlarmLog、Resource 与 Container 联动判异和处置，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *统计失控被即时转成现场拦截动作，异常批次不再后流，并留下可追溯的异常处置证据。*

<!-- slide -->


---

## 11. 不良品审理与 NCR 控制 (Non-Conformance & NCR Workflows)

### 📌 SC_201: MRB不良审理联签 - 外观缺陷待审

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 外观缺陷待审主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕外观缺陷待审建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_202: MRB不良审理联签 - 尺寸偏差特采

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 尺寸偏差特采主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕尺寸偏差特采建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_203: MRB不良审理联签 - 功能失败隔离

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 功能失败隔离主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕功能失败隔离建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_204: MRB不良审理联签 - 客户退货复判

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 客户退货复判主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕客户退货复判建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_205: MRB不良审理联签 - 供应商来料争议

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 供应商来料争议主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕供应商来料争议建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_206: MRB不良审理联签 - 返工后复审

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 返工后复审主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返工后复审建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_207: MRB不良审理联签 - 批量偏离让步

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 批量偏离让步主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕批量偏离让步建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_208: MRB不良审理联签 - 可靠性失败处置

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 可靠性失败处置主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕可靠性失败处置建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_209: MRB不良审理联签 - 混料疑似批审理

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 混料疑似批审理主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕混料疑似批审理建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_210: MRB不良审理联签 - 包装破损判定

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 包装破损判定主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕包装破损判定建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_211: MRB不良审理联签 - 实验批异常评审

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 实验批异常评审主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕实验批异常评审建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_212: MRB不良审理联签 - 生产偏差责任划分

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 生产偏差责任划分主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕生产偏差责任划分建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_213: MRB不良审理联签 - 工程变更偏离

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 工程变更偏离主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕工程变更偏离建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_214: MRB不良审理联签 - 超期库存复检

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 超期库存复检主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕超期库存复检建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_215: MRB不良审理联签 - 运输损伤确认

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 运输损伤确认主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕运输损伤确认建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_216: MRB不良审理联签 - 检验标准冲突

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 检验标准冲突主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕检验标准冲突建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_217: MRB不良审理联签 - 样品破坏性复验

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 样品破坏性复验主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕样品破坏性复验建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_218: MRB不良审理联签 - 报废转特采审批

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 报废转特采审批主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕报废转特采审批建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_219: MRB不良审理联签 - MRB超时未决

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: MRB超时未决主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕MRB超时未决建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_220: MRB不良审理联签 - 审理结论回写

- **本体模型映射**: `Quality, Role, ESignature, Rework`
- **业务痛点 (Pain Point)**: 审理结论回写主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕审理结论回写建立数字化校验点，Event、RoleDef、SignatureRule、SignatureLog、ReworkPath 与 Container 组成 MRB 审理链，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *评审结论出来前系统不放行，审理过程可追溯，并留下可追溯的异常处置证据。*

<!-- slide -->


---

## 12. 现场工艺异常与返工 (Shopfloor Deviations & Rework Routes)

### 📌 SC_221: 返工与强制报废 - 返工次数超限

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返工次数超限主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返工次数超限建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_222: 返工与强制报废 - 返修路线错入主线

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返修路线错入主线主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返修路线错入主线建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_223: 返工与强制报废 - 报废未销账

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 报废未销账主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕报废未销账建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_224: 返工与强制报废 - 返工后漏复测

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返工后漏复测主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返工后漏复测建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_225: 返工与强制报废 - 局部返修工序缺失

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 局部返修工序缺失主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕局部返修工序缺失建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_226: 返工与强制报废 - 返修资源不匹配

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返修资源不匹配主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返修资源不匹配建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_227: 返工与强制报废 - 重工批次混入良品

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 重工批次混入良品主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕重工批次混入良品建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_228: 返工与强制报废 - 返修材料未核销

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返修材料未核销主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返修材料未核销建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_229: 返工与强制报废 - 返修超时未处理

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返修超时未处理主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返修超时未处理建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_230: 返工与强制报废 - 返工路径版本错配

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返工路径版本错配主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返工路径版本错配建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_231: 返工与强制报废 - 返修后状态未恢复

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返修后状态未恢复主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返修后状态未恢复建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_232: 返工与强制报废 - 返修审批缺失

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返修审批缺失主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返修审批缺失建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_233: 返工与强制报废 - 强制报废未隔离

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 强制报废未隔离主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕强制报废未隔离建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_234: 返工与强制报废 - 返修计数被清零

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返修计数被清零主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返修计数被清零建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_235: 返工与强制报废 - 返修样本抽检缺失

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返修样本抽检缺失主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返修样本抽检缺失建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_236: 返工与强制报废 - 返修工艺参数错误

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返修工艺参数错误主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返修工艺参数错误建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_237: 返工与强制报废 - 报废原因未归类

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 报废原因未归类主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕报废原因未归类建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_238: 返工与强制报废 - 返工批次拆分失控

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返工批次拆分失控主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返工批次拆分失控建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_239: 返工与强制报废 - 返修完成未归档

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返修完成未归档主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返修完成未归档建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_240: 返工与强制报废 - 返工失败自动报废

- **本体模型映射**: `Rework, BillOfProcess, Spec, Container`
- **业务痛点 (Pain Point)**: 返工失败自动报废主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕返工失败自动报废建立数字化校验点，ReworkPath、BillOfProcess、Spec、Resource 与 Container 联动返工路线和报废规则，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *返修只能走授权路径，超限或失败件自动隔离，并留下可追溯的异常处置证据。*

<!-- slide -->


---

## 13. 环境温湿度与公用工程 (Environmental Monitoring & Cleanroom Control)

### 📌 SC_241: 环境洁净室ESD防错 - 尘埃粒子超标

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 尘埃粒子超标主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕尘埃粒子超标建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_242: 环境洁净室ESD防错 - 温度超限

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 温度超限主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕温度超限建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_243: 环境洁净室ESD防错 - 湿度超限

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 湿度超限主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕湿度超限建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_244: 环境洁净室ESD防错 - ESD接地失败

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: ESD接地失败主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕ESD接地失败建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_245: 环境洁净室ESD防错 - 压差异常

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 压差异常主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕压差异常建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_246: 环境洁净室ESD防错 - 洁净区门禁未闭合

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 洁净区门禁未闭合主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕洁净区门禁未闭合建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_247: 环境洁净室ESD防错 - 烘房温度漂移

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 烘房温度漂移主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕烘房温度漂移建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_248: 环境洁净室ESD防错 - 露点异常

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 露点异常主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕露点异常建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_249: 环境洁净室ESD防错 - VOC浓度超限

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: VOC浓度超限主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕VOC浓度超限建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_250: 环境洁净室ESD防错 - 氮气纯度不足

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 氮气纯度不足主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕氮气纯度不足建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_251: 环境洁净室ESD防错 - 冷却水温异常

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 冷却水温异常主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕冷却水温异常建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_252: 环境洁净室ESD防错 - 光照强度异常

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 光照强度异常主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕光照强度异常建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_253: 环境洁净室ESD防错 - 静电腕带失效

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 静电腕带失效主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕静电腕带失效建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_254: 环境洁净室ESD防错 - 洁净服有效期过期

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 洁净服有效期过期主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕洁净服有效期过期建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_255: 环境洁净室ESD防错 - 高温窑炉外壁超温

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 高温窑炉外壁超温主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕高温窑炉外壁超温建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_256: 环境洁净室ESD防错 - 湿敏区湿度报警

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 湿敏区湿度报警主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕湿敏区湿度报警建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_257: 环境洁净室ESD防错 - 环境数据断链

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 环境数据断链主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕环境数据断链建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_258: 环境洁净室ESD防错 - 区域等级不匹配

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 区域等级不匹配主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕区域等级不匹配建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_259: 环境洁净室ESD防错 - 环境报警未复位

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 环境报警未复位主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕环境报警未复位建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_260: 环境洁净室ESD防错 - 批次暴露时间超限

- **本体模型映射**: `Environment, Container, Spec, Alarm`
- **业务痛点 (Pain Point)**: 批次暴露时间超限主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕批次暴露时间超限建立数字化校验点，Environment、AlarmDef、AlarmLog、BusinessRule、Resource 与 Container 形成环境联锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *环境越界立即阻断过站和设备动作，产品不暴露在失控条件下，并留下可追溯的异常处置证据。*

<!-- slide -->


---

## 14. 包装称重与成品标签 (Packaging, Weighing & Finished Goods Labeling)

### 📌 SC_261: 包装条码称重防漏 - 标签模板错用

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 标签模板错用主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕标签模板错用建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_262: 包装条码称重防漏 - 条码重复打印

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 条码重复打印主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕条码重复打印建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_263: 包装条码称重防漏 - 箱内漏配件

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 箱内漏配件主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕箱内漏配件建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_264: 包装条码称重防漏 - 称重偏轻

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 称重偏轻主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕称重偏轻建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_265: 包装条码称重防漏 - 称重偏重

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 称重偏重主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕称重偏重建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_266: 包装条码称重防漏 - 客户标签错贴

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 客户标签错贴主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕客户标签错贴建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_267: 包装条码称重防漏 - 混箱发货

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 混箱发货主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕混箱发货建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_268: 包装条码称重防漏 - 打印缓存串单

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 打印缓存串单主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕打印缓存串单建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_269: 包装条码称重防漏 - 包装规格错选

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 包装规格错选主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕包装规格错选建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_270: 包装条码称重防漏 - 序列号漏扫

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 序列号漏扫主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕序列号漏扫建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_271: 包装条码称重防漏 - 尾箱数量不符

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 尾箱数量不符主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕尾箱数量不符建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_272: 包装条码称重防漏 - 防伪码未激活

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 防伪码未激活主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕防伪码未激活建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_273: 包装条码称重防漏 - 外箱内箱不一致

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 外箱内箱不一致主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕外箱内箱不一致建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_274: 包装条码称重防漏 - 称重设备离线

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 称重设备离线主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕称重设备离线建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_275: 包装条码称重防漏 - 标签打印后未校验

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 标签打印后未校验主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕标签打印后未校验建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_276: 包装条码称重防漏 - 包装返工未重打

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 包装返工未重打主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕包装返工未重打建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_277: 包装条码称重防漏 - 箱规版本过期

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 箱规版本过期主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕箱规版本过期建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_278: 包装条码称重防漏 - 标签语言错配

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 标签语言错配主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕标签语言错配建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_279: 包装条码称重防漏 - 装箱清单缺项

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 装箱清单缺项主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕装箱清单缺项建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_280: 包装条码称重防漏 - 出货前反向对账失败

- **本体模型映射**: `Label, Container, DataCollection, BusinessRule`
- **业务痛点 (Pain Point)**: 出货前反向对账失败主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕出货前反向对账失败建立数字化校验点，Label、DataCollectionDef、DataCollectionHistory、BusinessRule 与 Container 绑定包装、称重和条码核验，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *包装数据与实物一致后才可出货，漏装混贴被前置拦截，并留下可追溯的异常处置证据。*

<!-- slide -->


---

## 15. 出货发运与退货 RMA (Shipping Log & Return Material Authorization)

### 📌 SC_281: 出库道闸与RMA隔离 - Hold批次误出厂

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: Hold批次误出厂主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕Hold批次误出厂建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_282: 出库道闸与RMA隔离 - RMA件误投良品线

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: RMA件误投良品线主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕RMA件误投良品线建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_283: 出库道闸与RMA隔离 - 退货隔离区绕行

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 退货隔离区绕行主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕退货隔离区绕行建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_284: 出库道闸与RMA隔离 - 发货客户不匹配

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 发货客户不匹配主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕发货客户不匹配建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_285: 出库道闸与RMA隔离 - 叉车越界出库

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 叉车越界出库主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕叉车越界出库建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_286: 出库道闸与RMA隔离 - 出货状态未确认

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 出货状态未确认主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕出货状态未确认建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_287: 出库道闸与RMA隔离 - RMA检测路线缺失

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: RMA检测路线缺失主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕RMA检测路线缺失建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_288: 出库道闸与RMA隔离 - 退货件二次流出

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 退货件二次流出主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕退货件二次流出建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_289: 出库道闸与RMA隔离 - SalesOrder关闭仍发货

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: SalesOrder关闭仍发货主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕SalesOrder关闭仍发货建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_290: 出库道闸与RMA隔离 - 道闸扫码失败

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 道闸扫码失败主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕道闸扫码失败建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_291: 出库道闸与RMA隔离 - 异常批次装车

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 异常批次装车主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕异常批次装车建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_292: 出库道闸与RMA隔离 - 退货复判未完成

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 退货复判未完成主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕退货复判未完成建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_293: 出库道闸与RMA隔离 - 出库目的地错误

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 出库目的地错误主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕出库目的地错误建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_294: 出库道闸与RMA隔离 - 拦截后人工放行

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 拦截后人工放行主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕拦截后人工放行建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_295: 出库道闸与RMA隔离 - RMA返修路径错选

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: RMA返修路径错选主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕RMA返修路径错选建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_296: 出库道闸与RMA隔离 - 客户召回批次拦截

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 客户召回批次拦截主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕客户召回批次拦截建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_297: 出库道闸与RMA隔离 - 出货前Hold未解除

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 出货前Hold未解除主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕出货前Hold未解除建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_298: 出库道闸与RMA隔离 - 退货件标签混乱

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 退货件标签混乱主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕退货件标签混乱建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_299: 出库道闸与RMA隔离 - 成品库隔离失效

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 成品库隔离失效主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕成品库隔离失效建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_300: 出库道闸与RMA隔离 - 道闸报警未闭环

- **本体模型映射**: `Rma, SalesOrder, ShipRequest, Container`
- **业务痛点 (Pain Point)**: 道闸报警未闭环主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕道闸报警未闭环建立数字化校验点，SalesOrder、ReturnedEquipmentAction、Resource、Spec 与 Container 联动出库拦截和退货隔离，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *隐患批次出不了厂，RMA件不会重新混入良品流，并留下可追溯的异常处置证据。*

<!-- slide -->


---

## 2. 在制品容器与追溯 (WIP Container Tracking & Genealogy)

### 📌 SC_021: 批次Container生命周期状态机全电监控

- **本体模型映射**: `Container, Carrier, Spec, Quality, BusinessRule`
- **业务痛点 (Pain Point)**: 纸质批次流转卡极易丢失或字迹模糊，现场搞不清当前批次的真实物理状态与过站记录。
- **数字化映射方案 (Digital Solution)**: 定义Container本体。挂载Status（Queue/Active/Hold/Scrapped）状态机。过站事件全电驱动状态变换。
- **客户易懂价值 (Value to Client)**: *流转卡彻底数字化，制品状态实时透明，随时随地一键追溯，数据准确度达100%。*

<!-- slide -->

### 📌 SC_022: 批次拆分(Split)子母血统自动关联

- **本体模型映射**: `Container, Spec, Resource, Employee`
- **业务痛点 (Pain Point)**: 在制品需要拆分抽样或返工时，手工登记子批次导致其血统关系与母批次断档失联。
- **数字化映射方案 (Digital Solution)**: 当Container执行Split时，系统生成新子Container。底层建立Parent-Child关系链，自动继承母批次的所有谱系树。
- **客户易懂价值 (Value to Client)**: *子母血统谱系无缝连接，发生异常一键锁定子母批次，避免盲目大范围扩大封锁。*

<!-- slide -->

### 📌 SC_023: 批次合并(Merge)多源谱系精密核销

- **本体模型映射**: `Container, Carrier, Spec, Quality, BusinessRule`
- **业务痛点 (Pain Point)**: 多批次合并加工时，手工台账无法理清多源头谱系，发生异常无法定位涉及的原材料批次。
- **数字化映射方案 (Digital Solution)**: 当多个Container执行Merge时，MES底层记录多源Parent关系。生成统一的谱系图谱，BOM扣减分摊合并核销。
- **客户易懂价值 (Value to Client)**: *多源头谱系对账清清楚楚，原材料缺陷定位精度从‘某几天’精确到‘具体哪几箱’。*

<!-- slide -->

### 📌 SC_024: Container超期未过站(Transit Time)自动锁死

- **本体模型映射**: `Container, Spec, Resource, Employee`
- **业务痛点 (Pain Point)**: 敏感工序间（如曝光至显影之间）停留超时会导致产品报废，人工计算时间经常超时漏防。
- **数字化映射方案 (Digital Solution)**: Container出站触发Timer。若在规定transit time内未进入下一步Spec Move In，系统自动触发Auto-Hold与Alarm。
- **客户易懂价值 (Value to Client)**: *给高危工序间拉起数字化隐形防线，只要超限系统自动锁死拦截，超时报废率归零。*

<!-- slide -->

### 📌 SC_025: 在制品进站(Move In)设备防错核验

- **本体模型映射**: `Container, Carrier, Spec, Quality, BusinessRule`
- **业务痛点 (Pain Point)**: 操作员经常把A产品的批次投进B产品的机台加工，打刀损模，产品成批报废。
- **数字化映射方案 (Digital Solution)**: Move In时系统强制校验：Container.ProductId 是否与 Resource.CurrentProduct 一致，不匹配系统锁死进料门。
- **客户易懂价值 (Value to Client)**: *彻底终结投错机台的低级错误，保障昂贵的精密模具与刀具的现场硬件安全。*

<!-- slide -->

### 📌 SC_026: 在制品出站(Move Out)参数漏登拦截

- **本体模型映射**: `Container, Spec, Resource, Employee`
- **业务痛点 (Pain Point)**: 工艺要求出站必须测量厚度并记录，操作员为了图省事直接漏填漏登，导致工艺数据断档。
- **数字化映射方案 (Digital Solution)**: Move Out时系统强制检索DataCollection模板。若核心工艺参数字段为空，出站Move Out按钮保持灰色并警示漏登。
- **客户易懂价值 (Value to Client)**: *工艺参数100%强制完整录入，根除因作业员偷懒漏登导致的追溯合规漏洞。*

<!-- slide -->

### 📌 SC_027: 容器与物理托盘/载具(Carrier)双重绑定

- **本体模型映射**: `Container, Carrier, Spec, Quality, BusinessRule`
- **业务痛点 (Pain Point)**: 产品装进载具后，载具条码与产品批次脱节，设备扫载具条码时由于系统错配下发错工艺。
- **数字化映射方案 (Digital Solution)**: Container与Carrier建立一对多强关联。机台OPC直接扫描Carrier条码，MES动态寻址并核对绑定容器的工艺规范。
- **客户易懂价值 (Value to Client)**: *载具和制品自动对齐，设备智能识别载具注入正确配方，防呆自动化水平极大提升。*

<!-- slide -->

### 📌 SC_028: 车间在制品先入先出(FIFO)物理流线控制

- **本体模型映射**: `Container, Spec, Resource, Employee`
- **业务痛点 (Pain Point)**: 操作员凭经验在制品货架上随手拿料，导致滞后批次长期堆积超时损坏。
- **数字化映射方案 (Digital Solution)**: 在货架区定义FIFO规则。机台Move In扫描Container时，系统查验同队列是否有更早的Container，若有则拒绝过站。
- **客户易懂价值 (Value to Client)**: *彻底消灭在制品在货架上的‘死批次’积压超时风险，物流流动科学畅通。*

<!-- slide -->

### 📌 SC_029: 批次自动挂起(Hold)与解锁审计

- **本体模型映射**: `Container, Carrier, Spec, Quality, BusinessRule`
- **业务痛点 (Pain Point)**: 发现质量隐患需要挂起批次，但微信口头通知现场不理会，被挂起的批次依然被作业员开机加工。
- **数字化映射方案 (Digital Solution)**: 质量员在图谱一键Hold Container。HoldStatus置为1。现场Resource Move In只要识别到HoldStatus=1，瞬间切断进料。
- **客户易懂价值 (Value to Client)**: *Hold一键锁死，微信口头通知变系统硬控制，隐患批次现场1秒内被死死卡住。*

<!-- slide -->

### 📌 SC_030: 返工批次(Rework Container)特异工艺防呆

- **本体模型映射**: `Container, Spec, Resource, Employee`
- **业务痛点 (Pain Point)**: 返工产品工艺特殊，作业员极易将其误入普通量产线，导致产品越修越坏发生严重报废。
- **数字化映射方案 (Digital Solution)**: 返工Container自动指派ReworkPath。工艺路线Spec前置防错只允许其进入返工机台，在量产线扫描时系统大声报错。
- **客户易懂价值 (Value to Client)**: *返工流程刚性约束，走错路系统自动不准进站，返工质量得到最严密的规范。*

<!-- slide -->

### 📌 SC_031: 实验批次(Split Lot)多级属性隔离

- **本体模型映射**: `Container, Carrier, Spec, Quality, BusinessRule`
- **业务痛点 (Pain Point)**: 研发实验料没有特殊标签，在制品经常在车间内被操作员当成普通量产料混装发走。
- **数字化映射方案 (Digital Solution)**: 实验料Container.Product定义特殊研发属性。过站时系统强校验，强制将其路由到专属实验工步，与量产料隔离。
- **客户易懂价值 (Value to Client)**: *实验料与量产料在系统级彻底隔离，绝无混装发错货可能，保障高毛利客户交付质量。*

<!-- slide -->

### 📌 SC_032: 晶圆(Wafer)级芯片芯片双向高精度追溯

- **本体模型映射**: `Container, Spec, Resource, Employee`
- **业务痛点 (Pain Point)**: 高精尖芯片制造中，无法将具体测试不良关联到硅片晶圆的具体物理位置，无法做机理分析。
- **数字化映射方案 (Digital Solution)**: 建立Wafer-level（晶圆级）谱系图。将测试DataCollection的X/Y坐标与Container内WaferID及Product实体深度映射绑定。
- **客户易懂价值 (Value to Client)**: *测试不良一键精细定位到晶圆物理型格，良率原因机理挖掘分析速度提升数倍。*

<!-- slide -->

### 📌 SC_033: 非激活容器(Inactive Container)防重刷拦截

- **本体模型映射**: `Container, Carrier, Spec, Quality, BusinessRule`
- **业务痛点 (Pain Point)**: 已过站完工的容器条码被作业员二次扫描尝试重复投料套账，造成现场数据和库存极大混乱。
- **数字化映射方案 (Digital Solution)**: 完工Container.Status置为Inactive。若此CdoId再次尝试Move In过站，系统逻辑直接红字欺诈预警并报警锁定。
- **客户易懂价值 (Value to Client)**: *堵死条码重复套用和库存假对账黑洞，守护工厂实物账的绝对真实与严肃性。*

<!-- slide -->

### 📌 SC_034: 异常缺陷在制品批量天网一键隔离

- **本体模型映射**: `Container, Spec, Resource, Employee`
- **业务痛点 (Pain Point)**: 发现原材料有裂纹，需要拦截已经使用了该原材料 of 在线所有批次，人工找卡起码花半天，漏拦率高。
- **数字化映射方案 (Digital Solution)**: 开发一键Quarantine天网。在图谱中输入缺陷批号，系统回溯关系树，秒级将受波及的Container状态批量设为Hold。
- **客户易懂价值 (Value to Client)**: *质量风暴来袭秒级全自动批量天网拦截，质量控制水平达到世界级大厂水准。*

<!-- slide -->

### 📌 SC_035: 在制品位置(Location)高精度图谱同步

- **本体模型映射**: `Container, Carrier, Spec, Quality, BusinessRule`
- **业务痛点 (Pain Point)**: 中控看板无法实时呈现每个在制品具体在哪个库位或货架上，找料耗费大量工时。
- **数字化映射方案 (Digital Solution)**: 将货架 Resource 细化 Location 库位。Container 每次移入时扫码绑定库位，中控 3D 孪生看板通过 WebSocket 实时同步。
- **客户易懂价值 (Value to Client)**: *货架库位了如指岗，找料时间从30分钟缩减到5秒，中控室全景看板尽收眼底。*

<!-- slide -->

### 📌 SC_036: 在制品寿命(Expiration)超期自动报废

- **本体模型映射**: `Container, Spec, Resource, Employee`
- **业务痛点 (Pain Point)**: 特殊制品开封回温后有寿命期限，手工卡片记时间经常过期未理会继续加工，出厂大面积脱胶。
- **数字化映射方案 (Digital Solution)**: 敏感制品绑定Timer。开封回温时Timer启动，Container在Spec Move In时若Timer到期，系统红字阻断并强制Scrap报废。
- **客户易懂价值 (Value to Client)**: *敏感化学品过期拦截精准率达100%，胶水失效脱胶等出厂质量爆雷风险彻底绝迹。*

<!-- slide -->

### 📌 SC_037: 跨车间(WorkCenter)大跨度过站校验

- **本体模型映射**: `Container, Carrier, Spec, Quality, BusinessRule`
- **业务痛点 (Pain Point)**: 制品跨车间转产时，由于流程没有核验，经常发生未经过前一车间放行便直接投入后一车间生产。
- **数字化映射方案 (Digital Solution)**: 跨车间Spec定义Sequence校验。容器Move In时追溯其WorkCenter轨迹，若发现前置车间未放行，系统拒绝过站。
- **客户易懂价值 (Value to Client)**: *车间转产轨迹滴水不漏，杜绝任何漏检工序直接溜进后道组装的违规可能。*

<!-- slide -->

### 📌 SC_038: 容器与销售订单(SO)发货防混绑定

- **本体模型映射**: `Container, Spec, Resource, Employee`
- **业务痛点 (Pain Point)**: 给客户发货时，因条码极其相似，员工误将1.0版本产品装进2.0版本的箱子发走，遭客户巨额罚款。
- **数字化映射方案 (Digital Solution)**: 成品包装段，Container.Id与SalesOrder.ProductId进行强比对。若包装条码与SO型号有半点偏差，系统锁死贴标机。
- **客户易懂价值 (Value to Client)**: *出货防混装门神死死看门，混装客诉与客户罚款彻底清零，品牌美誉度飙升。*

<!-- slide -->

### 📌 SC_039: 外协在制品出厂与逆向回厂防呆

- **本体模型映射**: `Container, Carrier, Spec, Quality, BusinessRule`
- **业务痛点 (Pain Point)**: 外协在制品发出去后变成‘黑盒’，加工完回来现场扫码经常报错，血统断档。
- **数字化映射方案 (Digital Solution)**: 外协Container出厂触发外协ShipRequest。外协厂加工完归还扫码时，逆向接口自动读取外协单号恢复其Container状态。
- **客户易懂价值 (Value to Client)**: *外协逆向归还谱系不断档，彻底告别外协回来手工记账数据乱套的噩梦。*

<!-- slide -->

### 📌 SC_040: 制品返修次数超频系统自动拉闸

- **本体模型映射**: `Container, Spec, Resource, Employee`
- **业务痛点 (Pain Point)**: 同一制品超限返工（比如返工了4次），材料晶粒疲劳受损，人工计数记错导致带病出厂爆雷。
- **数字化映射方案 (Digital Solution)**: Container本体挂载ReworkCount计数器。进入返工Spec时计数加1，一旦达2次上限，系统强制自动将其判定为Scrap。
- **客户易懂价值 (Value to Client)**: *超频返修残次品在工厂内部即被系统直接拦截销毁，严防金相疲劳件出厂爆雷。*

<!-- slide -->


---

## 3. 工艺路线与规范控制 (Process Routing & Spec Integrity)

### 📌 SC_041: 首件放行前强制质检工步校验

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 首件未完成检验即进入后续加工，导致整批制品在错误工艺状态下继续流转。
- **数字化映射方案 (Digital Solution)**: 通过 Spec 与 BillOfProcess 定义首件检验前置关卡，Container 过站时由 BusinessRule 校验首件放行状态。
- **客户易懂价值 (Value to Client)**: *首件未放行的批次无法进入量产段，批量性工艺失误被拦截在第一站。*

<!-- slide -->

### 📌 SC_042: 返修回流主线节点防错

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 返修件回流时绕过复检节点，混入正常主线后造成重复加工和质量责任不清。
- **数字化映射方案 (Digital Solution)**: 在返修回流节点按 BillOfProcess 序列校验目标 Spec，仅允许 Container 从授权节点回到主线。
- **客户易懂价值 (Value to Client)**: *返修回流路径清晰可审计，异常返修件不会误入普通生产节拍。*

<!-- slide -->

### 📌 SC_043: 工艺版本生效窗口拦截

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 工艺版本切换期间旧版 Spec 与新版路线混用，现场靠人工通知容易滞后。
- **数字化映射方案 (Digital Solution)**: 将 Spec 版本和 BillOfProcess 生效窗口绑定，过站时用 BusinessRule 判定当前时间与版本状态。
- **客户易懂价值 (Value to Client)**: *版本切换从口头管控变成系统硬约束，减少错版加工和返工成本。*

<!-- slide -->

### 📌 SC_044: 并行分支工序互斥控制

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 同一 Container 在并行分支中被重复派工，清洗与涂覆等互斥工序顺序混乱。
- **数字化映射方案 (Digital Solution)**: 利用 BillOfProcess 的分支路径约束校验 Container 已执行轨迹，禁止进入互斥 Spec。
- **客户易懂价值 (Value to Client)**: *并行工序不再互相踩踏，分支路线执行结果可追踪可复核。*

<!-- slide -->

### 📌 SC_045: 热处理保温时长达标校验

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 热处理保温时间不足就提前出炉，后续机械性能检验才暴露问题。
- **数字化映射方案 (Digital Solution)**: 把热处理 Spec 的最短停留要求纳入路线控制，Container 出站前由 BusinessRule 校验工步时长。
- **客户易懂价值 (Value to Client)**: *关键热处理条件在过站时即时拦截，避免低强度批次继续流转。*

<!-- slide -->

### 📌 SC_046: 涂覆前清洗闭环确认

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 清洗工步未完成或记录缺失时直接进入涂覆，造成附着力异常和批量返修。
- **数字化映射方案 (Digital Solution)**: BillOfProcess 要求涂覆 Spec 前必须存在清洗完成轨迹，BusinessRule 在进站时核对。
- **客户易懂价值 (Value to Client)**: *涂覆前置条件闭环确认，表面处理缺失不会被带入后段。*

<!-- slide -->

### 📌 SC_047: 多站点同名工序版本错用防呆

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 多条产线存在同名 Spec，操作员选择错误站点版本导致工艺参数不匹配。
- **数字化映射方案 (Digital Solution)**: 将 Resource、Spec 与 BillOfProcess 绑定到当前路线，Container 进站时校验站点与版本组合。
- **客户易懂价值 (Value to Client)**: *同名工序不再混用，跨线作业也能保持工艺版本一致。*

<!-- slide -->

### 📌 SC_048: 客户特规路线锁定

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 客户特规订单误走通用路线，关键附加检验或特殊处理被跳过。
- **数字化映射方案 (Digital Solution)**: 按 Container 业务属性锁定特定 BillOfProcess 和 Spec 序列，BusinessRule 禁止切换到通用路径。
- **客户易懂价值 (Value to Client)**: *客户特规要求被固化为路线约束，减少客诉与特采风险。*

<!-- slide -->

### 📌 SC_049: 工艺变更后在制品路径重算

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 工程变更发布后，已在制批次未按新要求补充工步，形成在制品断层。
- **数字化映射方案 (Digital Solution)**: 变更后按 Container 当前 Spec 与目标 BillOfProcess 重新计算后续路径，并在过站时校验。
- **客户易懂价值 (Value to Client)**: *在制品能平滑承接工艺变更，避免新旧路线之间的灰区。*

<!-- slide -->

### 📌 SC_050: 临时跳站审批留痕控制

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 临时跳站靠线长口头批准，事后无法确认跳过原因与责任人。
- **数字化映射方案 (Digital Solution)**: BusinessRule 只允许带审批标记的 Container 跳过指定 Spec，并记录跳站路径。
- **客户易懂价值 (Value to Client)**: *例外处理有据可查，跳站不再成为质量追溯盲点。*

<!-- slide -->

### 📌 SC_051: 末道测试前装配序列核销

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 末道测试发现前序装配缺项，返查时无法定位漏装发生在哪个工步。
- **数字化映射方案 (Digital Solution)**: 在末道测试 Spec 前核销 BillOfProcess 要求的所有装配工步完成轨迹。
- **客户易懂价值 (Value to Client)**: *末道测试入口变成装配完整性闸口，漏工序产品无法进入终检。*

<!-- slide -->

### 📌 SC_052: 子流程回归主流程节点校验

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 子流程完成后回到错误主流程节点，导致后续工艺重复或缺失。
- **数字化映射方案 (Digital Solution)**: 校验 Container 从子流程返回时的目标 Spec 是否匹配 BillOfProcess 定义的回归节点。
- **客户易懂价值 (Value to Client)**: *子流程和主流程衔接稳定，复杂路线也能按节点回归。*

<!-- slide -->

### 📌 SC_053: 外协回厂补检强制执行

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 外协加工回厂后直接入线，缺少补检确认导致外协缺陷流入后段。
- **数字化映射方案 (Digital Solution)**: 将外协回厂状态映射到必须补检的 Spec，BusinessRule 拦截未补检 Container。
- **客户易懂价值 (Value to Client)**: *外协质量风险在回厂入口被吸收，后续生产不再替外协缺陷买单。*

<!-- slide -->

### 📌 SC_054: 重复过站计数污染防止

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 条码重复扫描造成同一 Spec 多次过站，产量与质量记录被污染。
- **数字化映射方案 (Digital Solution)**: BusinessRule 检查 Container 在当前 BillOfProcess 节点的过站历史，阻止非授权重复过站。
- **客户易懂价值 (Value to Client)**: *产量、节拍和质量记录更干净，减少重复扫描带来的数据噪声。*

<!-- slide -->

### 📌 SC_055: 设备能力与工艺匹配校验

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 临时换设备时没有确认 Resource 能力，普通设备执行了高精度 Spec。
- **数字化映射方案 (Digital Solution)**: 将 Spec 的资源能力要求与 Resource 绑定，Container 进站时同时校验路线和设备能力。
- **客户易懂价值 (Value to Client)**: *设备替换不会突破工艺能力边界，高精度工序得到保护。*

<!-- slide -->

### 📌 SC_056: 冻结工艺禁止投产

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 被冻结的 Spec 或路线仍被现场引用，导致已停用工艺继续生产。
- **数字化映射方案 (Digital Solution)**: 过站前校验 Spec 与 BillOfProcess 冻结状态，冻结对象触发 BusinessRule 拦截。
- **客户易懂价值 (Value to Client)**: *停用工艺真正停用，工程冻结不再停留在文档层。*

<!-- slide -->

### 📌 SC_057: 试制路线与量产路线隔离

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 试制批次路线被量产批次误用，试验参数进入正常生产。
- **数字化映射方案 (Digital Solution)**: 用 Container 类型区分试制与量产，限制其可进入的 BillOfProcess 和 Spec。
- **客户易懂价值 (Value to Client)**: *试制探索与量产执行隔离，防止实验参数污染稳定生产。*

<!-- slide -->

### 📌 SC_058: 危化工步前置确认

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 危化处理前缺少安全确认和前序状态检查，存在人员与设备风险。
- **数字化映射方案 (Digital Solution)**: 在危化 Spec 前设置前置状态核验，BusinessRule 拦截未满足条件的 Container。
- **客户易懂价值 (Value to Client)**: *高风险工步前置条件被系统化，安全与质量同时受控。*

<!-- slide -->

### 📌 SC_059: 批量拆分后路径一致性校验

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 批量 Split 后子批次路径不一致，部分子批走错路线或漏做工序。
- **数字化映射方案 (Digital Solution)**: 以 BillOfProcess 为基准校验拆分后每个 Container 的目标 Spec 与父批一致性。
- **客户易懂价值 (Value to Client)**: *拆分批次仍保持路线一致，批量追溯不会断裂。*

<!-- slide -->

### 📌 SC_060: 工艺路线退版防错

- **本体模型映射**: `Spec, BillOfProcess, Container, BusinessRule`
- **业务痛点 (Pain Point)**: 路线退版后现场仍扫描旧版本入口，导致已废止参数重新启用。
- **数字化映射方案 (Digital Solution)**: BusinessRule 校验 Container 当前路线版本，只允许进入当前有效 BillOfProcess。
- **客户易懂价值 (Value to Client)**: *退版风险被入口拦截，历史路线不会误回生产现场。*

<!-- slide -->


---

## 4. 物料控制与高级 BOM (Material Control & Advanced BOM)

### 📌 SC_061: 替代料比例上限防呆

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 替代料使用比例没有系统限制，关键物料被过量替代影响成品性能。
- **数字化映射方案 (Digital Solution)**: BOM 与 Material 联动校验替代料上限，超过阈值时 BusinessRule 拦截 Container 投料。
- **客户易懂价值 (Value to Client)**: *替代策略从人工经验变成系统限额，避免替代料滥用。*

<!-- slide -->

### 📌 SC_062: 供应商批次黑名单拦截

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 供应商问题批次仍被扫描上线，质量通知无法及时传达到产线。
- **数字化映射方案 (Digital Solution)**: Vendor 与 Material 批次状态参与投料校验，黑名单批次触发 AlarmDef。
- **客户易懂价值 (Value to Client)**: *问题供应商批次无法进入生产，来料风险前移到投料口。*

<!-- slide -->

### 📌 SC_063: 关键物料有效期到期拦截

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 胶水、焊料等时效物料超过有效期仍被使用，后段才出现质量异常。
- **数字化映射方案 (Digital Solution)**: TimerDef 对 Material 有效期计时，投料时 BusinessRule 判断是否过期。
- **客户易懂价值 (Value to Client)**: *过期料在上线前被拦截，减少隐性批量缺陷。*

<!-- slide -->

### 📌 SC_064: BOM版本与工单版本一致性

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 工单引用的 BOM 版本与现场领料版本不一致，导致装配错料。
- **数字化映射方案 (Digital Solution)**: 扫描 Material 时同时校验 BOM 版本和 Container 生产上下文。
- **客户易懂价值 (Value to Client)**: *工单、BOM、物料三者一致，错版领料不再流入现场。*

<!-- slide -->

### 📌 SC_065: 高价值物料超领防控

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 贵重芯片或核心部件超领后去向不清，形成成本和合规风险。
- **数字化映射方案 (Digital Solution)**: Material 投入数量与 BOM 需求量联动核销，超领时由 BusinessRule 拦截。
- **客户易懂价值 (Value to Client)**: *高价值物料消耗可控，减少线边库存黑洞。*

<!-- slide -->

### 📌 SC_066: 批次混料扫描防错

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 相邻批次物料外观相似，人工上料容易混料。
- **数字化映射方案 (Digital Solution)**: 以 BOM 指定 Material 和 Vendor 批号为准，扫描不匹配即触发 AlarmDef。
- **客户易懂价值 (Value to Client)**: *混料在扫描瞬间被发现，减少后段拆解返工。*

<!-- slide -->

### 📌 SC_067: 禁用替代料即时阻断

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 工程临时禁用某替代料后，旧领料单仍允许继续投料。
- **数字化映射方案 (Digital Solution)**: Material 可用状态参与投料判定，禁用项不允许绑定 Container。
- **客户易懂价值 (Value to Client)**: *工程禁用即时生效，现场不再依赖人工传达。*

<!-- slide -->

### 📌 SC_068: 料站与工序绑定校验

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 物料被送到错误工序料站，导致前后段混用。
- **数字化映射方案 (Digital Solution)**: Spec、BOM 与 Material 建立料站约束，错误工序投料直接拦截。
- **客户易懂价值 (Value to Client)**: *料站配送与工艺需求一致，降低错站投料。*

<!-- slide -->

### 📌 SC_069: 供应商证书到期拦截

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 供应商资质过期但物料仍可上线，审计风险高。
- **数字化映射方案 (Digital Solution)**: Vendor 资质状态参与 Material 放行判断，到期供应商触发 BusinessRule。
- **客户易懂价值 (Value to Client)**: *供应商合规状态进入生产拦截逻辑，审计更稳。*

<!-- slide -->

### 📌 SC_070: 工程变更物料替换控制

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: ECO 物料替换时新旧料并存，现场误用旧料。
- **数字化映射方案 (Digital Solution)**: BOM 替换生效后校验 Material 是否属于当前有效清单。
- **客户易懂价值 (Value to Client)**: *物料切换受控，工程变更不会造成错料窗口。*

<!-- slide -->

### 📌 SC_071: 湿敏物料开封时长控制

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 湿敏件开封后暴露超时仍被贴装，可靠性风险高。
- **数字化映射方案 (Digital Solution)**: TimerDef 记录开封时长，Material 上线时判断暴露时间。
- **客户易懂价值 (Value to Client)**: *湿敏件使用窗口清晰，超时物料自动拦截。*

<!-- slide -->

### 📌 SC_072: 序列化物料一物一码绑定

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 序列化关键件未绑定 Container，后续追溯不到单件来源。
- **数字化映射方案 (Digital Solution)**: Material 扫描时要求序列号绑定 Container 和 BOM 行。
- **客户易懂价值 (Value to Client)**: *关键件单件谱系完整，售后追溯更精确。*

<!-- slide -->

### 📌 SC_073: 线边库存先进先出校验

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 先进先出规则靠人工挑料，老批次积压过期。
- **数字化映射方案 (Digital Solution)**: Material 批次按 FIFO 顺序校验，非优先批次投料触发提醒或拦截。
- **客户易懂价值 (Value to Client)**: *减少呆滞料和过期料，线边库存周转更健康。*

<!-- slide -->

### 📌 SC_074: 物料单位换算误差防控

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 辅单位换算错误造成投料数量偏差，人工复核难发现。
- **数字化映射方案 (Digital Solution)**: BOM 需求量与 Material 实发量按单位换算规则比对。
- **客户易懂价值 (Value to Client)**: *投料数量精度提升，减少因单位错误引起的偏耗。*

<!-- slide -->

### 📌 SC_075: 危险物料专用工位限制

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 危险化学品被带到非授权工位使用，安全风险高。
- **数字化映射方案 (Digital Solution)**: Material 危险属性与 Spec/Resource 绑定，非授权工位拒绝投料。
- **客户易懂价值 (Value to Client)**: *危险物料使用范围受控，安全合规更可靠。*

<!-- slide -->

### 📌 SC_076: 客户指定品牌物料防错

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 客户指定品牌要求未落实，替代品牌被误用。
- **数字化映射方案 (Digital Solution)**: BOM 中客户指定 Material 与 Vendor 条件被扫描校验。
- **客户易懂价值 (Value to Client)**: *客户指定料不被替代，避免认证和客诉风险。*

<!-- slide -->

### 📌 SC_077: 来料检验未放行拦截

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: IQC 未放行批次提前上线，缺陷料流入生产。
- **数字化映射方案 (Digital Solution)**: Material 批次放行状态与 Vendor 检验结果参与投料判断。
- **客户易懂价值 (Value to Client)**: *未检或不合格来料无法上线，质量门前移。*

<!-- slide -->

### 📌 SC_078: 套料齐套性上线校验

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 套料缺件仍开工，生产中途停线找料。
- **数字化映射方案 (Digital Solution)**: BOM 要求的 Material 齐套状态在 Container 开工前统一校验。
- **客户易懂价值 (Value to Client)**: *缺料不再进入生产节拍，减少中途停线。*

<!-- slide -->

### 📌 SC_079: 剩余尾料使用授权

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 尾料未授权使用导致批次追溯不完整。
- **数字化映射方案 (Digital Solution)**: Material 尾料状态需要 BusinessRule 授权后才能绑定 Container。
- **客户易懂价值 (Value to Client)**: *尾料使用可控可追溯，减少账实差异。*

<!-- slide -->

### 📌 SC_080: 物料冻结状态联动拦截

- **本体模型映射**: `BOM, Material, Container, Supplier`
- **业务痛点 (Pain Point)**: 质量冻结物料仍留在线边被误扫上线。
- **数字化映射方案 (Digital Solution)**: Material 冻结状态参与所有投料扫描，冻结即触发 AlarmDef。
- **客户易懂价值 (Value to Client)**: *冻结物料不会绕过系统进入生产，隔离措施落地。*

<!-- slide -->


---

## 5. 工厂结构与制造日历 (Factory Structure & Mfg Calendars)

### 📌 SC_081: 工厂建模与班组排班 - 停电检修日历冲突

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 停电检修日历冲突主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕停电检修日历冲突建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_082: 工厂建模与班组排班 - 跨车间资源借用

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 跨车间资源借用主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕跨车间资源借用建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_083: 工厂建模与班组排班 - 夜班人员不足

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 夜班人员不足主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕夜班人员不足建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_084: 工厂建模与班组排班 - 瓶颈工站积压

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 瓶颈工站积压主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕瓶颈工站积压建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_085: 工厂建模与班组排班 - 节假日加班排程

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 节假日加班排程主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕节假日加班排程建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_086: 工厂建模与班组排班 - 班组技能覆盖不足

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 班组技能覆盖不足主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕班组技能覆盖不足建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_087: 工厂建模与班组排班 - 产线换班交接断点

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 产线换班交接断点主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕产线换班交接断点建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_088: 工厂建模与班组排班 - 临时停线窗口

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 临时停线窗口主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕临时停线窗口建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_089: 工厂建模与班组排班 - 多工厂订单转移

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 多工厂订单转移主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕多工厂订单转移建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_090: 工厂建模与班组排班 - 共享设备预约冲突

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 共享设备预约冲突主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕共享设备预约冲突建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_091: 工厂建模与班组排班 - 线体节拍失衡

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 线体节拍失衡主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕线体节拍失衡建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_092: 工厂建模与班组排班 - 维修窗口插入

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 维修窗口插入主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕维修窗口插入建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_093: 工厂建模与班组排班 - 班组工时虚报

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 班组工时虚报主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕班组工时虚报建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_094: 工厂建模与班组排班 - 外协工序回厂排程

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 外协工序回厂排程主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕外协工序回厂排程建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_095: 工厂建模与班组排班 - 洁净区班组准入

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 洁净区班组准入主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕洁净区班组准入建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_096: 工厂建模与班组排班 - 长周期工序跨班

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 长周期工序跨班主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕长周期工序跨班建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_097: 工厂建模与班组排班 - 工站负荷预警

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 工站负荷预警主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕工站负荷预警建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_098: 工厂建模与班组排班 - 紧急插单排班

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 紧急插单排班主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕紧急插单排班建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_099: 工厂建模与班组排班 - 试制线与量产线隔离

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 试制线与量产线隔离主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕试制线与量产线隔离建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_100: 工厂建模与班组排班 - 周末无人值守拦截

- **本体模型映射**: `Factory, WorkCenter, MfgCalendar, Team`
- **业务痛点 (Pain Point)**: 周末无人值守拦截主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕周末无人值守拦截建立数字化校验点，Factory、WorkCenter、MfgCalendar、Team、Resource 与 Container 联动校验排程可行性，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *计划、日历、班组和工站状态一致后才允许投产，并留下可追溯的异常处置证据。*

<!-- slide -->


---

## 6. 现场数据采集与配方 (Data Collection & Recipe Management)

### 📌 SC_101: PLC配方下发与数据采集 - 温度配方下发

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 温度配方下发主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕温度配方下发建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_102: PLC配方下发与数据采集 - 压力参数采集

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 压力参数采集主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕压力参数采集建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_103: PLC配方下发与数据采集 - 扭矩曲线回填

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 扭矩曲线回填主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕扭矩曲线回填建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_104: PLC配方下发与数据采集 - 涂胶流量监控

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 涂胶流量监控主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕涂胶流量监控建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_105: PLC配方下发与数据采集 - 烘烤时间采集

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 烘烤时间采集主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕烘烤时间采集建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_106: PLC配方下发与数据采集 - 真空度参数校验

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 真空度参数校验主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕真空度参数校验建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_107: PLC配方下发与数据采集 - 点胶坐标下发

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 点胶坐标下发主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕点胶坐标下发建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_108: PLC配方下发与数据采集 - 激光功率采集

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 激光功率采集主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕激光功率采集建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_109: PLC配方下发与数据采集 - 清洗浓度回填

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 清洗浓度回填主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕清洗浓度回填建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_110: PLC配方下发与数据采集 - 贴装压力下发

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 贴装压力下发主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕贴装压力下发建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_111: PLC配方下发与数据采集 - 固化能量采集

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 固化能量采集主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕固化能量采集建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_112: PLC配方下发与数据采集 - 测试电压参数

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 测试电压参数主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕测试电压参数建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_113: PLC配方下发与数据采集 - 视觉阈值下发

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 视觉阈值下发主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕视觉阈值下发建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_114: PLC配方下发与数据采集 - 称重数据回填

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 称重数据回填主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕称重数据回填建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_115: PLC配方下发与数据采集 - 湿度补偿参数

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 湿度补偿参数主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕湿度补偿参数建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_116: PLC配方下发与数据采集 - 冷却曲线采集

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 冷却曲线采集主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕冷却曲线采集建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_117: PLC配方下发与数据采集 - 速度配方下发

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 速度配方下发主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕速度配方下发建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_118: PLC配方下发与数据采集 - 电流波形采集

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 电流波形采集主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕电流波形采集建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_119: PLC配方下发与数据采集 - 批次参数继承

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 批次参数继承主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕批次参数继承建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_120: PLC配方下发与数据采集 - 异常参数重采

- **本体模型映射**: `Recipe, DataCollection, Resource, Spec`
- **业务痛点 (Pain Point)**: 异常参数重采主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕异常参数重采建立数字化校验点，Recipe、DataCollectionDef、DataCollectionHistory、Resource、Spec 与 Container 串联配方下发和采集回写，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *配方和实测数据形成闭环，人工录入误差被消除，并留下可追溯的异常处置证据。*

<!-- slide -->


---

## 7. 设备状态与 OEE 监控 (Equipment States & OEE Telemetry)

### 📌 SC_121: 设备OEE状态互锁 - PM保养到期

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: PM保养到期主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕PM保养到期建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_122: 设备OEE状态互锁 - 首件检验未通过

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 首件检验未通过主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕首件检验未通过建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_123: 设备OEE状态互锁 - 设备报警未复位

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 设备报警未复位主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕设备报警未复位建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_124: 设备OEE状态互锁 - 刀具寿命超限

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 刀具寿命超限主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕刀具寿命超限建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_125: 设备OEE状态互锁 - 安全门未闭合

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 安全门未闭合主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕安全门未闭合建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_126: 设备OEE状态互锁 - 能耗异常升高

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 能耗异常升高主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕能耗异常升高建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_127: 设备OEE状态互锁 - 节拍持续偏慢

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 节拍持续偏慢主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕节拍持续偏慢建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_128: 设备OEE状态互锁 - 设备离线掉线

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 设备离线掉线主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕设备离线掉线建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_129: 设备OEE状态互锁 - 点检表未完成

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 点检表未完成主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕点检表未完成建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_130: 设备OEE状态互锁 - 维修工单未关闭

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 维修工单未关闭主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕维修工单未关闭建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_131: 设备OEE状态互锁 - 稼动率跌破阈值

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 稼动率跌破阈值主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕稼动率跌破阈值建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_132: 设备OEE状态互锁 - 空转时间过长

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 空转时间过长主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕空转时间过长建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_133: 设备OEE状态互锁 - 换型确认缺失

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 换型确认缺失主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕换型确认缺失建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_134: 设备OEE状态互锁 - 关键轴温超限

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 关键轴温超限主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕关键轴温超限建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_135: 设备OEE状态互锁 - 气压不足

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 气压不足主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕气压不足建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_136: 设备OEE状态互锁 - 治具未夹紧

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 治具未夹紧主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕治具未夹紧建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_137: 设备OEE状态互锁 - 传感器异常

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 传感器异常主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕传感器异常建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_138: 设备OEE状态互锁 - 产能负荷过载

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 产能负荷过载主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕产能负荷过载建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_139: 设备OEE状态互锁 - 停机原因未录入

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 停机原因未录入主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕停机原因未录入建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_140: 设备OEE状态互锁 - 复机审批缺失

- **本体模型映射**: `EquipmentState, Resource, Maintenance, Alarm`
- **业务痛点 (Pain Point)**: 复机审批缺失主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕复机审批缺失建立数字化校验点，ResourceStatusCode、MaintenanceReq、AlarmDef、AlarmLog 与 Container 联动设备状态互锁，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *设备状态不满足时无法继续过站，OEE损失可定位，并留下可追溯的异常处置证据。*

<!-- slide -->


---

## 8. 工装治具与夹具控制 (Tooling & Life Cycle Tracking)

### 📌 SC_141: 工装模具寿命锁定 - 网版印刷次数超限

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 网版印刷次数超限主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕网版印刷次数超限建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_142: 工装模具寿命锁定 - 切刀寿命到期

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 切刀寿命到期主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕切刀寿命到期建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_143: 工装模具寿命锁定 - 模具第四腔异常

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 模具第四腔异常主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕模具第四腔异常建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_144: 工装模具寿命锁定 - 夹具校准过期

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 夹具校准过期主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕夹具校准过期建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_145: 工装模具寿命锁定 - 治具错装

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 治具错装主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕治具错装建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_146: 工装模具寿命锁定 - 多腔体偏穴

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 多腔体偏穴主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕多腔体偏穴建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_147: 工装模具寿命锁定 - 冲头磨损超限

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 冲头磨损超限主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕冲头磨损超限建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_148: 工装模具寿命锁定 - 吸嘴寿命耗尽

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 吸嘴寿命耗尽主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕吸嘴寿命耗尽建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_149: 工装模具寿命锁定 - 载具清洗逾期

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 载具清洗逾期主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕载具清洗逾期建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_150: 工装模具寿命锁定 - 工装借用未归还

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 工装借用未归还主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕工装借用未归还建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_151: 工装模具寿命锁定 - 模具保养未完成

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 模具保养未完成主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕模具保养未完成建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_152: 工装模具寿命锁定 - 腔体良率偏低

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 腔体良率偏低主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕腔体良率偏低建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_153: 工装模具寿命锁定 - 治具温度异常

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 治具温度异常主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕治具温度异常建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_154: 工装模具寿命锁定 - 夹爪磨损报警

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 夹爪磨损报警主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕夹爪磨损报警建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_155: 工装模具寿命锁定 - 治具版本错配

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 治具版本错配主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕治具版本错配建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_156: 工装模具寿命锁定 - 模具换型漏确认

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 模具换型漏确认主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕模具换型漏确认建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_157: 工装模具寿命锁定 - 刀模裂纹记录

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 刀模裂纹记录主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕刀模裂纹记录建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_158: 工装模具寿命锁定 - 治具计数复位异常

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 治具计数复位异常主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕治具计数复位异常建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_159: 工装模具寿命锁定 - 备件替换未验证

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 备件替换未验证主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕备件替换未验证建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_160: 工装模具寿命锁定 - 工装冻结仍使用

- **本体模型映射**: `Tool, Spec, Quality, Resource`
- **业务痛点 (Pain Point)**: 工装冻结仍使用主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕工装冻结仍使用建立数字化校验点，Tool、ToolStatus、Spec、Resource、Event 与 Container 共同锁定工装状态和使用次数，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *超寿命或异常工装不再继续生产，腔体级风险被隔离，并留下可追溯的异常处置证据。*

<!-- slide -->


---

## 9. 人员资质与安全合规 (Personnel & E-Sign Audit)

### 📌 SC_161: 资质上岗与电子签名 - 资质过期上机

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 资质过期上机主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕资质过期上机建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_162: 资质上岗与电子签名 - 越权配方覆盖

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 越权配方覆盖主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕越权配方覆盖建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_163: 资质上岗与电子签名 - 代签审批

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 代签审批主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕代签审批建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_164: 资质上岗与电子签名 - 疲劳工时超限

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 疲劳工时超限主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕疲劳工时超限建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_165: 资质上岗与电子签名 - 临时授权未登记

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 临时授权未登记主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕临时授权未登记建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_166: 资质上岗与电子签名 - 双人复核缺失

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 双人复核缺失主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕双人复核缺失建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_167: 资质上岗与电子签名 - 高危工序刷卡失败

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 高危工序刷卡失败主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕高危工序刷卡失败建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_168: 资质上岗与电子签名 - 特批Override滥用

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 特批Override滥用主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕特批Override滥用建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_169: 资质上岗与电子签名 - 岗位角色不匹配

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 岗位角色不匹配主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕岗位角色不匹配建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_170: 资质上岗与电子签名 - 培训记录未完成

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 培训记录未完成主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕培训记录未完成建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_171: 资质上岗与电子签名 - 夜班主管缺席

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 夜班主管缺席主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕夜班主管缺席建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_172: 资质上岗与电子签名 - 外协人员无权限

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 外协人员无权限主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕外协人员无权限建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_173: 资质上岗与电子签名 - 维修模式误操作

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 维修模式误操作主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕维修模式误操作建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_174: 资质上岗与电子签名 - 参数修改无签名

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 参数修改无签名主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕参数修改无签名建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_175: 资质上岗与电子签名 - 批量放行缺审批

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 批量放行缺审批主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕批量放行缺审批建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_176: 资质上岗与电子签名 - 换线确认未签核

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 换线确认未签核主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕换线确认未签核建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_177: 资质上岗与电子签名 - 质量让步未留痕

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 质量让步未留痕主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕质量让步未留痕建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_178: 资质上岗与电子签名 - 复机授权缺失

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 复机授权缺失主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕复机授权缺失建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_179: 资质上岗与电子签名 - 关键报警屏蔽

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 关键报警屏蔽主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕关键报警屏蔽建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->

### 📌 SC_180: 资质上岗与电子签名 - 离岗账号未锁定

- **本体模型映射**: `Employee, Role, ESignature, BusinessRule`
- **业务痛点 (Pain Point)**: 离岗账号未锁定主要依赖人工发现和线下沟通，异常批次容易继续流转，现场缺少实时拦截与闭环记录。
- **数字化映射方案 (Digital Solution)**: 围绕离岗账号未锁定建立数字化校验点，Employee、RoleDef、SignatureRule、SignatureLog、BusinessRule 与 Container 形成身份和签名约束，在扫描、过站或放行时执行规则判断。
- **客户易懂价值 (Value to Client)**: *人、岗、权、签名全部留痕，越权操作无法悄悄发生，并留下可追溯的异常处置证据。*

<!-- slide -->


---

