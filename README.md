# WeChat Article Workflow Project

一个面向公众号长文生产的半自动化工作流项目说明。

目标不是“全自动一键发文”，而是把你现在已经跑通、并且确认有效的协作流程，整理成一个可复用、可分享、可继续开发的项目基础包。

## 项目目标

- 保留“人确认每一步”的工作方式
- 固化 4 套 Wechat 正文排版主题
- 让文章润色、配图规划、提示词打包、正文配图、HTML 排版尽量自动化
- 为后续封装成独立 skill 做准备

## 当前确认的工作流

1. 用户先获得一篇正文草稿
2. 使用 `khazix-writer` 做长文润色
3. 使用 `baoyu-format-markdown` 统一 Markdown 结构
4. 使用 `baoyu-article-illustrator` 分析正文插图位置，输出配图建议与提示词
5. 生成正文配图，正文图默认使用 `4:3` 横版
6. 将图片插回正文
7. 一次性输出 4 套 Wechat HTML 排版供手动选择
8. 后续再进入草稿箱发布阶段

## 当前新增的发布链路结论

这轮真实验证后，已经确认：

- “浏览器预览页 HTML” 不能直接作为公众号 API 发稿输入
- 真正可用的是“发布态 HTML”，也就是：
  - 不依赖 `<style>` 标签
  - 不依赖 `<script>`
  - 尽量不依赖 class
  - 结构尽量保守，适配微信草稿箱过滤与重排
- `Claude` 主题已经补出第一版发布态导出器：
  `scripts/claude_publish_export.py`
- 导出器已经配套测试：
  `tests/test_claude_publish_export.py`

## 当前固定的 4 套排版

- `Claude`
- `纽约时报`
- `深度阅读`
- `Medium`

策略已经确定：

- 不再继续收敛成单一模板
- 每篇文章默认同时产出这 4 套 HTML
- 用户手动选一套作为最终正式版

## 当前已完成的成果

### 1. 发稿链路已跑通

已经成功跑通过“发到微信公众号草稿箱”的真实链路。

补充说明：

- 已经不再直接拿预览页发稿
- 当前实际可用方案是：
  `Markdown -> Claude 发布态 HTML -> wechat-api.ts -> 公众号草稿箱`

### 2. 排版预览原型已完成

当前预览目录：

`D:\cc project\新建文件夹 (2)\wechat-theme-previews`

入口文件：

`D:\cc project\新建文件夹 (2)\wechat-theme-previews\index.html`

已生成内容：

- 4 套自定义 Wechat 主题预览
- 同一篇测试文章的统一对比页面
- 图注统一处理
- 表格样式对比

### 3. 文章与素材测试集已建立

测试正文：

`H:\3.写公众号素材\别再让 AI 直接写正文了_卡兹克版.wechat.md`

测试图片目录：

`H:\3.写公众号素材\imgs`

## 项目内关键文件

### 预览生成脚本

`prototype/wechat-theme-previews/generate-previews.mjs`

用途：

- 读取测试文章 Markdown
- 生成 4 套 Wechat HTML 预览
- 统一图片图注
- 统一表格展示
- 更新预览入口页

### Skill 骨架

`skills/wechat-article-workflow/SKILL.md`

用途：

- 定义未来通用 skill 的触发条件
- 固化阶段化输出与人工确认点
- 给后续 AI 一个明确的封装入口

### 项目说明文档

- `docs/PROJECT_STATUS.md`
- `docs/AI_HANDOFF.md`
- `docs/ROADMAP.md`

### 发布态导出器

`scripts/claude_publish_export.py`

用途：

- 将正文 Markdown 转成微信兼容的 `Claude` 发布态 HTML
- 自动把本地图片路径改写为文章目录内可用的相对路径
- 避免把预览页壳子、脚本、外部样式一起发进公众号

### 回归测试

`tests/test_claude_publish_export.py`

当前重点锁定：

- 不输出 `<style>` / `<script>`
- 图片保留图注
- 表格保留样式
- 原生 `ol/ul/li` 不进入发布态 HTML
- 列表统一转成微信更稳的手工编号块

## 当前边界

这个项目当前只把“项目说明 + 预览原型 + 工作流边界”整理清楚，还没有正式封装成独立 skill。

原因是：

- 真实链路虽然已跑通
- 但完整 skill 还需要把多阶段确认逻辑、输入约定、输出约定、错误处理统一起来
- 当前只把 `Claude` 主题的发布态导出真正打通，另外 3 套主题还没有补发布态版本

## 下一步建议

1. 把“输入正文 -> 输出 4 套 HTML”的流程封成一个稳定命令
2. 按同样思路补齐 `纽约时报 / 深度阅读 / Medium` 的发布态导出
3. 把“正文配图规划 + 提示词打包”补成独立中间产物
4. 再把整条链路封装成通用 skill
5. 最后单独处理“草稿箱投递”和“封面工作流”

## GitHub 发布建议

当前仓库已经建立并推送到 GitHub。

后续重点不再是“先上传”，而是继续做两件事：

1. 验证整条工作流的阶段输出是否稳定
2. 把现有原型逐步收敛成真正可复用的 skill
