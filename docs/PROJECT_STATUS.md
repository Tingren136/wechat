# Project Status

## 当前状态

项目处于“说明书、预览原型、4 套发布态导出器已建立，等待正式封装”阶段。

## 已完成

- 明确了公众号文章协作工作流
- 跑通了微信公众号草稿箱发稿链路
- 建立了测试文章与测试图片素材
- 做出了 4 套 Wechat HTML 正文排版主题
- 确认未来默认提供 4 套排版，用户手动选择
- 仓库内的排版原型已经能基于本仓库素材自洽重跑
- 修复了 `baoyu-format-markdown` 在 Windows 下“脚本看似执行成功、实际未进入 CLI 主逻辑”的问题
- 为 `baoyu-format-markdown` 增加了 Windows 稳定入口：`scripts/run-formatter.ps1`
- 已经补出 4 套主题共用的微信发布态导出器：`scripts/claude_publish_export.py`
- 已经为发布态导出器补回归测试：`tests/test_claude_publish_export.py`
- 已确认“预览页 HTML 不等于可发稿 HTML”
- 已确认微信会把原生 `ol/li` 列表渲染坏，发布态必须改成手工编号块
- 已确认长图注不宜直接照搬 `alt`，发布态应使用短版显示图注
- 已确认正文图片圆角优先通过显示层容器裁切实现，不修改原图文件
- 已确认文章相关图片、prompt、HTML 资产应按“单文章单目录”管理
- 已确认公众号正文连续纯文字区段不应超过约 `300` 中文字
- 已用真实文章重新上传公众号草稿箱验证新的发布态链路
- 已封装 skill 最小稳定闭环脚本：`skills/wechat-article-workflow/scripts/workflow_bundle.py`
- 已封装本机安装脚本：`skills/wechat-article-workflow/scripts/install_local_skill.py`
- 已封装依赖检查脚本：`skills/wechat-article-workflow/scripts/ensure_dependencies.py`
- 已安装到本机 `C:\Users\86156\.codex\skills\wechat-article-workflow`
- 已把文章工作区升级为中文分层目录结构：`01-原稿 / 02-规划 / 03-提示词 / 04-素材 / 05-排版 / 06-发布`
- 已拆出独立草稿箱发布 skill：`skills/wechat-draft-publisher`

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
- 还没有把“300 字视觉中断检查”正式编码进脚本入口
- 还没有做成可直接共享给他人的仓库结构
- `baoyu-format-markdown` 仍依赖外部 `autocorrect-node`，后续最好补成本地锁定依赖或统一 runner
- 当前导出脚本文件名仍叫 `claude_publish_export.py`，但实际已支持 4 套主题，命名有误导性
- 当前最小稳定闭环只覆盖“Markdown -> 4 套预览 + 4 套发布态 HTML”，还没把润色、生图、发稿串成一个执行器
- 依赖自动补装目前以 repo 维度安装，后续仍可继续细化到更精确的 skill 级别
- 草稿箱发布 skill 目前已固定职责边界，但真实投递脚本仍可继续补强

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
- 随后又确认：长图注直接显示会太啰嗦，因此显示层图注已改为短版，原始 `alt` 保留给图片本身
- 同时确认：正文里更圆润的图片效果应该通过圆角容器裁切实现，点开大图仍保留原始方图是正常表现

## 当前最合理的下一步

1. 继续验证完整工作流分阶段输出
2. 先把规则补齐到 GitHub 文档闭环
3. 整理多主题发布态导出脚本与文档命名
4. 再逐步封装为通用 skill
