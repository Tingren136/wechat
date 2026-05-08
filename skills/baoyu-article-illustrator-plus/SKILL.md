---
name: baoyu-article-illustrator-plus
description: 在保留 baoyu-article-illustrator 语义配图能力的基础上，强制执行“连续纯文字区段不超过300字”的正文配图下限规则，适用于公众号长文配图规划阶段。
---

# Baoyu Article Illustrator Plus

## 定位

这是一个“包装增强 skill”，不替代 `baoyu-article-illustrator`，而是在它之前和之后补上硬规则，确保配图结果既语义合理，又满足阅读节奏约束。

核心目标：

- 保留宝玉对文章结构和语义的配图能力
- 强制满足视觉中断规则（默认每 300 字至少一次中断）
- 保证 `配图数量确认.txt` 不会低于机器统计下限

## 输入

- `01-原稿/03-整理稿.md`
- `02-规划/配图数量确认.txt`（可先为空，后续回填）
- `02-规划/视觉中断清单.md`
- `02-规划/视觉中断清单.json`

## 标准流程

1. 先运行视觉中断统计脚本，生成/刷新：
- `02-规划/视觉中断清单.md`
- `02-规划/视觉中断清单.json`

2. 读取 `视觉中断清单.json` 的 `required_body_images`，把它作为正文最少配图数量下限。

3. 调用 `baoyu-article-illustrator` 做语义配图规划，产出图位、outline、batch、prompt 草稿。

4. 合并约束：
- 如果语义规划图数 `< required_body_images`，必须补图位直到 `>= required_body_images`
- 优先把新增图位补在长段纯文字区段
- 保持章节语义连续，不做无意义“硬插图”

5. 回填并明确写入：
- `02-规划/配图数量确认.txt` 必须包含“正文配图 X 张”

## 强制规则

- 不允许跳过第 1 步直接做语义规划
- 不允许只满足数量而破坏语义连贯
- 不允许只满足语义而忽略 `required_body_images`
- 任何阶段推进前都要通过主 workflow 的 `status` 校验

## 说明

本 skill 默认与 `wechat-article-workflow` 联动使用，由主 workflow 负责最终校验和阶段推进。
