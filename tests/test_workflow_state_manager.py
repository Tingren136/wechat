import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "skills" / "wechat-article-workflow" / "scripts" / "workflow_state_manager.py"


def load_module():
    spec = importlib.util.spec_from_file_location("workflow_state_manager", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WorkflowStateManagerTests(unittest.TestCase):
    def test_initialize_state_creates_expected_stage_sequence(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            planning_dir.mkdir(parents=True)
            state_path = planning_dir / "工作流状态.json"

            state = module.initialize_state(
                state_path=state_path,
                title="测试文章",
                artifacts={"draft": "01-原稿/01-草稿.md"},
            )

            self.assertTrue(state_path.exists())
            self.assertEqual(state["title"], "测试文章")
            self.assertEqual(state["current_stage_id"], "polish_review")
            self.assertEqual(state["current_stage_label"], "润色完成后确认")
            self.assertEqual(state["current_stage_index"], 0)
            self.assertEqual(len(state["stages"]), 8)
            self.assertEqual(state["stages"][0]["id"], "polish_review")
            self.assertEqual(state["stages"][-1]["id"], "draft_publish_review")
            self.assertIn("approval_dir", state["artifacts"])

    def test_advance_stage_moves_to_next_confirmation_and_finishes(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            planning_dir.mkdir(parents=True)
            state_path = planning_dir / "工作流状态.json"
            module.initialize_state(
                state_path=state_path,
                title="测试文章",
                artifacts={"draft": "01-原稿/01-草稿.md"},
            )

            next_state = module.advance_stage(state_path, note="润色已确认")
            self.assertEqual(next_state["current_stage_id"], "markdown_review")
            self.assertEqual(next_state["history"][0]["note"], "润色已确认")

            for _ in range(6):
                next_state = module.advance_stage(state_path)

            self.assertEqual(next_state["current_stage_id"], "draft_publish_review")
            finished = module.advance_stage(state_path, note="允许进入草稿箱")
            self.assertEqual(finished["status"], "completed")
            self.assertEqual(finished["current_stage_id"], "completed")
            self.assertEqual(finished["history"][-1]["note"], "允许进入草稿箱")

    def test_record_stage_approval_writes_receipt_for_current_stage(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            planning_dir.mkdir(parents=True)
            approval_dir = planning_dir / "人工确认"
            state_path = planning_dir / "工作流状态.json"

            module.initialize_state(
                state_path=state_path,
                title="测试文章",
                artifacts={"draft": "01-原稿/01-草稿.md", "approval_dir": str(approval_dir)},
            )

            state = module.record_stage_approval(state_path, note="用户已确认润色稿可以继续")

            self.assertEqual(state["last_approval"]["stage_id"], "polish_review")
            receipt_path = approval_dir / "01-润色完成后确认.txt"
            self.assertTrue(receipt_path.exists())
            self.assertIn("用户已确认润色稿可以继续", receipt_path.read_text(encoding="utf-8"))

    def test_set_selected_theme_updates_state_and_theme_file(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            delivery_dir = article_dir / "06-发布"
            planning_dir.mkdir(parents=True)
            delivery_dir.mkdir(parents=True)
            state_path = planning_dir / "工作流状态.json"
            theme_path = delivery_dir / "已选主题.txt"

            module.initialize_state(
                state_path=state_path,
                title="测试文章",
                artifacts={"draft": "01-原稿/01-草稿.md", "selected_theme": str(theme_path)},
            )

            state = module.set_selected_theme(state_path, "Claude")

            self.assertEqual(state["selected_theme"], "Claude")
            self.assertEqual(theme_path.read_text(encoding="utf-8"), "Claude")


if __name__ == "__main__":
    unittest.main()
