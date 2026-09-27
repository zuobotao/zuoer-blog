# 左二博客

- 使用 Astro 静态输出，内容在 src/content 下，视觉遵守 DESIGN.md。
- 新文章默认 draft: true。sample: true 表示待审核内容，保留内部标识直到作者审核；公开页面不显示该标识。
- 不编造作者经历、项目状态、实验数据和引用。技术结论引用原始文档。
- 写作依次参考 agents/writer.md、reviewer.md、editor.md。
- 提交前运行 npm run check、npm run build、npm test、npm run test:server。
- 访问统计仅公开计数。数据库与匿名化密钥保留在服务器，禁止进入仓库或静态输出；完整 IP 不入库。详细汇总仅内网访问，统计保留 90 天。
- 发布、合并和代表作者的表达需要作者审核。不得自动将 draft 改为 false。
