# Workflow Validation And Guardrails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给公众号工作流补上可执行的阶段校验与推进保护层，把“300 字视觉中断规则”和关键阶段产物检查真正编码进主 skill。

**Architecture:** 新增一个独立的 `workflow_validator.py`，专门负责读取工作区和状态文件，生成阶段检查结果与中文报告。`workflow_executor.py` 在 `status` 时附带校验结果，在 `confirm` 时默认阻止带 blocker 的推进，只允许显式放行。

**Tech Stack:** Python 3、unittest、现有 `workflow_state_manager.py` / `workflow_stage_runner.py` / `workflow_bundle.py`

---

## File Structure

- Create: `skills/wechat-article-workflow/scripts/workflow_validator.py`
  - 负责阶段校验、300 字视觉中断检查、中文检查报告生成。
- Modify: `skills/wechat-article-workflow/scripts/workflow_executor.py`
  - 在 `status` 中返回校验结果。
  - 在 `confirm` 中默认阻止 blocker，并支持显式放行。
- Modify: `skills/wechat-article-workflow/SKILL.md`
  - 说明新的检查与推进规则。
- Modify: `README.md`
  - 记录主工作流已内建阶段校验与视觉中断检查。
- Modify: `docs/PROJECT_STATUS.md`
  - 更新当前完成状态与剩余边界。
- Create: `tests/test_workflow_validator.py`
  - 覆盖阶段校验、视觉中断规则、中文报告生成。
- Modify: `tests/test_workflow_executor.py`
  - 覆盖 `status` 返回校验结果。
  - 覆盖 `confirm` 在 blocker 存在时阻止推进。
  - 覆盖显式放行时允许推进。

## Task 1: 为视觉中断规则写失败测试

**Files:**
- Create: `tests/test_workflow_validator.py`
- Modify: `skills/wechat-article-workflow/scripts/workflow_validator.py`

- [ ] **Step 1: 写失败测试，锁定“超过 300 中文字未被打断”会报 blocker**

```python
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
```

- [ ] **Step 2: 运行测试并确认它先失败**

Run: `py -m unittest tests.test_workflow_validator.WorkflowValidatorTests.test_validator_flags_long_plain_text_without_visual_break`

Expected: FAIL，因为 `workflow_validator.py` 还不存在。

- [ ] **Step 3: 写最小实现，让检查器能识别长纯文字段**

```python
def scan_markdown_visual_breaks(markdown: str, max_chars: int = 300) -> list[dict[str, Any]]:
    # 识别图片、表格、引用块、代码块、列表等非纯正文段；对连续正文累计中文字符数。
    ...
```

- [ ] **Step 4: 再跑同一条测试，确认变绿**

Run: `py -m unittest tests.test_workflow_validator.WorkflowValidatorTests.test_validator_flags_long_plain_text_without_visual_break`

Expected: PASS

- [ ] **Step 5: 提交这一小步**

```bash
git add tests/test_workflow_validator.py skills/wechat-article-workflow/scripts/workflow_validator.py
git commit -m "Add visual break validator"
```

## Task 2: 为阶段产物检查写失败测试

**Files:**
- Modify: `tests/test_workflow_validator.py`
- Modify: `skills/wechat-article-workflow/scripts/workflow_validator.py`

- [ ] **Step 1: 写失败测试，锁定 `layout_review` 必须有 4 套预览和 4 套发布版**

```python
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
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"))

        result = validator.validate_stage(state_path)

        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any(item["code"] == "missing_theme_outputs" for item in result["issues"]))
```

- [ ] **Step 2: 运行测试并确认先失败**

Run: `py -m unittest tests.test_workflow_validator.WorkflowValidatorTests.test_validator_flags_missing_layout_outputs`

Expected: FAIL，当前还没有阶段产物检查。

- [ ] **Step 3: 补最小实现，为关键阶段增加文件存在性和完整性检查**

```python
STAGE_VALIDATORS = {
    "layout_review": validate_layout_outputs,
    "image_insert_review": validate_with_images_markdown,
    "draft_publish_review": validate_publish_inputs,
}
```

- [ ] **Step 4: 重新跑测试确认变绿**

Run: `py -m unittest tests.test_workflow_validator.WorkflowValidatorTests.test_validator_flags_missing_layout_outputs -v`

Expected: PASS

- [ ] **Step 5: 提交这一小步**

