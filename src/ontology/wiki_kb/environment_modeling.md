# 环境度量数据 (Environment) 建模说明

## 概述
`Environment` 是数字孪生和工业物联网场景中的关键本体对象。用以对接工厂 SCADA 遥测数据、PLC 环境数据（如洁净室温湿度、空气尘埃粒子数、工作台 ESD 接地状态等），并与物理工厂位置和设备关联以支持防错和联锁逻辑。

## 核心建模规范
- **层级**: Config (物理动态测量数据/系统集成实体)
- **业务主键**: 环境传感器区域编号 (EnvironmentName)

## 关联关系描述
- `Environment -[MONITORS_LOCATION]-> PhysicalLocation`: 监控数据归属的物理车间或库区区域。
- `Environment -[MONITORS_RESOURCE]-> Resource`: 传感器对应的物理设备。
