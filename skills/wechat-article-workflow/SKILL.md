---
name: wechat-article-workflow
description: Use when producing a long-form WeChat Official Account article from a draft and wanting staged polishing, illustration planning, image generation, and four selectable WeChat HTML layouts with human confirmation at each key stage.
---

# WeChat Article Workflow

## Overview

这是一个“半自动化公众号长文生产”skill。

核心原则：

- 不追求一键全自动
- 每个关键阶段都必须允许用户确认
- 默认一次性输出 4 套 Wechat 排版供手动选择
- 编排子 skill 时，必须完整遵循子 skill 的原始流程，不能为了提速跳过确认、分析或中间产物
- 必须先选择密度阈值（`200/300/400/500` 或自定义），再生成 `02-规划/视觉中断清单.md`
- 每篇文章的图片资产必须单独存放在“以文章标题命名”的文件夹中，不能混放

当前这一版已经封装好的最小稳定闭环是：

- 输入 1 篇 Markdown 正文
- 自动创建文章同名目录
- 输出 4 套预览 HTML
- 输出 4 套发布态 HTML

仓库内主脚本：

- `skills/wechat-article-workflow/scripts/workflow_bundle.py`
- `skills/wechat-article-workflow/scripts/install_local_skill.py`
- `skills/wechat-article-workflow/scripts/ensure_dependencies.py`
- `skills/wechat-article-workflow/scripts/workflow_state_manager.py`
- `skills/wechat-article-workflow/scripts/workflow_stage_runner.py`
- `skills/wechat-article-workflow/scripts/workflow_executor.py`
- `skills/wechat-article-workflow/scripts/workflow_validator.py`

## When to Use

适用于这些场景：

- 用户已经有一篇草稿，想继续做成公众号文章
- 用户需要先润色，再决定插图，再决定排版
- 用户希望保留人工终审，而不是完全自动发布

不适用于：

- 只想单次生成一篇短文
- 只想做图片，不做正文
- 只想发稿，不需要完整文章工作流

## Fixed Output Themes

默认输出以下 4 套 Wechat HTML：

- Claude
- 纽约时报
- 深度阅读
- Medium

不在运行时继续收敛成单一模板。

## Mandatory Gate Protocol

这是主 skill 的硬协议，不是建议：

1. 初始化工作区后，先运行一次 `workflow_executor.py status`，只处理当前 `stage_id`。
2. 当前阶段结果展示给用户，得到明确同意后，必须先运行 `workflow_executor.py record-approval` 写入人工确认回执。
3. 当前阶段产物写完后，必须再次运行 `status`，不能凭记忆直接切到下一个子 skill。
4. 只有当 `validation.status` 等于 `ok` 时，才允许运行 `workflow_executor.py confirm`。
5. 如果 `validation.status` 等于 `blocked`，必须先修复 `02-规划/阶段检查报告.md` 里的 blocker，再重新运行 `status`。
6. 不允许把“已经写在 SKILL.md 里的规则”当作“已经被执行过的规则”。

换句话说：

- `SKILL.md` 负责告诉 AI 应该怎么做
- `workflow_executor.py status` 和 `workflow_validator.py` 负责验证有没有真的做到
- `workflow_executor.py record-approval` 负责把用户确认落成正式回执
- 没有经过 `展示结果 -> 用户同意 -> record-approval -> status -> confirm` 的阶段，不算完成

## Workflow

1. 读取输入正文或草稿
2. 检查依赖 skill 是否齐全，缺失时优先自动补装
3. 如果正文尚未润色，先走 `khazix-writer`
4. 如果 Markdown 尚未整理，先走 `baoyu-format-markdown`
5. 为当前文章创建独立图片资产目录，目录名默认等于文章标题
6. 先确认本篇正文配图密度（200/300/400/500 或自定义），再产出 `02-规划/视觉中断清单.md`
7. 再走 `lizi-article-illustrator` 输出配图规划、prompt 打包结果，并等待确认
8. 图片生成阶段优先调用已安装的生图 skill，正文图默认 `4:3`
9. 将图片插回正文，并检查 `300` 字内视觉中断规则
10. 导出 4 套预览 HTML
11. 导出 4 套对应主题的发布态 HTML
12. 等待用户手动选择最终排版
13. 对选中主题执行草稿箱发布前检查
14. 只有在用户再次确认后，才进入草稿箱投递

