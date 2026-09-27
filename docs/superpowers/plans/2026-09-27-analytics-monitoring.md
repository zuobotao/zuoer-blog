# 博客统计与内网监控实施计划

**目标：** 在实际服务器上线访问统计、内网资源监控和游戏房间汇总。
**架构：** Python 标准库及 SQLite 实现同源统计与独立内网面板，Ledger 专用 loopback 监听提供聚合统计。
**设计：** ../specs/2026-09-27-blog-analytics-design.md 与 ../specs/2026-09-27-lan-server-monitoring-design.md；新方案对原文中“不保存监控数据”的例外仅限博客访问数据，资源曲线仍只保留在浏览器。

## 约束与检查重点

仅提交博客仓库。发布目录不保存数据库或密钥。保留内部 sample 标记而不公开显示。90 天统计，五秒可见页面采样、半小时去重。公网只返回总数，IP 网段仅内网可见。检测 Android `/proc` 权限不足、代理头伪造、双语重复、未知页面注入、统计服务不可用。

## 任务

- [x] `deploy/analytics.py`：SQLite 记录与汇总，HMAC IP 和脱敏网络，90 天清理；`tests/test_analytics.py` 验证去重、身份来源和敏感字段。
- [x] `deploy/serve.py`：POST 同源记录、GET 公开计数，路径白名单及大小/速率边界；保留静态服务与 404。
- [x] `src/components/Analytics.astro`、Base、文章页和 privacy：公开阅读/访问人数、可见页面记录、失败与中英文文案。
- [x] `deploy/monitor.py`、`deploy/monitor.html`：8765 来源限制、系统采样与故障隔离、统计可视化；`tests/test_monitor.py` 验证权限和解析。
- [x] `deploy/ledger-metrics.ts` 与安装脚本：只读聚合 loopback 8788，实际房间仓库状态变化测试；不修改 Ledger 本地未提交内容。
- [x] `deploy/termux/20-zuoer-monitor`：独立幂等启动；检查现有开机启动不被覆盖。
- [x] 运行完整验证，检查隐私和 noreply 提交身份，发布备份及新 release，验证公网和内网及双启动，推送到指定博客仓库。
- [ ] GitHub Discussions/Giscus 配置：仍需 GitHub API 登录及 Giscus App 授权。
