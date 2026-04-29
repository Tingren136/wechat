# AI Handoff

这个文档用于让新的 AI 会话快速接手本项目。

## 这是什么

这是一个“公众号长文半自动化生产工作流”项目说明包。

核心目标：

- 保留人工确认
- 把多步骤协作尽量工具化
- 最终封装成一个可复用、可分享的 skill

## 已确认的核心规则

- 正文图片默认 `4:3` 横版
- 正文排版固定输出 4 套主题
- 用户手动选排版，不强制单模板
- 调用子 skill 时必须完整遵循原始流程，不能跳过分析、确认或中间产物
- 宝玉官方主题不再作为主方案
- 每篇文章的图片、prompt、HTML 资产都必须落在“文章同名目录”
- 正文连续纯文字区段不应超过约 `300` 中文字
- 微信发布态不要直接使用浏览器预览页 HTML
- 微信发布态不要保留原生 `ol/ul/li` 列表
- 微信发布态里的长图注不要直接照搬完整 `alt`
- 微信正文里的图片圆角优先通过显示层裁切实现，不直接改原图
- 固定结尾不再插入签名图，也不再追加单独作者行
- 当前最重要的是把项目说明与原型梳理好，方便后续 AI 接手

## 当前 4 套主题

- Claude
- 纽约时报
- 深度阅读
- Medium

## 必看文件

1. `README.md`
2. `docs/PROJECT_STATUS.md`
3. `docs/ROADMAP.md`
4. `prototype/wechat-theme-previews/generate-previews.mjs`
5. `scripts/claude_publish_export.py`
6. `tests/test_claude_publish_export.py`

## 当前真实素材

- 正文：
  `H:\3.写公众号素材\别再让 AI 直接写正文了_卡兹克版.wechat.md`
- 图片：
  `H:\3.写公众号素材\imgs`

## 新增重要上下文

- 当前真实验证文章也包括：
  `H:\3.写公众号素材\AI赋能日常：从工具到伙伴，解锁生活新可能_栗子版-formatted.md`
- 当前真实验证文章带图版：
  `H:\3.写公众号素材\AI赋能日常：从工具到伙伴，解锁生活新可能_栗子版-with-images.md`
- 当前文章目录：
  `H:\3.写公众号素材\imgs\AI赋能日常：从工具到伙伴，解锁生活新可能\`
- `khazix-writer` 已被本地修改为固定署名：
  `栗子智培`
- 固定结尾不再插入签名图，也不再追加单独作者行
- `baoyu-format-markdown` 已修复 Windows CLI 入口 bug，并增加稳定入口：
  `C:\Users\86156\.codex\skills\baoyu-format-markdown\scripts\run-formatter.ps1`
- 如果后续 AI 需要跑格式化，优先用：
  `powershell -File run-formatter.ps1 <markdown-file>`
- 当前 skill 已安装到本机：
  `C:\Users\86156\.codex\skills\wechat-article-workflow`
- 当前依赖清单在：
  `skills/wechat-article-workflow/references/dependencies.json`

## 当前已经验证过的重要技术结论

- 预览页 HTML 不能直接发公众号 API
- 4 套主题现在共用一个发布态导出器：
  `scripts/claude_publish_export.py`
- 这个导出器会：
  - 去掉预览页壳子
  - 输出微信兼容的内联样式 HTML
  - 把本地图片改成文章目录内可用的相对路径
  - 把原生有序列表改成微信更稳的手工编号块
  - 把长图注压缩成更短的显示图注，但保留原始 `alt`
  - 在正文显示层给图片加圆角容器裁切
- 当前 workflow 还要求：
  - 先确认本篇文章适合几张图，再继续图位分析
  - 插图插回正文后，要检查长段纯文字是否已被足够打断
  - 每篇文章默认应保留 4 套预览 HTML 和 4 套发布态 HTML
- 对应回归测试在：
  `tests/test_claude_publish_export.py`

## 最近一次真实发稿结果

- 文章：
  `AI赋能日常，从工具到伙伴，解锁生活新可能`
- 已至少完成一次“发布态 HTML -> 公众号草稿箱”的成功验证
- 最近一次修复后的草稿 `media_id`：
  `0_8_QNSfEWMT1RU1C3ZoLR_qMkArsijyKlVNxubNZHF7ZSf3GFH9BScQjckAkBCz`

## 当前最适合继续做的事

1. 先继续补齐 GitHub 文档闭环，避免规则只存在于会话记忆里
2. 再把“输入文章 -> 输出 4 套预览 + 4 套可发稿 HTML”定义成稳定接口
3. 给每个阶段补充输入、输出、确认点说明
4. 整理脚本命名，避免 `claude_publish_export.py` 这个历史名字误导
5. 再开始写正式 skill

## 暂时不要做的事

- 不要再花时间收敛单一排版模板
- 不要重新回到宝玉主题路线
- 不要跳过项目说明直接做复杂 skill 封装
