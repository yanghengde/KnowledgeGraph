# SPC 图表可视化参数建模说明 / SPC Chart Visual Parameters Modeling

## 中文

`SPCChartVisualParams` 表示 SPC 图表的可视化参数名称、参数名与参数值。物理表通过 `ParentId` 指向 `SPCChartDef`，因此创建从可视化参数到 SPC 图表定义的导航关系。

需要注意：`SPCChartDef.SPCChartVisualParamsId` 在新版 CSV 中仍未标记为外键，因此 `SPCChartDef.spcChartVisualParams` 保持 Integer，不反向推断为 Navigation。

## English

`SPCChartVisualParams` stores the visual parameter name, key, and value for an SPC chart. Its physical `ParentId` foreign key points to `SPCChartDef`.

`SPCChartDef.SPCChartVisualParamsId` is not declared as a foreign key in the CSV, so the corresponding ontology property remains an Integer rather than an inferred Navigation.
