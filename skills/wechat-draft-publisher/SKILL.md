---
name: wechat-draft-publisher
description: Use when a WeChat article has already been prepared as publish-safe HTML and the user wants to validate it, confirm the selected theme, and send it into the WeChat Official Account draft box.
---

# WeChat Draft Publisher

## Overview

这是一个只负责“公众号草稿箱最后一跳”的 skill。

它不负责：

- 正文润色
- Markdown 整理
- 配图规划
- 生图
- 四套排版对比

它只负责：

- 接收已经确认好的发布态 HTML
- 检查是否满足草稿箱投递前规则
- 再次停下来等待人工确认
- 在确认后再进入公众号草稿箱

## When to Use

适用于这些场景：

- 已经有选定主题的发布态 HTML
- 已经完成排版选择
- 只差最后进入公众号草稿箱

不适用于：

- 还在正文润色阶段
- 还在配图阶段
- 还没选定最终主题

## Required Inputs

在进入这个 skill 之前，应至少具备：

- 文章标题目录
- `02-规划/发布检查清单.md`
- `06-发布/已选主题.txt`
- `05-排版/发布版/` 下对应主题的发布态 HTML

## Publish Gate

草稿箱发布前必须检查：

- 当前输入文件是发布态 HTML，不是预览 HTML
- 没有 `<style>`、`<script>`、复杂 class
- 没有原生 `ol/ul/li`
- 图注为短版图注
- 没有签名图
- 没有额外单独作者行
- 图片路径仍然指向当前文章目录
- 用户已经明确确认“进入草稿箱”

## Human Confirmation

真正投递前必须再次确认：

1. 文章标题
2. 当前选定主题
3. 当前发布态 HTML 路径
4. 是否真的进入公众号草稿箱

## Current Scope

当前这版先把职责边界和检查规则固定下来。

后续可以继续补：

- 真实草稿箱 API / 自动化调用脚本
- 发布结果回写
- 草稿箱 `media_id` 归档