```bash
git add tests/test_workflow_validator.py skills/wechat-article-workflow/scripts/workflow_validator.py
git commit -m "Add stage artifact validation"
```

## Task 3: 为执行器守门行为写失败测试

**Files:**
- Modify: `tests/test_workflow_executor.py`
- Modify: `skills/wechat-article-workflow/scripts/workflow_executor.py`

- [ ] **Step 1: 写失败测试，锁定 `status` 必须返回 `validation`**

```python
def test_status_returns_validation_packet(self):
    ...
    status = executor.get_status(state_path)
    self.assertIn("validation", status)
```

- [ ] **Step 2: 写失败测试，锁定 `confirm` 在 blocker 存在时不推进**

```python
def test_confirm_current_stage_blocks_when_validation_has_blockers(self):
    ...
    with self.assertRaisesRegex(RuntimeError, "仍有未处理的阻塞项"):
        executor.confirm_current_stage(state_path)
```

- [ ] **Step 3: 运行测试并确认先失败**

Run: `py -m unittest tests.test_workflow_executor -v`

Expected: FAIL，因为执行器还没接入 validator。

- [ ] **Step 4: 写最小实现，让 `status` 返回校验结果，`confirm` 默认阻止推进**

```python
def confirm_current_stage(state_path: Path, note: str = "", allow_issues: bool = False) -> dict[str, Any]:
    validation = validator.validate_stage(state_path)
    if validation["status"] == "blocked" and not allow_issues:
        raise RuntimeError("当前阶段仍有未处理的阻塞项")
    ...
```

- [ ] **Step 5: 再跑执行器测试确认变绿**

Run: `py -m unittest tests.test_workflow_executor -v`

Expected: PASS

- [ ] **Step 6: 提交这一小步**

```bash
git add tests/test_workflow_executor.py skills/wechat-article-workflow/scripts/workflow_executor.py
git commit -m "Add executor validation guardrails"
```

## Task 4: 补 CLI 与文档闭环

**Files:**
- Modify: `skills/wechat-article-workflow/scripts/workflow_executor.py`
- Modify: `skills/wechat-article-workflow/SKILL.md`
- Modify: `README.md`
- Modify: `docs/PROJECT_STATUS.md`

- [ ] **Step 1: 给 CLI 增加 `--allow-issues` 入口**

```python
confirm_parser.add_argument("--allow-issues", action="store_true")
```

- [ ] **Step 2: 在文档中写清楚默认守门和显式放行规则**

```markdown
- `status` 会输出当前阶段校验结果与中文报告
- `confirm` 默认不会跨过 blocker
- 只有显式传入 `--allow-issues` 时，才允许带问题推进
```

- [ ] **Step 3: 跑回归测试**

Run: `py -m unittest tests.test_workflow_validator tests.test_workflow_executor tests.test_workflow_state_manager tests.test_workflow_stage_runner tests.test_wechat_article_workflow_bundle tests.test_install_local_skill tests.test_wechat_workflow_dependencies tests.test_claude_publish_export`

Expected: 全绿

- [ ] **Step 4: 做一次真实命令行验收**

Run:

```powershell
$result = py .\skills\wechat-article-workflow\scripts\workflow_bundle.py `
  "H:\3.写公众号素材\某篇文章.md" `
  --image-root "H:\3.写公众号素材\imgs" `
  --json | ConvertFrom-Json

py .\skills\wechat-article-workflow\scripts\workflow_executor.py status --state-path $result.files.state_path
py .\skills\wechat-article-workflow\scripts\workflow_executor.py confirm --state-path $result.files.state_path
```

Expected:
- `status` 返回 `validation`
- 当阶段缺产物时，`confirm` 报阻塞错误
- 在补齐产物或显式 `--allow-issues` 后，才允许推进

- [ ] **Step 5: 提交这一小步**

```bash
git add README.md docs/PROJECT_STATUS.md skills/wechat-article-workflow/SKILL.md skills/wechat-article-workflow/scripts/workflow_executor.py
git commit -m "Document workflow validation guardrails"
```

## Self-Review

- 这个计划覆盖了当前最缺的两层：规则真正落代码、执行器真正有守门逻辑。
- 没有引入与当前范围无关的封面工作流、真实生图调用、真实发布 API 重构。
- 类型命名统一围绕 `validation`、`issues`、`status`、`allow_issues`，避免后续接口漂移。
