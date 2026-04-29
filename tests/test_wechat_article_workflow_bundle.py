import importlib.util
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
            self.assertTrue((article_dir / "00-source").exists())
            self.assertTrue((article_dir / "01-planning").exists())
            self.assertTrue((article_dir / "02-prompts" / "draft").exists())
            self.assertTrue((article_dir / "02-prompts" / "final").exists())
            self.assertTrue((article_dir / "03-assets" / "body-images").exists())
            self.assertTrue((article_dir / "03-assets" / "cover-images").exists())
            self.assertTrue((article_dir / "04-output" / "previews").exists())
            self.assertTrue((article_dir / "04-output" / "publish").exists())
            self.assertTrue((article_dir / "05-delivery").exists())
            self.assertTrue((article_dir / "01-planning" / "workflow-state.json").exists())
            self.assertTrue((article_dir / "01-planning" / "rules-summary.md").exists())
            self.assertTrue((article_dir / "01-planning" / "publish-checklist.md").exists())
            self.assertTrue((article_dir / "00-source" / "01-draft.md").exists())
            self.assertTrue((article_dir / "00-source" / "02-polished.md").exists())
            self.assertTrue((article_dir / "00-source" / "03-formatted.md").exists())
            self.assertTrue((article_dir / "00-source" / "04-with-images.md").exists())
            self.assertTrue((article_dir / "03-assets" / "body-images" / "demo.png").exists())
            self.assertTrue((article_dir / "05-delivery" / "selected-theme.txt").exists())

            for theme_id, paths in result["themes"].items():
                preview_path = Path(paths["preview"])
                publish_path = Path(paths["publish"])
                self.assertTrue(preview_path.exists(), theme_id)
                self.assertTrue(publish_path.exists(), theme_id)
                self.assertEqual(preview_path.parent, article_dir / "04-output" / "previews")
                self.assertEqual(publish_path.parent, article_dir / "04-output" / "publish")

                preview_html = preview_path.read_text(encoding="utf-8")
                publish_html = publish_path.read_text(encoding="utf-8")

                self.assertIn("技能测试文章", preview_html)
                self.assertIn("技能测试文章", publish_html)
                self.assertIn("../..", preview_html)
                self.assertIn("../..", publish_html)
                self.assertIn("body-images/demo.png", preview_html)
                self.assertIn("body-images/demo.png", publish_html)
                self.assertIn("预览版", preview_html)
                self.assertNotIn("预览版", publish_html)


if __name__ == "__main__":
    unittest.main()
