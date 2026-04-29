# WeChat Article Workflow Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把“公众号文章最小稳定闭环”封装成仓库内可分享的 skill，并同步安装到本机可直接调用的 skills 目录。

**Architecture:** 以现有 `scripts/claude_publish_export.py` 为发布态核心，新增一个 skill 自带的执行脚本，负责读取 Markdown、创建文章同名目录，并一次性产出 4 套预览 HTML 与 4 套发布态 HTML。仓库内 `skills/wechat-article-workflow/` 保存完整 skill 包，再同步复制到本机 `C:\Users\86156\.codex\skills\wechat-article-workflow`。

**Tech Stack:** Python、unittest、现有 Markdown/BeautifulSoup 导出器、Codex skill 目录结构

---

### Task 1: 定义 skill 入口行为测试

**Files:**
- Create: `D:\cc project\新建文件夹 (2)\wechat-article-workflow-project\tests\test_wechat_article_workflow_bundle.py`
- Test: `D:\cc project\新建文件夹 (2)\wechat-article-workflow-project\tests\test_wechat_article_workflow_bundle.py`

- [ ] **Step 1: 写失败测试**
- [ ] **Step 2: 运行测试并确认失败**
- [ ] **Step 3: 定义最小入口行为**

覆盖点：
- 输入一篇 Markdown 和图片根目录
- 自动创建文章同名目录
- 输出 4 套预览 HTML
- 输出 4 套发布态 HTML
- 返回可预测的主题文件映射

### Task 2: 实现 skill 自带执行脚本

**Files:**
- Create: `D:\cc project\新建文件夹 (2)\wechat-article-workflow-project\skills\wechat-article-workflow\scripts\workflow_bundle.py`
- Modify: `D:\cc project\新建文件夹 (2)\wechat-article-workflow-project\scripts\claude_publish_export.py`

- [ ] **Step 1: 复用现有主题定义和发布态导出器**
- [ ] **Step 2: 增加预览 HTML 导出能力**
- [ ] **Step 3: 增加“一次性导出 4 套主题”的 bundle 入口**
- [ ] **Step 4: 增加 CLI，支持 Markdown 路径和图片根目录参数**

### Task 3: 完善 skill 包元数据与说明

**Files:**
- Modify: `D:\cc project\新建文件夹 (2)\wechat-article-workflow-project\skills\wechat-article-workflow\SKILL.md`
- Create: `D:\cc project\新建文件夹 (2)\wechat-article-workflow-project\skills\wechat-article-workflow\agents\openai.yaml`

- [ ] **Step 1: 把 SKILL.md 改成安装态说明**
- [ ] **Step 2: 写清楚最小稳定闭环入口命令**
- [ ] **Step 3: 补 agents/openai.yaml**

### Task 4: 本机安装与同步

**Files:**
- Create/Sync: `C:\Users\86156\.codex\skills\wechat-article-workflow\...`

- [ ] **Step 1: 复制仓库 skill 包到本机 skills 目录**
- [ ] **Step 2: 确认目录结构完整**
- [ ] **Step 3: 记录本机安装结果到仓库文档（如有必要）**

### Task 5: 验证、提交、推送

**Files:**
- Test: `D:\cc project\新建文件夹 (2)\wechat-article-workflow-project\tests\test_claude_publish_export.py`
- Test: `D:\cc project\新建文件夹 (2)\wechat-article-workflow-project\tests\test_wechat_article_workflow_bundle.py`

- [ ] **Step 1: 跑新增测试**
- [ ] **Step 2: 跑现有发布态回归测试**
- [ ] **Step 3: 用临时样例跑一次 skill CLI**
- [ ] **Step 4: 提交并推送**
