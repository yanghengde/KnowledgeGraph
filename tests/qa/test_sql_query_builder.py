import unittest

from src.qa.sql_query_builder import MAX_QUERY_OBJECTS, build_query_builder_plan


class SqlQueryBuilderTests(unittest.TestCase):
    def test_selection_limit_is_sixteen(self):
        self.assertEqual(MAX_QUERY_OBJECTS, 16)

    def test_empty_plan(self):
        plan = build_query_builder_plan([])
        self.assertEqual(plan["nodes"], [])
        self.assertEqual(plan["sql"], "")

    def test_single_table_plan_uses_primary_key(self):
        plan = build_query_builder_plan(["Container"])
        self.assertEqual(plan["root_table"], "Container")
        self.assertIn("ContainerId", plan["sql"])
        self.assertIn("FROM Container c", plan["sql"])
        self.assertEqual(plan["unconnected"], [])

    def test_join_plan_only_renders_verified_physical_join(self):
        plan = build_query_builder_plan(["Container", "CurrentStatus"])
        self.assertTrue(plan["joins"])
        self.assertIn("JOIN CurrentStatus", plan["sql"])
        self.assertIn("CurrentStatusId", plan["sql"])
        self.assertTrue(all(edge["from_field"] for edge in plan["joins"]))
        self.assertTrue(all(edge["to_field"] for edge in plan["joins"]))
        self.assertEqual(
            plan["reference_validation"]["status"],
            "validated",
        )
        self.assertFalse(
            plan["reference_validation"]["runtime_database_checked"],
        )

    def test_one_center_node_can_keep_two_query_branches(self):
        plan = build_query_builder_plan(
            ["HistoryMainline", "Container", "Employee"]
        )

        joins = {
            (
                item["from_table"],
                item["from_field"],
                item["to_table"],
                item["to_field"],
            )
            for item in plan["joins"]
        }
        self.assertIn(
            ("HistoryMainline", "ContainerId", "Container", "ContainerId"),
            joins,
        )
        self.assertIn(
            ("HistoryMainline", "EmployeeId", "Employee", "EmployeeId"),
            joins,
        )
        self.assertEqual(plan["unconnected"], [])

    def test_equal_length_join_paths_prefer_direct_branch_from_query_root(self):
        plan = build_query_builder_plan(
            ["HistoryMainline", "Container", "Product"]
        )

        joins = {
            (
                item["from_table"],
                item["from_field"],
                item["to_table"],
                item["to_field"],
            )
            for item in plan["joins"]
        }
        self.assertIn(
            ("HistoryMainline", "ContainerId", "Container", "ContainerId"),
            joins,
        )
        self.assertIn(
            ("HistoryMainline", "ProductId", "Product", "ProductId"),
            joins,
        )
        self.assertNotIn(
            ("Container", "ProductId", "Product", "ProductId"),
            joins,
        )
        self.assertIn("hm.ProductId = p.ProductId", plan["sql"])

    def test_sqlserver_identifiers_and_aliases(self):
        plan = build_query_builder_plan(
            ["Container", "CurrentStatus"],
            dialect="sqlserver",
        )
        self.assertIn("FROM [Container] AS c", plan["sql"])
        self.assertIn("JOIN [CurrentStatus] AS cs", plan["sql"])

    def test_ambiguous_physical_fk_is_disclosed(self):
        plan = build_query_builder_plan(["Container", "Spec"])
        self.assertTrue(any("物理外键候选" in item for item in plan["warnings"]))

    def test_ambiguous_join_exposes_clickable_candidates(self):
        plan = build_query_builder_plan(["HistoryMainline", "Spec"])

        group = next(
            item for item in plan["join_candidates"]
            if item["pair_key"] == "HistoryMainline|Spec"
        )
        self.assertEqual(len(group["candidates"]), 2)
        self.assertEqual(group["selected"]["from_field"], "SpecId")
        self.assertEqual(
            {item["from_field"] for item in group["candidates"]},
            {"FromSpecId", "SpecId"},
        )

    def test_join_override_rebuilds_sql_with_user_selected_candidate(self):
        override = {
            "from_table": "HistoryMainline",
            "from_field": "FromSpecId",
            "to_table": "Spec",
            "to_field": "SpecId",
        }
        plan = build_query_builder_plan(
            ["HistoryMainline", "Spec"],
            join_overrides=[override],
        )

        self.assertEqual(plan["joins"][0], override)
        self.assertIn("hm.FromSpecId = s.SpecId", plan["sql"])
        self.assertEqual(plan["join_candidates"][0]["selected"], override)

    def test_unknown_join_override_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "不是参考 Schema"):
            build_query_builder_plan(
                ["HistoryMainline", "Spec"],
                join_overrides=[{
                    "from_table": "HistoryMainline",
                    "from_field": "MadeUpSpecId",
                    "to_table": "Spec",
                    "to_field": "SpecId",
                }],
            )

    def test_unknown_table_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "未知物理对象"):
            build_query_builder_plan(["DefinitelyNotATable"])


if __name__ == "__main__":
    unittest.main()
