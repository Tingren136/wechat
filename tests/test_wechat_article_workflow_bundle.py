import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "skills" / "wechat-article-workflow" / "scripts" / "workflow_bundle.py"


def load_module():
    spec = importlib.util.spec_from_file_location("workflow_bundle", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SAMPLE_MARKDOWN = """---
title: 技能测试文章
author: 栗子智培
summary: 用于验证 skill bundle 输出。
---

# 技能测试文章

这是一段正文，用来测试最小稳定闭环。

![这是一张用于测试图注和相对路径改写的示意图片。](demo.png)

## 小节

1. 第一条
2. 第二条
"""


class WechatArticleWorkflowBundleTests(unittest.TestCase):
    def test_export_article_bundle_creates_categorized_workspace_and_all_theme_outputs(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            markdown_path = temp_path / "draft.md"
            image_root = temp_path / "imgs"
            markdown_path.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
            (temp_path / "demo.png").write_bytes(b"fake-image")

            result = module.export_article_bundle(markdown_path, image_root)

            article_dir = image_root / "技能测试文章"
            self.assertEqual(result["title"], "技能测试文章")
            self.assertEqual(Path(result["article_dir"]), article_dir)
            self.assertTrue(article_dir.exists())
            self.assertEqual(sorted(result["themes"].keys()), ["claude", "deep-reading", "medium", "nyt"])
            self.assertTrue((article_dir / "01-原稿").exists())
            self.assertTrue((article_dir / "02-规划").exists())
            self.assertTrue((article_dir / "03-提示词" / "草稿").exists())
            self.assertTrue((article_dir / "03-提示词" / "定稿").exists())
            self.assertTrue((article_dir / "04-素材" / "正文配图").exists())
            self.assertTrue((article_dir / "04-素材" / "封面配图").exists())
            self.assertTrue((article_dir / "05-排版" / "预览版").exists())
            self.assertTrue((article_dir / "05-排版" / "发布版").exists())
            self.assertTrue((article_dir / "06-发布").exists())
            self.assertTrue((article_dir / "02-规划" / "工作流状态.json").exists())
            self.assertTrue((article_dir / "02-规划" / "当前阶段说明.md").exists())
            self.assertTrue((article_dir / "02-规划" / "规则摘要.md").exists())
            self.assertTrue((article_dir / "02-规划" / "发布检查清单.md").exists())
            self.assertTrue((article_dir / "01-原稿" / "01-草稿.md").exists())
            self.assertTrue((article_dir / "01-原稿" / "02-润色稿.md").exists())
            self.assertTrue((article_dir / "01-原稿" / "03-整理稿.md").exists())
            self.assertTrue((article_dir / "01-原稿" / "04-配图稿.md").exists())
            self.assertTrue((article_dir / "04-素材" / "正文配图" / "demo.png").exists())
            self.assertTrue((article_dir / "06-发布" / "已选主题.txt").exists())
            state = json.loads((article_dir / "02-规划" / "工作流状态.json").read_text(encoding="utf-8"))
            self.assertEqual(state["current_stage_id"], "polish_review")
            self.assertEqual(state["current_stage_label"], "润色完成后确认")
            self.assertEqual(Path(result["files"]["state_path"]), article_dir / "02-规划" / "工作流状态.json")
            self.assertEqual(Path(result["files"]["instruction_file"]), article_dir / "02-规划" / "当前阶段说明.md")
            self.assertEqual(Path(result["files"]["selected_theme_file"]), article_dir / "06-发布" / "已选主题.txt")

            for theme_id, paths in result["themes"].items():
                preview_path = Path(paths["preview"])
                publish_path = Path(paths["publish"])
                self.assertTrue(preview_path.exists(), theme_id)
                self.assertTrue(publish_path.exists(), theme_id)
                self.assertEqual(preview_path.parent, article_dir / "05-排版" / "预览版")
                self.assertEqual(publish_path.parent, article_dir / "05-排版" / "发布版")

                preview_html = preview_path.read_text(encoding="utf-8")
                publish_html = publish_path.read_text(encoding="utf-8")

                self.assertIn("技能测试文章", preview_html)
                self.assertIn("技能测试文章", publish_html)
                self.assertIn("正文配图/demo.png", preview_html)
                self.assertIn("正文配图/demo.png", publish_html)
                self.assertIn("预览版", preview_html)
                self.assertNotIn("预览版", publish_html)

    def test_cli_json_output_exposes_state_path_for_chinese_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            markdown_path = temp_path / "draft.md"
            image_root = temp_path / "imgs"
            markdown_path.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
            (temp_path / "demo.png").write_bytes(b"fake-image")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    str(markdown_path),
                    "--image-root",
                    str(image_root),
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            payload = json.loads(completed.stdout)
            article_dir = image_root / "技能测试文章"
            self.assertEqual(Path(payload["article_dir"]), article_dir)
            self.assertEqual(Path(payload["files"]["state_path"]), article_dir / "02-规划" / "工作流状态.json")
            self.assertTrue(Path(payload["files"]["state_path"]).exists())

    def test_export_article_bundle_does_not_reset_existing_workflow_state(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            markdown_path = temp_path / "draft.md"
            image_root = temp_path / "imgs"
            markdown_path.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
            (temp_path / "demo.png").write_bytes(b"fake-image")

            first = module.export_article_bundle(markdown_path, image_root)
            state_path = Path(first["files"]["state_path"])

            # 模拟用户已推进到下一阶段
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["current_stage_id"] = "markdown_review"
            state["current_stage_label"] = "Markdown整理后确认"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

            second = module.export_article_bundle(markdown_path, image_root)
            updated = json.loads(state_path.read_text(encoding="utf-8"))

            self.assertEqual(Path(second["files"]["state_path"]), state_path)
            self.assertEqual(updated["current_stage_id"], "markdown_review")
            self.assertEqual(updated["current_stage_label"], "Markdown整理后确认")


if __name__ == "__main__":
    unittest.main()
