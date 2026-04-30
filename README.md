# WeChat Article Workflow

一个可以复用、可以分享的“公众号长文生产主 skill”仓库。

它的目标不是“一键全自动发文”，而是把已经跑通的公众号文章工作流，整理成一个别人可以安装、调用、继续协作的大 skill。

## 它能做什么

安装后，主 skill `wechat-article-workflow` 可以围绕一篇文章，按阶段组织这些步骤：

1. 润色正文
2. 整理 Markdown
3. 确认配图数量
4. 先补视觉中断清单，再生成配图规划与 prompt
5. 生成正文图片
6. 把图片插回正文
7. 输出 4 套公众号排版
8. 进入发布前检查

这个 workflow 已经固定了这些规则：

- 关键阶段必须停下来让人确认
- 正文固定输出 4 套主题：`Claude`、`纽约时报`、`深度阅读`、`Medium`
- 正文图片默认 `4:3`
- 连续纯文字区段不应超过约 `300` 中文字
- 如果整理稿里出现超过 `300` 字的长纯文字区段，必须先产出 `02-规划/视觉中断清单.md`
- 每篇文章的素材、Markdown、HTML 必须放在“文章标题同名目录”里
- 发布公众号时必须使用“发布态 HTML”，不能直接拿预览页发稿

## 适合谁

适合这些人：

- 已经有一篇公众号草稿，想按固定流程继续打磨
- 想把“润色、配图、排版、发布准备”统一收进一个主 skill
- 希望保留人工确认，而不是完全黑箱自动发文

不适合这些场景：

- 只想单独生图
- 只想单独排版
- 只想做封面
- 希望完全不确认、一步自动发出去

## 仓库里最重要的东西

- 主 skill：`skills/wechat-article-workflow`
- 发布 skill：`skills/wechat-draft-publisher`
- 安装脚本：`skills/wechat-article-workflow/scripts/install_local_skill.py`
- 依赖检查脚本：`skills/wechat-article-workflow/scripts/ensure_dependencies.py`
- 工作流打包脚本：`skills/wechat-article-workflow/scripts/workflow_bundle.py`
- 工作流执行器：`skills/wechat-article-workflow/scripts/workflow_executor.py`

## 依赖的外部 skill

这个主 skill 不会把所有能力都硬写死，它会依赖一些现成 skill。

当前默认依赖：

- `khazix-writer`
- `baoyu-format-markdown`
- `baoyu-article-illustrator`
- `baoyu-imagine`

来源仓库：

- `https://github.com/KKKKhazix/khazix-skills`
- `https://github.com/JimLiu/baoyu-skills`

依赖清单文件：

- `skills/wechat-article-workflow/references/dependencies.json`

## 怎么安装

### 1. 克隆这个仓库

```powershell
git clone https://github.com/Tingren136/wechat.git
cd wechat
```

### 2. 安装主 skill 到本机 skills 目录

```powershell
py .\skills\wechat-article-workflow\scripts\install_local_skill.py
```

这个脚本会做两件事：

- 安装主 skill `wechat-article-workflow`
- 一起安装 `wechat-draft-publisher`

默认安装位置：

- `C:\Users\你的用户名\.codex\skills\wechat-article-workflow`
- `C:\Users\你的用户名\.codex\skills\wechat-draft-publisher`

### 3. 检查并补装依赖 skill

```powershell
py .\skills\wechat-article-workflow\scripts\ensure_dependencies.py
```

如果缺少依赖，它会尽量自动补装；如果补装失败，也会告诉你缺哪个 skill、来自哪个仓库。

## 怎么调用

最简单的入口不是一口气自动跑完整流程，而是先初始化一篇文章的工作区。

### 第一步：初始化文章工作区

```powershell
py .\skills\wechat-article-workflow\scripts\workflow_bundle.py `
  "H:\3.写公众号素材\某篇文章.md" `
  --image-root "H:\3.写公众号素材\imgs" `
  --json
