---
title: 为什么多 Agent 写代码需要 Git Worktree
description: 并行开发的第一步，是让每个 Agent 拥有独立的工作目录。
date: 2026-09-27
tags: [Agent, Engineering, Git]
sample: true
---

## 问题从共享目录开始

当两个 Agent 在同一个工作目录里修改文件时，它们看到的是同一份未提交的状态。即使任务分别属于后端和前端，也可能同时触碰依赖清单、公共类型或配置。

Git 分支记录提交历史，但一个工作目录在某一时刻只检出一份状态。仅仅为每个 Agent 建立分支，无法隔离正在发生的文件修改。

## Worktree 提供什么

Git Worktree 让同一个仓库拥有多个工作目录。每个目录可以检出不同分支，Agent 在各自目录里编辑、构建和测试。

```bash
git worktree add ../hive-agent-search -b agent/search
git worktree add ../hive-agent-review -b agent/review
```

它隔离工作目录、索引和检出的分支，共享底层 Git 对象。安装依赖时仍需要关注全局缓存、数据库和服务端口，这些不会自动隔离。

## 并行任务需要边界

在开始分工前，先约定输入、输出和共享接口。一个任务修改 API 类型，另一个任务依赖这个类型时，应该先稳定接口，再展开并行实现。

1. 每个任务指定负责人、分支和目录。
2. 在任务目录里运行检查。
3. 提交完成后检查差异，再逐个合并。
4. 对合并后的结果执行集成验证。

## 合并仍然需要判断

Worktree 能减少互相覆盖，但无法消除设计冲突。两个实现可能分别通过测试，合起来却对同一业务规则有不同理解。主分支的集成检查与人工审阅仍然重要。

## 参考

- [Git Worktree 官方文档](https://git-scm.com/docs/git-worktree)
