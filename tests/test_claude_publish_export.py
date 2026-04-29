import tempfile
import unittest
from pathlib import Path
import importlib.util


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "claude_publish_export.py"


def load_module():
    spec = importlib.util.spec_from_file_location("claude_publish_export", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SAMPLE_MARKDOWN = """---
title: 测试文章
author: 栗子智培
summary: 用于验证发布态导出。
---

# 测试文章

这是一段普通正文，里面有 **重点句子**，也有一点英文 AI。

![AI 最稀缺的价值之一，不只是懂得多，而是它愿意一遍又一遍地陪你讲明白。](demo.png)

## 对比表

| 项目 | 说明 |
| --- | --- |
| 排版 | 内联样式 |
| 图片 | 要有图注 |

```python
print("hello")
```
"""


class ClaudePublishExportTests(unittest.TestCase):
    def test_export_creates_wechat_safe_inline_html(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
          temp_path = Path(temp_dir)
          markdown_path = temp_path / "article.md"
          image_path = temp_path / "demo.png"
          output_path = temp_path / "article.claude.publish.html"
          markdown_path.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
          image_path.write_bytes(b"fake-image")

          result = module.export_markdown_to_html(markdown_path, output_path)
          html = output_path.read_text(encoding="utf-8")
          figcaption = html.split("<figcaption", 1)[1].split("</figcaption>", 1)[0]
          figure = html.split("<figure", 1)[1].split(">", 1)[0]

          self.assertEqual(result["title"], "测试文章")
          self.assertTrue(output_path.exists())
          self.assertNotIn("<style", html)
          self.assertNotIn("<script", html)
          self.assertNotIn('class="', html)
          self.assertIn("<figure", html)
          self.assertIn("<figcaption", html)
          self.assertIn("text-align:center", html)
          self.assertIn("overflow:hidden", figure)
          self.assertIn("AI 愿意一遍又一遍地陪你讲明白。", html)
          self.assertNotIn("AI 最稀缺的价值之一，不只是懂得多，而是它愿意一遍又一遍地陪你讲明白。", figcaption)
          self.assertIn("<table", html)
          self.assertIn("border-collapse:collapse", html)
          self.assertIn("<pre", html)
          self.assertIn("background:#2f3138", html)
          self.assertNotIn("<ol", html)
          self.assertNotIn("<li", html)

    def test_export_rewrites_local_image_paths_for_output_directory(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
          temp_path = Path(temp_dir)
          article_dir = temp_path / "imgs" / "示例文章"
          article_dir.mkdir(parents=True)
          markdown_path = temp_path / "article.md"
          output_path = article_dir / "publish.html"
          image_path = article_dir / "demo.png"
          markdown_path.write_text(
              SAMPLE_MARKDOWN.replace("(demo.png)", "(imgs/示例文章/demo.png)"),
              encoding="utf-8",
          )
          image_path.write_bytes(b"fake-image")

          module.export_markdown_to_html(markdown_path, output_path)
          html = output_path.read_text(encoding="utf-8")

          self.assertIn('src="demo.png"', html)
          self.assertNotIn('src="imgs/示例文章/demo.png"', html)

    def test_ordered_lists_are_rendered_as_safe_manual_blocks(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
          temp_path = Path(temp_dir)
          markdown_path = temp_path / "article.md"
          output_path = temp_path / "article.claude.publish.html"
          markdown_path.write_text(
              """# 列表测试

1. 第一条内容
2. 第二条内容
3. 第三条内容
""",
              encoding="utf-8",
          )

          module.export_markdown_to_html(markdown_path, output_path)
          html = output_path.read_text(encoding="utf-8")

          self.assertNotIn("<ol", html)
          self.assertNotIn("<ul", html)
          self.assertNotIn("<li", html)
          self.assertIn("data-wechat-list=\"ordered\"", html)
          self.assertIn(">1.</span>", html)
          self.assertIn(">2.</span>", html)
          self.assertIn(">3.</span>", html)

    def test_supports_multiple_publish_themes(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
          temp_path = Path(temp_dir)
          markdown_path = temp_path / "article.md"
          image_path = temp_path / "demo.png"
          markdown_path.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
          image_path.write_bytes(b"fake-image")

          expected_theme_markers = {
              "claude": "color:#d86d47",
              "nyt": "font-family:Georgia",
              "deep-reading": "border-left:5px solid #c9d4e5",
              "medium": "font-size:20px;line-height:1.92;color:#242424",
          }

          for theme_id, marker in expected_theme_markers.items():
              output_path = temp_path / f"{theme_id}.publish.html"
              module.export_markdown_to_html(markdown_path, output_path, theme_id=theme_id)
              html = output_path.read_text(encoding="utf-8")

              self.assertNotIn("<style", html)
              self.assertNotIn("<script", html)
              self.assertNotIn("<ol", html)
              self.assertIn(marker, html)


if __name__ == "__main__":
    unittest.main()
