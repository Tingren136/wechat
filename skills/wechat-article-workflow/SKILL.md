---
name: wechat-article-workflow
description: Use when producing a long-form WeChat Official Account article from a draft and wanting staged polishing, illustration planning, image generation, and four selectable WeChat HTML layouts with human confirmation at each key stage.
---

# WeChat Article Workflow

## Overview

这是一个“半自动化公众号长文生产”skill 骨架。

核心原则：

- 不追求一键全自动
- 每个关键阶段都必须允许用户确认
- 默认一次性输出 4 套 Wechat 排版供手动选择

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
2. 使用 `khazix-writer` 润色正文
3. 使用 `baoyu-format-markdown` 统一 Markdown 结构
4. 使用 `baoyu-article-illustrator` 分析插图位置
5. 输出正文配图建议与 prompt 打包结果
6. 等待用户确认是否生成图片
7. 生成正文图片，默认 `4:3` 横版
8. 将图片插回正文
9. 输出 4 套 Wechat HTML
10. 等待用户手动选择最终排版
11. 再决定是否进入草稿箱投递

## Required Human Checkpoints

以下节点必须允许用户确认：

1. 润色完成后
2. 配图规划完成后
3. 图片生成前
4. 4 套排版产出后
5. 草稿箱投递前

## Current Prototype Sources

- 项目说明：`wechat-article-workflow-project/README.md`
- 状态说明：`wechat-article-workflow-project/docs/PROJECT_STATUS.md`
- 验证清单：`wechat-article-workflow-project/docs/WORKFLOW_VALIDATION.md`
- 排版原型：`wechat-article-workflow-project/prototype/wechat-theme-previews/`

## Implementation Notes

当前还只是第一版 skill 骨架，尚未完成真正安装态封装。

后续正式实现时要补齐：

- 输入参数约定
- 目录结构约定
- 中间产物命名约定
- 错误处理与阶段回滚规则

## Common Mistakes

- 直接跳过人工确认点
- 只生成一种排版而不是四种
- 把封面工作流和正文工作流混在一起
- 没有保留 prompt 打包结果
