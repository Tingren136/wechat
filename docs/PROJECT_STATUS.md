# Project Status

## 当前状态

项目处于“说明书、预览原型、Claude 发布态导出器已建立，等待正式封装”阶段。

## 已完成

- 明确了公众号文章协作工作流
- 跑通了微信公众号草稿箱发稿链路
- 建立了测试文章与测试图片素材
- 做出了 4 套 Wechat HTML 正文排版主题
- 确认未来默认提供 4 套排版，用户手动选择
- 仓库内的排版原型已经能基于本仓库素材自洽重跑
- 修复了 `baoyu-format-markdown` 在 Windows 下“脚本看似执行成功、实际未进入 CLI 主逻辑”的问题
- 为 `baoyu-format-markdown` 增加了 Windows 稳定入口：`scripts/run-formatter.ps1`
- 已经补出 `Claude` 主题的微信发布态导出器：`scripts/claude_publish_export.py`
- 已经为发布态导出器补回归测试：`tests/test_claude_publish_export.py`
- 已确认“预览页 HTML 不等于可发稿 HTML”
- 已确认微信会把原生 `ol/li` 列表渲染坏，发布态必须改成手工编号块
- 已用真实文章重新上传公众号草稿箱验证新的发布态链路

## 已废弃方向

- 不再继续使用宝玉官方主题作为主对比方案
- 不再尝试只保留单一正文模板

## 当前保留方案

- `Claude`
- `纽约时报`
- `深度阅读`
- `Medium`

## 关键产物

- 预览入口：
  `D:\cc project\新建文件夹 (2)\wechat-theme-previews\index.html`
- 预览脚本：
  `D:\cc project\新建文件夹 (2)\wechat-theme-previews\generate-previews.mjs`
- 测试正文：
  `H:\3.写公众号素材\别再让 AI 直接写正文了_卡兹克版.wechat.md`
- 测试配图：
  `H:\3.写公众号素材\imgs`
- 发布态导出器：
  `D:\cc project\新建文件夹 (2)\wechat-article-workflow-project\scripts\claude_publish_export.py`
- 发布态测试：
  `D:\cc project\新建文件夹 (2)\wechat-article-workflow-project\tests\test_claude_publish_export.py`

## 风险点

- 当前仍然依赖本地绝对路径
- 还没有统一输入输出契约
- 还没有把“人工确认点”正式编码进 skill 行为
- 还没有做成可直接共享给他人的仓库结构
- `baoyu-format-markdown` 仍依赖外部 `autocorrect-node`，后续最好补成本地锁定依赖或统一 runner
- 目前只有 `Claude` 主题真正完成了发布态导出，其他 3 套仍停留在预览态

## 最近一次关键排查

- 根因不是文章内容错误，而是 `C:\\Users\\86156\\.codex\\skills\\baoyu-format-markdown\\scripts\\main.ts` 使用了不兼容 Windows 的入口判断：
  `import.meta.url === file://${process.argv[1]}`
- 这会导致脚本被加载后直接退出，表面上命令成功，实际上没有执行格式化逻辑
- 已修复为基于 `fileURLToPath(import.meta.url)` 与 `resolve(process.argv[1])` 的稳定比较
- 已验证：
  - `tsx main.ts <file>`
  - `powershell -File run-formatter.ps1 <file>`
  两种方式都能真实改写输出文件

## 最近一次真实发稿排查

- 之前“API 发稿成功但排版没保住”，根因不是 API 失效，而是我们把“浏览器预览页”当成了“发布态 HTML”
- 预览页会依赖外层壳、脚本或 `<style>`，微信草稿箱不会按预期保留
- 已新增 `scripts/claude_publish_export.py`，直接从 Markdown 生成微信兼容的 `Claude` 发布态 HTML
- 首轮发稿后又发现：微信会把原生 `ol/li` 列表渲染成错位编号
- 已把发布态列表统一改为“手工编号块”，并加测试锁定，后续不应再回到这个坑

## 当前最合理的下一步

1. 继续验证完整工作流分阶段输出
2. 为另外 3 套主题补发布态导出
3. 再逐步封装为通用 skill
