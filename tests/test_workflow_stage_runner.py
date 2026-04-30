import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_MODULE_PATH = REPO_ROOT / "skills" / "wechat-article-workflow" / "scripts" / "workflow_state_manager.py"
RUNNER_MODULE_PATH = REPO_ROOT / "skills" / "wechat-article-workflow" / "scripts" / "workflow_stage_runner.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WorkflowStageRunnerTests(unittest.TestCase):
    def test_stage_runner_generates_stage_packet_for_current_stage(self):
        state_module = load_module(STATE_MODULE_PATH, "workflow_state_manager")
        runner_module = load_module(RUNNER_MODULE_PATH, "workflow_stage_runner")
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            source_dir = article_dir / "01-原稿"
            planning_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            state_path = planning_dir / "工作流状态.json"
            artifacts = {
                "draft": str(source_dir / "01-草稿.md"),
                "polished": str(source_dir / "02-润色稿.md"),
                "formatted": str(source_dir / "03-整理稿.md"),
                "with_images": str(source_dir / "04-配图稿.md"),
                "publish_checklist": str(planning_dir / "发布检查清单.md"),
                "selected_theme": str(article_dir / "06-发布" / "已选主题.txt"),
            }
            state_module.initialize_state(state_path=state_path, title="测试文章", artifacts=artifacts)

            packet = runner_module.generate_stage_packet(state_path)

            self.assertEqual(packet["stage_id"], "polish_review")
            self.assertEqual(packet["stage_label"], "润色完成后确认")
            self.assertIn("next_steps", packet)
            self.assertGreaterEqual(len(packet["next_steps"]), 2)
            self.assertIn("suggested_commands", packet)
            self.assertTrue(any("khazix-writer" in item for item in packet["next_steps"]))
            self.assertTrue((planning_dir / "当前阶段说明.md").exists())
            text = (planning_dir / "当前阶段说明.md").read_text(encoding="utf-8")
            self.assertIn("khazix-writer", text)
            self.assertIn("02-润色稿.md", text)
            self.assertIn("确认后才能进入下一阶段", text)
            self.assertIn("建议命令", text)

    def test_stage_runner_updates_packet_after_advancing(self):
        state_module = load_module(STATE_MODULE_PATH, "workflow_state_manager")
        runner_module = load_module(RUNNER_MODULE_PATH, "workflow_stage_runner")
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            source_dir = article_dir / "01-原稿"
            planning_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            state_path = planning_dir / "工作流状态.json"
            artifacts = {
                "draft": str(source_dir / "01-草稿.md"),
                "polished": str(source_dir / "02-润色稿.md"),
                "formatted": str(source_dir / "03-整理稿.md"),
                "with_images": str(source_dir / "04-配图稿.md"),
                "publish_checklist": str(planning_dir / "发布检查清单.md"),
                "selected_theme": str(article_dir / "06-发布" / "已选主题.txt"),
            }
            state_module.initialize_state(state_path=state_path, title="测试文章", artifacts=artifacts)
            state_module.advance_stage(state_path, note="润色已确认")

            packet = runner_module.generate_stage_packet(state_path)

            self.assertEqual(packet["stage_id"], "markdown_review")
            self.assertIn("baoyu-format-markdown", packet["recommended_skill"])
            self.assertIn("03-整理稿.md", json.dumps(packet, ensure_ascii=False))
            self.assertTrue(any("baoyu-format-markdown" in item for item in packet["next_steps"]))


if __name__ == "__main__":
    unittest.main()