## Dependency Bootstrap

在运行主工作流前，先检查这些依赖是否存在：

- `khazix-writer`
- `baoyu-format-markdown`
- `baoyu-imagine`

本仓库内置一个本地配图规划 skill：

- `lizi-article-illustrator`（按我们的规则强制执行 300 字视觉中断下限与图数下限）

检查与自动补装脚本：

```powershell
py .\skills\wechat-article-workflow\scripts\ensure_dependencies.py
```

规则：

- 如果缺依赖，先补依赖，再继续工作流
- 如果自动补装失败，要明确告诉用户缺什么、来自哪个 repo、建议执行什么安装命令
- 依赖来源以 `references/dependencies.json` 为准
- 不允许在依赖缺失状态下假装继续完整工作流

## Minimal Stable Entry

当用户只是要先“跑通排版闭环”时，优先使用这个入口，而不是一口气调完整大工作流：

```powershell
py .\skills\wechat-article-workflow\scripts\workflow_bundle.py `
  "H:\3.写公众号素材\某篇文章.md" `
  --image-root "H:\3.写公众号素材\imgs" `
  --json
```

这条命令会：

- 读取 Markdown 标题
- 在 `--image-root` 下创建文章同名目录
- 把正文引用到的本地图片复制进文章目录
- 输出 4 套预览 HTML
- 输出 4 套发布态 HTML
- 自动生成工作流状态文件、规则摘要和发布检查清单
- 同时返回 `files.state_path`，便于后续执行器稳定读取中文路径

推荐后续执行方式：

```powershell
$result = py .\skills\wechat-article-workflow\scripts\workflow_bundle.py `
  "H:\3.写公众号素材\某篇文章.md" `
  --image-root "H:\3.写公众号素材\imgs" `
  --json | ConvertFrom-Json

py .\skills\wechat-article-workflow\scripts\workflow_executor.py `
  status `
  --state-path $result.files.state_path
```

说明：

- 不建议在 PowerShell 里用纯文本截取文章目录后，再手工拼接 `工作流状态.json`
- 中文路径场景下，优先使用 `--json` 结果里的 `files.state_path`
- `status` 会返回当前阶段校验结果，并写出 `02-规划/阶段检查报告.md`
- `status` 还会返回 `next_steps` 与 `suggested_commands`，并把这些内容写入 `02-规划/当前阶段说明.md`
- `status` 还会返回机器可读的 `gate` 字段，明确要求“产物写完后必须重新运行 status，只有 validation.status=ok 才能 confirm”
- 用户确认当前阶段结果后，必须先运行：

```powershell
py .\skills\wechat-article-workflow\scripts\workflow_executor.py `
  record-approval `
  --state-path $result.files.state_path `
  --note "这里写用户确认原话"
