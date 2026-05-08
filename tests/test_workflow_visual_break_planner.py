import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLANNER_MODULE_PATH = REPO_ROOT / "skills" / "wechat-article-workflow" / "scripts" / "workflow_visual_break_planner.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WorkflowVisualBreakPlannerTests(unittest.TestCase):
    def test_required_breaks_calculation_matches_300_rule(self):
        planner = load_module(PLANNER_MODULE_PATH, "workflow_visual_break_planner")
        with tempfile.TemporaryDirectory() as temp_dir:
            markdown_path = Path(temp_dir) / "03-整理稿.md"
            markdown = "\n\n".join(
                [
                    "# 标题",
                    "甲" * 603,
                    "![图1](a.png)",
                    "乙" * 727,
                    "![图2](b.png)",
                    "丙" * 620,
                    "![图3](c.png)",
                    "丁" * 506,
                ]
            )
            markdown_path.write_text(markdown, encoding="utf-8")

            plan = planner.build_plan(markdown_path=markdown_path, max_chars=300)

            self.assertEqual(plan["required_body_images"], 7)
            breaks = [block["required_breaks"] for block in plan["long_plain_text_blocks"]]
            self.assertEqual(breaks, [2, 2, 2, 1])

    def test_load_density_max_chars_from_config(self):
        planner = load_module(PLANNER_MODULE_PATH, "workflow_visual_break_planner")
        with tempfile.TemporaryDirectory() as temp_dir:
            planning_dir = Path(temp_dir) / "02-规划"
            planning_dir.mkdir(parents=True)
            (planning_dir / "配图密度配置.json").write_text(
                '{"density_profile":"medium","max_chars_per_break":400}',
                encoding="utf-8",
            )
            self.assertEqual(planner.load_density_max_chars(planning_dir), 400)


if __name__ == "__main__":
    unittest.main()
