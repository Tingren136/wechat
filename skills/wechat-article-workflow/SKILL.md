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
- 每篇文章的图片资产必须单独存放在“以文章标题命名”的文件夹中，不能混放

当前这一版已经封装好的最小稳定闭环是：

- 输入 1 篇 Markdown 正文
- 自动创建文章同名目录
- 输出 4 套预览 HTML
- 输出 4 套发布态 HTML

仓库内主脚本：

- `skills/wechat-article-workflow/scripts/workflow_bundle.py`
- `skills/wechat-article-workflow/scripts/install_local_skill.py`

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

## Workflow

1. 读取输入正文或草稿
2. 如果正文尚未润色，先走 `khazix-writer`
3. 如果 Markdown 尚未整理，先走 `baoyu-format-markdown`
4. 为当前文章创建独立图片资产目录，目录名默认等于文章标题
5. 如果正文已具备插图，先导出 4 套预览 HTML
6. 同时导出 4 套对应主题的发布态 HTML
7. 等待用户手动选择最终排版
8. 后续再决定是否进入草稿箱投递

## Minimal Stable Entry

当用户只是要先“跑通排版闭环”时，优先使用这个入口，而不是一口气调完整大工作流：

```powershell
py .\skills\wechat-article-workflow\scripts\workflow_bundle.py `
  "H:\3.写公众号素材\某篇文章.md" `
  --image-root "H:\3.写公众号素材\imgs"
```

这条命令会：

- 读取 Markdown 标题
- 在 `--image-root` 下创建文章同名目录
- 把正文引用到的本地图片复制进文章目录
- 输出 4 套预览 HTML
- 输出 4 套发布态 HTML

本机安装 skill：

```powershell
py .\skills\wechat-article-workflow\scripts\install_local_skill.py
```

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
    ├── outline.md
    ├── batch.json
    ├── claude.html
    ├── claude-publish.html
    ├── nyt.html
    ├── deep-reading.html
    ├── medium.html
    ├── 01-xxx.png
    ├── 02-xxx.png
    ├── prompts/
    └── prompts-draft/
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
- `baoyu-article-illustrator` 要先确认配图数量、类型、风格或密度，就必须先问再继续
- 如果正文某一段连续文字过长，即使主图数量已够，也要补充视觉中断，不能让读者长时间只面对大段文字

如果 workflow 为了编排效率与子 skill 原规则发生冲突，**以子 skill 的完整流程为准**。

## Required Human Checkpoints

以下节点必须允许用户确认：

1. 润色完成后
2. 配图数量确认后
3. 配图规划完成后
4. 图片生成前
5. 4 套排版产出后
6. 草稿箱投递前

## Reading Rhythm Rule

公众号长文不能只看“总共放了几张图”，还要看“阅读节奏是否被打断得足够自然”。

默认要求：

- 不能让正文出现过长的纯文字连续区段
- 一般每隔不超过 `300` 中文字，至少应该出现一种视觉中断
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

## Current Prototype Sources

- 项目说明：`wechat-article-workflow-project/README.md`
- 状态说明：`wechat-article-workflow-project/docs/PROJECT_STATUS.md`
- 验证清单：`wechat-article-workflow-project/docs/WORKFLOW_VALIDATION.md`
- 排版原型：`wechat-article-workflow-project/prototype/wechat-theme-previews/`

## Implementation Notes

当前已经完成：

- 最小稳定闭环脚本 `workflow_bundle.py`
- 本机安装脚本 `install_local_skill.py`

当前仍未完成：

- 把润色、Markdown 结构化、配图规划、图片生成、草稿箱投递全部串成一个自动执行器
- 把“300 字视觉中断检查”正式编码进执行脚本
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