```

- `confirm` 默认不会跨过 blocker；只有显式传入 `--allow-issues` 时才允许带问题推进

本机安装 skill：

```powershell
py .\skills\wechat-article-workflow\scripts\install_local_skill.py
```

依赖检查与自动补装：

```powershell
py .\skills\wechat-article-workflow\scripts\ensure_dependencies.py
```

依赖来源清单：

- `skills/wechat-article-workflow/references/dependencies.json`

## Stage Outputs

完整工作流里的关键中间产物应尽量固定命名：

- `01-原稿/01-草稿.md`
- `01-原稿/02-润色稿.md`
- `01-原稿/03-整理稿.md`
- `01-原稿/04-配图稿.md`
- `02-规划/工作流状态.json`
- `02-规划/配图数量确认.txt`
- `02-规划/配图密度配置.json`
- `02-规划/视觉中断清单.md`
- `02-规划/视觉中断清单.json`
- `02-规划/配图执行记录.txt`（必须包含 `planner_skill: lizi-article-illustrator`）
- `02-规划/人工确认/`
- `02-规划/规则摘要.md`
- `02-规划/发布检查清单.md`
- `02-规划/outline.md`
- `02-规划/batch.json`
- `03-提示词/草稿/`
- `03-提示词/定稿/`
- `04-素材/正文配图/`
- `04-素材/封面配图/`
- `05-排版/预览版/`
- `05-排版/发布版/`
- `06-发布/已选主题.txt`

## Asset Directory Rule

图片相关资产统一按“单文章单目录”管理。

默认规则：

- 每篇文章在图片根目录下拥有一个独立文件夹
- 文件夹名称默认使用文章标题
- 正文图、封面图、`outline.md`、`batch.json`、`prompts/`、`prompts-draft/`、4 套 HTML 预览都放在该目录内
- HTML 预览如果从原型目录复制到文章目录，必须同步修正其中的图片、签名图等相对路径；更优先的是直接在目标目录生成

推荐结构：

```text
imgs/
└── 文章标题/
    ├── 01-原稿/
    │   ├── 01-草稿.md
    │   ├── 02-润色稿.md
    │   ├── 03-整理稿.md
    │   └── 04-配图稿.md
    ├── 02-规划/
    │   ├── 工作流状态.json
    │   ├── 配图数量确认.txt
    │   ├── 视觉中断清单.md
    │   ├── 人工确认/
    │   ├── 规则摘要.md
    │   ├── 发布检查清单.md
    │   ├── outline.md
    │   └── batch.json
    ├── 03-提示词/
    │   ├── 草稿/
    │   └── 定稿/
    ├── 04-素材/
    │   ├── 正文配图/
    │   └── 封面配图/
    ├── 05-排版/
    │   ├── 预览版/
    │   └── 发布版/
    └── 06-发布/
        └── 已选主题.txt
