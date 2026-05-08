---
name: lizi-article-illustrator
description: 栗子智培公众号专用配图规划 skill。基于文章结构与语义规划图位，并强制执行每300字视觉中断规则，不提供“低密度”回退。
---

# Lizi Article Illustrator

## 目标

- 先保证阅读节奏：连续纯文字区段不超过 300 字
- 再保证语义匹配：图位与段落观点、情绪、信息密度匹配
- 最终保证数量下限：规划图数必须 >= `视觉中断清单.json.required_body_images`

## 输入

- `01-原稿/03-整理稿.md`
- `02-规划/视觉中断清单.md`
- `02-规划/视觉中断清单.json`
- `02-规划/配图数量确认.txt`

## 输出

- `02-规划/outline.md`
- `02-规划/batch.json`
- `03-提示词/草稿/`
- `02-规划/配图执行记录.txt`

## 固定规则

1. 禁止把配图密度降到低于视觉中断下限。
2. 禁止“先确认高图数，后续再降到 4-5 张”。
3. `batch.json` 中可计数任务数必须 >= `required_body_images`。
4. `配图执行记录.txt` 必须写入：`planner_skill: lizi-article-illustrator`。

## 执行步骤

1. 读取 `视觉中断清单.json`，拿到 `required_body_images`。
2. 结合 `03-整理稿.md` 做语义图位规划（问题段、转折段、密集信息段优先）。
3. 生成 `outline.md` 与 `batch.json`。
4. 如果 `batch.json` 图数不足，自动补图位，直到达到下限。
5. 写入 `配图执行记录.txt` 标记 skill 身份。

## 备注

该 skill 是主工作流的唯一配图规划入口，不能被其他“密度选择”流程替代。