```

这一步会：

- 读取文章标题
- 创建文章同名目录
- 复制正文引用到的本地图片
- 生成 4 套预览 HTML
- 生成 4 套发布态 HTML
- 生成状态文件、规则摘要、检查清单

进入后续阶段后，工作流还会继续要求这些关键中间产物：

- `02-规划/配图数量确认.txt`
- `02-规划/视觉中断清单.md`
- `02-规划/outline.md`
- `02-规划/batch.json`
- `03-提示词/草稿/`

### 第二步：查看当前阶段

```powershell
$result = py .\skills\wechat-article-workflow\scripts\workflow_bundle.py `
  "H:\3.写公众号素材\某篇文章.md" `
  --image-root "H:\3.写公众号素材\imgs" `
  --json | ConvertFrom-Json

py .\skills\wechat-article-workflow\scripts\workflow_executor.py `
  status `
  --state-path $result.files.state_path
```

`status` 会输出：

- 当前阶段
- 当前阶段校验结果
- `next_steps`
- `suggested_commands`

同时还会在文章目录里写出：

- `02-规划/当前阶段说明.md`
- `02-规划/阶段检查报告.md`

其中从“配图数量确认”阶段开始，如果 `01-原稿/03-整理稿.md` 里存在超过 `300` 字的连续纯文字区段，`status` 会直接拦住，要求先补 `02-规划/视觉中断清单.md`，而不是拖到最后插图阶段才发现。

### 第三步：确认并推进下一阶段

```powershell
py .\skills\wechat-article-workflow\scripts\workflow_executor.py `
  confirm `
  --state-path "你的工作流状态.json路径"
```

默认规则：

- 如果当前阶段还有 blocker，就不会推进
- 如果你确实要强行推进，才显式使用：

```powershell
py .\skills\wechat-article-workflow\scripts\workflow_executor.py `
  confirm `
  --state-path "你的工作流状态.json路径" `
  --allow-issues
```

### 第四步：刷新排版

如果你已经完成配图稿，希望重新导出 4 套排版：

```powershell
py .\skills\wechat-article-workflow\scripts\workflow_executor.py `
  refresh-layouts `
  --state-path "你的工作流状态.json路径"
```

### 第五步：设置最终主题

```powershell
py .\skills\wechat-article-workflow\scripts\workflow_executor.py `
  set-theme `
  --state-path "你的工作流状态.json路径" `
  --theme "Claude"
```

## 调用后的目录长什么样

每篇文章都会整理成一个中文目录结构：

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
    │   ├── 当前阶段说明.md
    │   ├── 阶段检查报告.md
    │   ├── 配图数量确认.txt
    │   ├── 视觉中断清单.md
    │   ├── 规则摘要.md
    │   ├── outline.md
    │   ├── batch.json
    │   └── 发布检查清单.md
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

## 外部使用时要知道的边界

这个仓库已经能作为“主 skill 仓库”分享出去，但它不是完全无依赖的一键魔法按钮。

别人从 GitHub 下载后，想成功调用它，通常还需要：

- 本地已经能使用 Codex / Claude Code 的 skill 目录
- 已安装依赖 skill
- 有自己的图片生成环境
- 如果要进公众号草稿箱，还要有自己的发布环境或账号配置

所以它现在的定位是：

- `可以分享`
- `可以安装`
- `可以调用`
- `可以跑通完整阶段化流程`
- `但不是零配置、零依赖、零确认的一键全自动发稿器`

## 现在已经跑通了哪些关键能力

- 主 skill 本机可安装
- 依赖可检查、可补装
- 文章工作区可自动初始化
- 300 字视觉中断规则已经前移到配图规划阶段校验
- 4 套主题排版可导出
- 发布态 HTML 已跑通
- 关键阶段有状态机
- 阶段有校验器
- 阶段有下一步动作建议
- 发布前有单独 skill 边界

## 建议别人怎么理解这个仓库

最简单的理解方式就是：

> 这是一个“公众号长文生产主 skill 仓库”，不是单一功能脚本仓库。

它最重要的价值不是某一个命令，而是把已经验证过的写作工作流收束成了一个统一入口。

## 补充文档

如果你想继续看内部设计和项目状态，可以读：

- `docs/PROJECT_STATUS.md`
- `docs/AI_HANDOFF.md`
- `docs/ROADMAP.md`
- `skills/wechat-article-workflow/SKILL.md`
