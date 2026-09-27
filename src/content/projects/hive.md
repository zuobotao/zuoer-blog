---
title: 虫巢 Hive
description: 多 Agent 协作开发的实验场。
date: 2026-09-27
tags: [Agent, Projects]
status: 构想阶段
sample: false
---

## 项目方向

HiveNest（虫巢）是我用来探索 Agent Runtime 的一个长期项目。它关注的不是把几个 Agent 连接起来，而是让不同能力、不同成本的 Agent，在一个可靠、可观察、可恢复的运行时里协作，把真实需求变成经过验证的交付物。

## 初心

我做 HiveNest 的起点，是对“模型会写代码”这件事还不满足。一个模型可以给出很好的回答，但真实的软件工程还包括任务拆分、工具调用、状态管理、失败重试、成本控制、测试和人工复核。真正困难的部分，往往不在某一次生成，而在怎样把这些步骤稳定地串起来。

所以我想把注意力从 Prompt 往下移一点，做一个能承载工程过程的 Runtime。代码只是结果，运行过程中的判断、边界和失败同样值得被记录。

## 产品设计

HiveNest 的基本流程是“需求 → 规划 → 执行 → 工具 → 评估 → 交付”。用户提交一个需求后，Brain 负责理解问题并生成任务图，Queen 按领域协调任务，Worker 执行具体工作，Tool 和 MCP 提供真实环境中的操作能力，Judge 则检查结果是否真的满足要求。

这个设计里有三个取舍。第一，不把所有任务都交给 LLM，能用确定性工具完成的事情就不调用模型。第二，不让 Agent 自己宣布成功，结果要经过 Judge 验证。第三，把成本、日志、检查点和重试放进产品本身，而不是留到出问题以后再补。

第一阶段会把软件工程任务作为主要场景，逐步走向从 Issue 到可审阅 Pull Request 的完整链路。人仍然在交付环节保留决定权，HiveNest 负责把中间过程变得更清楚、更可控。

## 项目架构

项目采用 Maven 多模块结构，按职责拆成七个模块：`hivenest-core` 保存需求、任务、任务图、Agent、Artifact 和执行追踪等领域模型；`hivenest-runtime` 负责调度、状态机、事件总线、检查点、重试和预算；`hivenest-agent` 实现 Brain、Queen 和 Worker；`hivenest-model` 负责模型提供商、注册表、路由和调用；`hivenest-tool` 统一 Git、Shell、文件系统、数据库、浏览器、搜索和 MCP 工具；`hivenest-evaluation` 负责 Judge 和结果评估；`hivenest-console` 提供 Web 控制台。

一次执行大致沿着这条路径展开：`Requirement → Brain → TaskGraph → Worker → Tool → Result → Judge → Artifact`。Runtime 处在中间，负责把每一步的状态、事件、预算和恢复策略串起来。这样模型可以替换，工具可以扩展，但任务执行的边界和可观察性不会跟着某一个模型绑定。

## 技术选型

后端使用 Java 17 和 Spring Boot 3.3.4，采用 Maven 多模块管理依赖和构建。领域模型、Runtime、Agent、模型、工具、评估和控制台彼此分离，既方便逐层测试，也为后续替换实现留下空间。

模型层坚持模型无关。`ModelProvider` 抽象具体提供商，`ModelRouter` 根据任务类型、能力、成本、延迟、上下文窗口、成功率和隐私要求选择模型；预算紧张时，可以从 Strong 逐级降级到 Medium、Cheap 或 Local。当前仓库先用 Mock Provider 验证 Runtime，OpenAI 兼容提供商和 Ollama 等本地模型属于后续接入方向。

工具层采用统一的 Tool 接口，把 Git、Shell、文件系统、数据库、浏览器、搜索和 MCP 接入同一套执行流程。控制台后端基于 Spring Boot Web，前端采用 Vue 3、TypeScript、Vue Router、Vue I18n 和 Vite。数据层预留 H2 与 PostgreSQL，当前重点仍是先把执行链路、追踪和评估跑通。

## 当前状态

项目已经完成基础工程初始化和七个模块的骨架实现，包含确定性 Worker、最小 Runtime、模型路由、工具注册和基础评估能力。下一步是补齐端到端集成测试，再接入真正的 LLM Worker，让 Brain 能从自然语言需求生成多任务图。

## 后续计划

接下来会沿着四条线继续推进：完善 Runtime 的恢复与观测；实现 LLM Worker 和结构化工具调用；让 Brain、Queen 能处理真实的软件开发任务；最后用 HiveNest 自己参与构建 HiveNest。这个项目还在早期，页面里的架构会随着实际运行结果继续修正。
