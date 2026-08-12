# 物理表与本体覆盖矩阵汇总

- 物理表总数：1555
- 已建本体：528
- SQL学习范围排除：69
- 其他未建顶级本体：958

| 规则分类 | 数量 |
|---|---:|
| child_or_association | 200 |
| excluded_from_sql_learning | 69 |
| internal_infrastructure | 24 |
| internal_or_unclassified | 131 |
| modeled | 528 |
| non_top_level_record | 126 |
| runtime_or_history | 477 |

完整逐表清单见 `docs/physical_ontology_coverage.csv`。分类为规则初筛，高置信顶级和支撑候选已完成审核并生成；SQL学习范围排除项仍完整保留在物理CSV中，但不进入业务关系图。
