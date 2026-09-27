---
title: 一个技术博客，为什么选择静态生成
description: 内容写在 Markdown 里，把维护成本留给值得解决的问题。
date: 2026-09-20
tags: [Engineering, Architecture]
sample: true
---

## 内容优先

文章、短记与项目介绍的访问方式相近：读者打开链接，阅读已经写好的内容。这类需求适合在构建阶段生成 HTML。

## 写作与页面分开

Markdown 文件负责内容，模板负责排版。标题、日期、标签等字段通过 schema 校验，缺少必要字段时构建失败，避免错误内容悄悄上线。

## 搜索也可以是静态的

Pagefind 在 HTML 生成后建立搜索索引，浏览器按需加载数据。它不需要运行一个搜索服务器，但内容更新后需要重新构建索引。

## 什么时候需要后端

账户、私密内容或实时协作可能需要服务端。等具体需求出现后再评估，会让前期的博客更容易维护。

## 参考

- [Astro 内容集合](https://docs.astro.build/en/guides/content-collections/)
- [Pagefind 使用说明](https://pagefind.app/docs/)
