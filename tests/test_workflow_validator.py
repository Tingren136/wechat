import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_MODULE_PATH = REPO_ROOT / "skills" / "wechat-article-workflow" / "scripts" / "workflow_validator.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WorkflowValidatorTests(unittest.TestCase):
    def test_validator_flags_long_plain_text_without_visual_break(self):
        validator = load_module(VALIDATOR_MODULE_PATH, "workflow_validator")
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            source_dir = article_dir / "01-原稿"
            planning_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)

            markdown = "# 标题\n\n" + ("这是一段很长的正文" * 80)
            (source_dir / "04-配图稿.md").write_text(markdown, encoding="utf-8")

            state = {
                "title": "测试文章",
                "current_stage_id": "image_insert_review",
                "current_stage_label": "插图回正文后确认",
                "artifacts": {"with_images": str(source_dir / "04-配图稿.md")},
            }
            state_path = planning_dir / "工作流状态.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

            result = validator.validate_stage(state_path)

            self.assertEqual(result["status"], "blocked")
            self.assertTrue(any(item["code"] == "long_plain_text_block" for item in result["issues"]))
            self.assertTrue((planning_dir / "阶段检查报告.md").exists())

    def test_validator_passes_when_visual_breaks_are_present(self):
        validator = load_module(VALIDATOR_MODULE_PATH, "workflow_validator")
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            source_dir = article_dir / "01-原稿"
            planning_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)

            markdown = "\n\n".join(
                [
                    "# 标题",
                    "这是一段正文" * 20,
                    "![配图说明](demo.png)",
                    "这是一段正文" * 20,
                    "> 引用块也算视觉中断",
                    "这是一段正文" * 20,
                ]
            )
            (source_dir / "04-配图稿.md").write_text(markdown, encoding="utf-8")

            state = {
                "title": "测试文章",
                "current_stage_id": "image_insert_review",
                "current_stage_label": "插图回正文后确认",
                "artifacts": {"with_images": str(source_dir / "04-配图稿.md")},
            }
            state_path = planning_dir / "工作流状态.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

            result = validator.validate_stage(state_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["issues"], [])

    def test_validator_flags_missing_layout_outputs(self):
        validator = load_module(VALIDATOR_MODULE_PATH, "workflow_validator")
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            publish_dir = article_dir / "05-排版" / "发布版"
            preview_dir = article_dir / "05-排版" / "预览版"
            planning_dir.mkdir(parents=True)
            publish_dir.mkdir(parents=True)
            preview_dir.mkdir(parents=True)

            state = {
                "title": "测试文章",
                "current_stage_id": "layout_review",
                "current_stage_label": "四套排版产出后确认",
                "artifacts": {},
            }
            state_path = planning_dir / "工作流状态.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

            result = validator.validate_stage(state_path)

            self.assertEqual(result["status"], "blocked")
            self.assertTrue(any(item["code"] == "missing_theme_outputs" for item in result["issues"]))


if __name__ == "__main__":
    unittest.main()
