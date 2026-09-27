# 左二博客

Astro + TypeScript + Markdown + Pagefind 静态个人站。文章、项目、短记、周读、标签筛选、全文搜索、文章目录、RSS、Sitemap 和 SEO 已包含。

```bash
npm install
npm run dev
npm run check
npm run build
npm test
npm run preview
```

全文搜索需要构建后的 Pagefind 索引，请在 preview 中体验。

## 中英文界面

默认中文，英文界面位于 `/en/`。页首 `中文 / EN` 切换到对应页面，并保留查询参数和锚点。文章正文、标题与摘要保留原文，英文界面标注中文内容；搜索只索引中文正文一次，英文搜索结果链接仍保持英文界面。

英文路由复用原有页面，界面文案由 `src/middleware.ts` 在静态构建时转换。新增文案应补充翻译表；作者内容使用 `lang="zh-CN"` 或正文容器保护，不翻译 URL、ID 和锚点。改动后运行完整构建与测试，检查语言切换及目录链接。

## 写作

在 src/content/articles、notes、weekly、projects 下添加 Markdown 文件。文件名是 URL 路径。

```yaml
title: 文章标题
description: 简洁摘要
date: 2026-09-27
tags: [Agent, Engineering]
draft: true
sample: false
```

draft 和未来日期内容不会公开。文章、笔记与周读由作者持续整理。Agent 流程定义在 agents/，最终由作者审核。

## 部署

Cloudflare Pages 或 Vercel 的项目根目录设置为 zuoer-blog，构建命令 npm run build，输出目录 dist。配置 SITE_URL 为实际域名后重新构建，RSS、canonical、Sitemap 会使用该域名。默认 example.com 仅供本地搭建，不应直接上线。

GitHub Actions 在 PR 和推送时执行检查，不自动合并或发布。托管平台的 Git 集成可在人工合并后发布。

## Termux 局域网部署

网页端口为 `8080`。在本机部署时，将 `SITE_URL` 设置为你自己的站点地址后构建。
静态文件放在远程 `/data/data/com.termux/files/home/zuoer-blog/releases/` 的版本目录中，`current` 指向当前版本。`serve.py` 和 `start.sh` 来自本项目 deploy 目录。

服务通过 Python 运行，关闭 SSH 连接后仍可继续访问；这用于可信局域网，未配置公网 HTTPS 或 Android 重启自启动。Android 可能停止后台 Termux 进程，需保持 Termux 可运行。

在远程终端查看状态：

```bash
cat ~/zuoer-blog/server.pid
tail -n 30 ~/zuoer-blog/server.log
curl -I http://127.0.0.1:8080/
```

进程已退出时，执行 `bash ~/zuoer-blog/start.sh` 恢复。更新静态内容时上传到新版本目录，再切换 current 符号链接。重新启动服务后切换才生效，因为服务启动时解析了 current 的实际目录。旧版本保留以便回滚。

## 评论配置

评论组件已支持 Giscus，默认关闭。要启用它，先在公开 GitHub 仓库开启 Discussions 并安装 Giscus App，再从 giscus.app 获取仓库与分类 ID。将四项 `PUBLIC_GISCUS_*` 环境变量设在本机未跟踪的 `.env` 文件或托管平台构建环境中，然后重新构建；不要把真实配置文件或凭据提交到仓库。读者点击「加载 GitHub 评论」后才会连接第三方服务。

## 字体与隐私

标题与正文使用霞鹜文楷屏幕阅读版（LXGW WenKai Screen），采用 SIL Open Font License 1.1，支持免费商用与随网站分发。字体许可随构建发布在 /fonts/OFL.txt，网页字体包的 MIT 许可在 /fonts/webfont-MIT.txt。字体通过 npm 安装，由 Astro 构建为同源 WOFF2 分片，浏览器按页面字符加载，不连接第三方字体服务。离线回退使用系统楷体。
