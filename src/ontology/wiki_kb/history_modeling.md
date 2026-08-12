# 主历史记录 (HistoryMainline) 建模说明

## 概述
`HistoryMainline` 是 Siemens Opcenter MES 中的核心交易审计日志对象。用于实时记录和追踪所有在制品容器（`Container`）在车间的物理流转、数据采集、设备过站、状态变动以及员工操作历史。

## 核心建模规范
- **CdoId**: 3980
- **层级**: Config (物理只读数据)
- **业务主键**: 历史交易序号/事务名 (HistoryMainlineName)

## 关联关系描述
- `HistoryMainline -[TRACES_CONTAINER]-> Container`: 该条审计日志所针对和影响的物理在制品容器。
- `HistoryMainline -[RECORDED_AT_SPEC]-> Spec`: 指示该交易在哪个具体的工艺工段/工序发生。
- `HistoryMainline -[ON_RESOURCE]-> Resource`: 该交易执行时所使用的物理机台设备。
- `HistoryMainline -[BY_EMPLOYEE]-> Employee`: 记录执行该交易的具体操作员工账号。
