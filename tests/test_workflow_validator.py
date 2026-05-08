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
    def test_validator_blocks_image_count_review_without_density_config(self):
        validator = load_module(VALIDATOR_MODULE_PATH, "workflow_validator")
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            source_dir = article_dir / "01-原稿"
            approval_dir = planning_dir / "人工确认"
            planning_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            approval_dir.mkdir(parents=True)

            markdown = "# 标题\n\n" + ("这是一段很长的正文" * 80)
            (source_dir / "03-整理稿.md").write_text(markdown, encoding="utf-8")
            (planning_dir / "视觉中断清单.md").write_text("# 视觉中断清单\n", encoding="utf-8")
            (planning_dir / "视觉中断清单.json").write_text(
                json.dumps({"rule_max_chars": 300, "required_body_images": 7, "long_plain_text_blocks": []}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (planning_dir / "配图数量确认.txt").write_text("正文配图 7 张", encoding="utf-8")
            (approval_dir / "03-配图数量确认.txt").write_text("阶段: image_count_review\n状态: 已确认\n", encoding="utf-8")

            state = {
                "title": "测试文章",
                "current_stage_id": "image_count_review",
                "current_stage_label": "配图数量确认",
                "artifacts": {"formatted": str(source_dir / "03-整理稿.md"), "approval_dir": str(approval_dir)},
            }
            state_path = planning_dir / "工作流状态.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

            result = validator.validate_stage(state_path)

            self.assertEqual(result["status"], "blocked")
            self.assertTrue(any(item["code"] == "missing_density_config" for item in result["issues"]))

    def test_validator_blocks_polish_review_without_human_approval_receipt(self):
        validator = load_module(VALIDATOR_MODULE_PATH, "workflow_validator")
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            source_dir = article_dir / "01-原稿"
            approval_dir = planning_dir / "人工确认"
            planning_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            approval_dir.mkdir(parents=True)

            polished_path = source_dir / "02-润色稿.md"
            polished_path.write_text("# 润色稿\n\n内容已完成。", encoding="utf-8")

            state = {
                "title": "测试文章",
                "current_stage_id": "polish_review",
                "current_stage_label": "润色完成后确认",
                "artifacts": {
                    "polished": str(polished_path),
                    "approval_dir": str(approval_dir),
                },
            }
            state_path = planning_dir / "工作流状态.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

            result = validator.validate_stage(state_path)

            self.assertEqual(result["status"], "blocked")
            self.assertTrue(any(item["code"] == "missing_human_approval_receipt" for item in result["issues"]))

    def test_validator_flags_long_plain_text_during_image_count_review(self):
        validator = load_module(VALIDATOR_MODULE_PATH, "workflow_validator")
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            source_dir = article_dir / "01-原稿"
            approval_dir = planning_dir / "人工确认"
            planning_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            approval_dir.mkdir(parents=True)

            markdown = "# 标题\n\n" + ("这是一段很长的正文" * 80)
            (source_dir / "03-整理稿.md").write_text(markdown, encoding="utf-8")
            (planning_dir / "配图密度配置.json").write_text(
                json.dumps({"density_profile": "medium_high", "max_chars_per_break": 300}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            state = {
                "title": "测试文章",
                "current_stage_id": "image_count_review",
                "current_stage_label": "配图数量确认",
                "artifacts": {"formatted": str(source_dir / "03-整理稿.md"), "approval_dir": str(approval_dir)},
            }
            state_path = planning_dir / "工作流状态.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

            result = validator.validate_stage(state_path)

            self.assertEqual(result["status"], "blocked")
            self.assertTrue(any(item["code"] == "long_plain_text_block" for item in result["issues"]))
            self.assertTrue(any(item["code"] == "missing_visual_break_plan" for item in result["issues"]))
            self.assertTrue(any(item["code"] == "missing_visual_break_plan_json" for item in result["issues"]))

    def test_validator_blocks_when_confirmed_image_count_less_than_required(self):
        validator = load_module(VALIDATOR_MODULE_PATH, "workflow_validator")
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            source_dir = article_dir / "01-原稿"
            approval_dir = planning_dir / "人工确认"
            planning_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            approval_dir.mkdir(parents=True)

            markdown = "# 标题\n\n" + ("这是一段很长的正文" * 80)
            formatted_path = source_dir / "03-整理稿.md"
            formatted_path.write_text(markdown, encoding="utf-8")
            (planning_dir / "配图密度配置.json").write_text(
                json.dumps({"density_profile": "medium_high", "max_chars_per_break": 300}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (planning_dir / "视觉中断清单.md").write_text("# 视觉中断清单\n", encoding="utf-8")
            (planning_dir / "视觉中断清单.json").write_text(
                json.dumps({"rule_max_chars": 300, "required_body_images": 7, "long_plain_text_blocks": []}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (planning_dir / "配图数量确认.txt").write_text("正文配图 4 张", encoding="utf-8")
            (approval_dir / "03-配图数量确认.txt").write_text("阶段: image_count_review\n状态: 已确认\n", encoding="utf-8")

            state = {
                "title": "测试文章",
                "current_stage_id": "image_count_review",
                "current_stage_label": "配图数量确认",
                "artifacts": {"formatted": str(formatted_path), "approval_dir": str(approval_dir)},
            }
            state_path = planning_dir / "工作流状态.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

            result = validator.validate_stage(state_path)

            self.assertEqual(result["status"], "blocked")
            self.assertTrue(any(item["code"] == "insufficient_image_count_for_visual_breaks" for item in result["issues"]))

    def test_validator_flags_long_plain_text_without_visual_break(self):
        validator = load_module(VALIDATOR_MODULE_PATH, "workflow_validator")
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            source_dir = article_dir / "01-原稿"
            approval_dir = planning_dir / "人工确认"
            planning_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            approval_dir.mkdir(parents=True)

            markdown = "# 标题\n\n" + ("这是一段很长的正文" * 80)
            (source_dir / "04-配图稿.md").write_text(markdown, encoding="utf-8")

            state = {
                "title": "测试文章",
                "current_stage_id": "image_insert_review",
                "current_stage_label": "插图回正文后确认",
                "artifacts": {"with_images": str(source_dir / "04-配图稿.md"), "approval_dir": str(approval_dir)},
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
            approval_dir = planning_dir / "人工确认"
            planning_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            approval_dir.mkdir(parents=True)

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
            (approval_dir / "06-插图回正文后确认.txt").write_text(
                "阶段: image_insert_review\n状态: 已确认\n说明: 用户已确认配图稿。\n",
                encoding="utf-8",
            )

            state = {
                "title": "测试文章",
                "current_stage_id": "image_insert_review",
                "current_stage_label": "插图回正文后确认",
                "artifacts": {"with_images": str(source_dir / "04-配图稿.md"), "approval_dir": str(approval_dir)},
            }
            state_path = planning_dir / "工作流状态.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

            result = validator.validate_stage(state_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["issues"], [])

    def test_validator_passes_polish_review_when_human_approval_receipt_exists(self):
        validator = load_module(VALIDATOR_MODULE_PATH, "workflow_validator")
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            source_dir = article_dir / "01-原稿"
            approval_dir = planning_dir / "人工确认"
            planning_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            approval_dir.mkdir(parents=True)

            polished_path = source_dir / "02-润色稿.md"
            polished_path.write_text("# 润色稿\n\n内容已完成。", encoding="utf-8")
            (approval_dir / "01-润色完成后确认.txt").write_text(
                "阶段: polish_review\n状态: 已确认\n说明: 用户已确认润色稿可以继续。\n",
                encoding="utf-8",
            )

            state = {
                "title": "测试文章",
                "current_stage_id": "polish_review",
                "current_stage_label": "润色完成后确认",
                "artifacts": {
                    "polished": str(polished_path),
                    "approval_dir": str(approval_dir),
                },
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

    def test_validator_passes_illustration_plan_when_visual_break_plan_exists(self):
        validator = load_module(VALIDATOR_MODULE_PATH, "workflow_validator")
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            source_dir = article_dir / "01-原稿"
            prompts_dir = article_dir / "03-提示词" / "草稿"
            approval_dir = planning_dir / "人工确认"
            planning_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            prompts_dir.mkdir(parents=True)
            approval_dir.mkdir(parents=True)

            markdown = "# 标题\n\n" + ("这是一段很长的正文" * 80)
            (source_dir / "03-整理稿.md").write_text(markdown, encoding="utf-8")
            (planning_dir / "配图密度配置.json").write_text(
                json.dumps({"density_profile": "medium_high", "max_chars_per_break": 300}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (planning_dir / "配图数量确认.txt").write_text("正文配图 7 张。", encoding="utf-8")
            (planning_dir / "视觉中断清单.md").write_text(
                "# 视觉中断清单\n\n- 第 3-3 行，补一张解释型图片。\n",
                encoding="utf-8",
            )
            (planning_dir / "视觉中断清单.json").write_text(
                json.dumps({"rule_max_chars": 300, "required_body_images": 7, "long_plain_text_blocks": []}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (planning_dir / "outline.md").write_text("# outline", encoding="utf-8")
            (planning_dir / "batch.json").write_text('{"items":[1,2,3,4,5,6,7]}', encoding="utf-8")
            (planning_dir / "配图执行记录.txt").write_text(
                "planner_skill: lizi-article-illustrator\n",
                encoding="utf-8",
            )
            (prompts_dir / "01-提示词.md").write_text("一张图", encoding="utf-8")
            (approval_dir / "04-配图规划完成后确认.txt").write_text(
                "阶段: illustration_plan_review\n状态: 已确认\n说明: 用户已确认配图规划。\n",
                encoding="utf-8",
            )

            state = {
                "title": "测试文章",
                "current_stage_id": "illustration_plan_review",
                "current_stage_label": "配图规划完成后确认",
                "artifacts": {"formatted": str(source_dir / "03-整理稿.md"), "approval_dir": str(approval_dir)},
            }
            state_path = planning_dir / "工作流状态.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

            result = validator.validate_stage(state_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["issues"], [])

    def test_validator_blocks_illustration_plan_when_plus_skill_trace_missing(self):
        validator = load_module(VALIDATOR_MODULE_PATH, "workflow_validator")
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            source_dir = article_dir / "01-原稿"
            prompts_dir = article_dir / "03-提示词" / "草稿"
            approval_dir = planning_dir / "人工确认"
            planning_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            prompts_dir.mkdir(parents=True)
            approval_dir.mkdir(parents=True)

            markdown = "# 标题\n\n" + ("这是一段很长的正文" * 80)
            (source_dir / "03-整理稿.md").write_text(markdown, encoding="utf-8")
            (planning_dir / "配图密度配置.json").write_text(
                json.dumps({"density_profile": "medium_high", "max_chars_per_break": 300}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (planning_dir / "配图数量确认.txt").write_text("正文配图 7 张。", encoding="utf-8")
            (planning_dir / "视觉中断清单.md").write_text("# 视觉中断清单\n", encoding="utf-8")
            (planning_dir / "视觉中断清单.json").write_text(
                json.dumps({"rule_max_chars": 300, "required_body_images": 7, "long_plain_text_blocks": []}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (planning_dir / "outline.md").write_text("# outline", encoding="utf-8")
            (planning_dir / "batch.json").write_text('{"items":[1,2,3,4,5,6,7]}', encoding="utf-8")
            (prompts_dir / "01-提示词.md").write_text("一张图", encoding="utf-8")
            (approval_dir / "04-配图规划完成后确认.txt").write_text(
                "阶段: illustration_plan_review\n状态: 已确认\n说明: 用户已确认配图规划。\n",
                encoding="utf-8",
            )

            state = {
                "title": "测试文章",
                "current_stage_id": "illustration_plan_review",
                "current_stage_label": "配图规划完成后确认",
                "artifacts": {"formatted": str(source_dir / "03-整理稿.md"), "approval_dir": str(approval_dir)},
            }
            state_path = planning_dir / "工作流状态.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

            result = validator.validate_stage(state_path)

            self.assertEqual(result["status"], "blocked")
            self.assertTrue(any(item["code"] == "missing_planner_skill_trace" for item in result["issues"]))

    def test_validator_blocks_when_batch_image_tasks_less_than_required(self):
        validator = load_module(VALIDATOR_MODULE_PATH, "workflow_validator")
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = Path(temp_dir) / "测试文章"
            planning_dir = article_dir / "02-规划"
            source_dir = article_dir / "01-原稿"
            prompts_dir = article_dir / "03-提示词" / "草稿"
            approval_dir = planning_dir / "人工确认"
            planning_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            prompts_dir.mkdir(parents=True)
            approval_dir.mkdir(parents=True)

            markdown = "# 标题\n\n" + ("这是一段很长的正文" * 80)
            (source_dir / "03-整理稿.md").write_text(markdown, encoding="utf-8")
            (planning_dir / "配图密度配置.json").write_text(
                json.dumps({"density_profile": "medium_high", "max_chars_per_break": 300}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (planning_dir / "配图数量确认.txt").write_text("正文配图 7 张。", encoding="utf-8")
            (planning_dir / "视觉中断清单.md").write_text("# 视觉中断清单\n", encoding="utf-8")
            (planning_dir / "视觉中断清单.json").write_text(
                json.dumps({"rule_max_chars": 300, "required_body_images": 7, "long_plain_text_blocks": []}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (planning_dir / "outline.md").write_text("# outline", encoding="utf-8")
            (planning_dir / "batch.json").write_text('{"items":[1,2,3,4]}', encoding="utf-8")
            (planning_dir / "配图执行记录.txt").write_text("planner_skill: lizi-article-illustrator\n", encoding="utf-8")
            (prompts_dir / "01-提示词.md").write_text("一张图", encoding="utf-8")
            (approval_dir / "04-配图规划完成后确认.txt").write_text(
                "阶段: illustration_plan_review\n状态: 已确认\n说明: 用户已确认配图规划。\n",
                encoding="utf-8",
            )

            state = {
                "title": "测试文章",
                "current_stage_id": "illustration_plan_review",
                "current_stage_label": "配图规划完成后确认",
                "artifacts": {"formatted": str(source_dir / "03-整理稿.md"), "approval_dir": str(approval_dir)},
            }
            state_path = planning_dir / "工作流状态.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

            result = validator.validate_stage(state_path)

            self.assertEqual(result["status"], "blocked")
            self.assertTrue(any(item["code"] == "insufficient_planned_images_in_batch" for item in result["issues"]))


if __name__ == "__main__":
    unittest.main()