```

这样做的目的：

- 避免不同文章的同编号图片互相覆盖
- 避免 `prompts/01-...` 这类文件与旧文章混在一起
- 方便后续整篇文章一起迁移、归档、复用
- 方便 HTML 排版和草稿箱投递时按文章维度取资源
- 方便用户直接在文章目录内完成“看图、选版、继续投递”
- 避免 HTML 挪了位置以后，图片路径仍指向旧目录而导致“文字正常、图片失效”

## Sub-skill Orchestration Rule

这是本 workflow 的硬规则：

- 调用任何子 skill 时，**必须完整遵循该子 skill 的原始说明**
- 不允许为了提速而跳过子 skill 里的确认节点
- 不允许直接替用户做掉本应由子 skill 明确询问的选择题
- 不允许省略子 skill 要求保留的中间产物，例如分析稿、outline、prompt 文件、候选方案
- 如果用户之前已经表达过偏好，这些偏好只能作为“推荐输入”，不能替代当前轮应有的确认

简单说：

- `khazix-writer` 要先润色再确认，就必须先确认
- `baoyu-format-markdown` 要先分析再格式化，就必须保留分析与格式化阶段
- `lizi-article-illustrator` 要先跑视觉中断统计，再做语义规划，并在不足时补图位
- 如果正文某一段连续文字过长，即使主图数量已够，也要补充视觉中断，不能让读者长时间只面对大段文字

如果 workflow 为了编排效率与子 skill 原规则发生冲突，**以子 skill 的完整流程为准**。

## Required Human Checkpoints

以下节点必须允许用户确认：

1. 润色完成后
2. Markdown 整理完成后
3. 配图数量确认后
4. 配图规划完成后
5. 图片生成前
6. 图片插回正文后
7. 4 套排版产出后
8. 草稿箱投递前

## Reading Rhythm Rule

公众号长文不能只看“总共放了几张图”，还要看“阅读节奏是否被打断得足够自然”。

默认要求：

- 不能让正文出现过长的纯文字连续区段
- 一般每隔不超过 `300` 中文字，至少应该出现一种视觉中断
- 这条规则不是只在最后检查，而是在 `image_count_review` 与 `illustration_plan_review` 阶段就开始强制执行
- 如果整理稿里已经出现超长纯文字区段，但还没有 `02-规划/视觉中断清单.md`，阶段校验必须直接阻塞
- 视觉中断不一定都是真图片，也可以是表格、引用块、对比卡、流程图、信息图
- 如果某一节信息密度高、情绪重、读者容易疲劳，宁可多放一张图，也不要硬撑长文本

## Publish Safety Rule

进入公众号发稿阶段时，必须额外遵守这些规则：

- 不能直接把浏览器预览页 HTML 发给公众号 API
- 发布态 HTML 应尽量只保留正文内容本身
- 发布态 HTML 不应依赖 `<style>`、`<script>` 或复杂 class 选择器
- 图片、图注、表格、引用块、代码块都应尽量写成内联样式
- 原生 `ol/ul/li` 列表默认视为高风险结构，应优先转成微信更稳的手工编号或手工项目符号块
- 图片图注默认不要直接照搬完整 `alt`，应优先输出更短、更适合正文阅读的显示图注
- 图片圆角优先通过显示层容器裁切实现；点开大图仍是原始方图时，视为正常，不要求强行改原图文件
- 发稿前应检查是否残留高风险结构

重点检查位置：

- 数据和观点密集段
- 风险提醒段
- 方法论连续列点前后
- 从一个大章节切到下一个大章节之前

目标不是“平均分配图片”，而是“让读者读得下去”。

## Draft Gate

草稿箱投递必须经过单独保护层：

- 只能使用用户选中的那一套主题
- 只能使用对应的发布态 HTML
- 最终投递应优先调用我们自己的 `wechat-draft-publisher` skill，而不是复用宝玉默认发布 skill
- 投递前必须更新 `06-发布/已选主题.txt`
- 投递前必须核对 `02-规划/发布检查清单.md`
- 投递前必须再次询问用户是否真正进入草稿箱
- 如果用户只想“先准备好”，则停在 `prepare-only`，不要自动发稿

## Current Prototype Sources

- 项目说明：`wechat-article-workflow-project/README.md`
- 状态说明：`wechat-article-workflow-project/docs/PROJECT_STATUS.md`
- 验证清单：`wechat-article-workflow-project/docs/WORKFLOW_VALIDATION.md`
- 排版原型：`wechat-article-workflow-project/prototype/wechat-theme-previews/`

## Implementation Notes

当前已经完成：

- 最小稳定闭环脚本 `workflow_bundle.py`
- 本机安装脚本 `install_local_skill.py`
- 依赖检查脚本 `ensure_dependencies.py`
- 分层文章工作区目录结构
- 阶段推进状态机脚本 `workflow_state_manager.py`
- 当前阶段说明生成器 `workflow_stage_runner.py`
- 阶段执行器 `workflow_executor.py`
- 阶段校验器 `workflow_validator.py`
- 300 字视觉中断规则已前移到配图数量确认与配图规划阶段校验

当前仍未完成：

- 把润色、Markdown 结构化、配图规划、图片生成、草稿箱投递全部串成一个自动执行器
- 把子 skill 编排和确认点做成真正的可交互状态机

## Common Mistakes

- 直接跳过人工确认点
- 调用子 skill 时只用了结果，没有完整遵循它的过程
- 把“用户以前表达过的偏好”误当成“这一次已经确认”
- 把多篇文章的图片和 prompt 混放在同一个目录，导致编号冲突或串图
- 复制 HTML 到文章目录后，没有同步修正图片和签名图的相对路径
- 图总数看起来够了，但中间仍然留下大段连续纯文字，阅读节奏断不下来
- 只生成一种排版而不是四种
- 把封面工作流和正文工作流混在一起
- 没有保留 prompt 打包结果
