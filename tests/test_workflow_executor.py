import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_MODULE_PATH = REPO_ROOT / "skills" / "wechat-article-workflow" / "scripts" / "workflow_state_manager.py"
RUNNER_MODULE_PATH = REPO_ROOT / "skills" / "wechat-article-workflow" / "scripts" / "workflow_stage_runner.py"
EXECUTOR_MODULE_PATH = REPO_ROOT / "skills" / "wechat-article-workflow" / "scripts" / "workflow_executor.py"
BUILDER_MODULE_PATH = REPO_ROOT / "skills" / "wechat-article-workflow" / "scripts" / "workflow_bundle.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SAMPLE_MARKDOWN = """---
title: 执行器测试文章
author: 栗子智培
summary: 用于验证执行器。
---

# 执行器测试文章

这是一段正文。

![测试图片说明。](demo.png)
"""


class WorkflowExecutorTests(unittest.TestCase):
    def test_confirm_current_stage_advances_and_refreshes_brief(self):
        builder = load_module(BUILDER_MODULE_PATH, "workflow_bundle")
        executor = load_module(EXECUTOR_MODULE_PATH, "workflow_executor")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            markdown_path = temp_path / "draft.md"
            image_root = temp_path / "imgs"
            markdown_path.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
            (temp_path / "demo.png").write_bytes(b"fake-image")

            result = builder.export_article_bundle(markdown_path, image_root)
            state_path = Path(result["workspace"]["planning"]) / "工作流状态.json"

            updated = executor.confirm_current_stage(state_path, note="润色完成")

            self.assertEqual(updated["state"]["current_stage_id"], "markdown_review")
            self.assertEqual(updated["packet"]["stage_id"], "markdown_review")
            self.assertIn("baoyu-format-markdown", updated["packet"]["recommended_skill"])

    def test_select_theme_updates_state_and_theme_file(self):
        builder = load_module(BUILDER_MODULE_PATH, "workflow_bundle")
        executor = load_module(EXECUTOR_MODULE_PATH, "workflow_executor")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            markdown_path = temp_path / "draft.md"
            image_root = temp_path / "imgs"
            markdown_path.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
            (temp_path / "demo.png").write_bytes(b"fake-image")

            result = builder.export_article_bundle(markdown_path, image_root)
            state_path = Path(result["workspace"]["planning"]) / "工作流状态.json"

            updated = executor.select_theme(state_path, "Claude")

            self.assertEqual(updated["state"]["selected_theme"], "Claude")
            self.assertEqual(Path(result["workspace"]["delivery"]).joinpath("已选主题.txt").read_text(encoding="utf-8"), "Claude")

    def test_refresh_layout_outputs_rebuilds_preview_and_publish_html(self):
        builder = load_module(BUILDER_MODULE_PATH, "workflow_bundle")
        executor = load_module(EXECUTOR_MODULE_PATH, "workflow_executor")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            markdown_path = temp_path / "draft.md"
            image_root = temp_path / "imgs"
            markdown_path.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
            (temp_path / "demo.png").write_bytes(b"fake-image")

            result = builder.export_article_bundle(markdown_path, image_root)
            article_dir = Path(result["article_dir"])
            with_images_path = article_dir / "01-原稿" / "04-配图稿.md"
            with_images_path.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
            state_path = article_dir / "02-规划" / "工作流状态.json"

            refreshed = executor.refresh_layout_outputs(state_path)

            self.assertEqual(sorted(refreshed["themes"].keys()), ["claude", "deep-reading", "medium", "nyt"])
            self.assertTrue((article_dir / "05-排版" / "预览版" / "最终排版-Claude.html").exists())
            self.assertTrue((article_dir / "05-排版" / "发布版" / "最终排版-Claude-发布版.html").exists())


if __name__ == "__main__":
    unittest.main()
