import { defineMiddleware } from 'astro:middleware';

// Translate interface text only. Authored content is preserved in its original language.
const labels: Record<string, string> = {
  'hi 你好，我是左二，一个写代码的家伙！': "Hi, I'm Zuoer, a guy who writes code!",
  '左二 · 技术与日常': 'Zuoer · Code & everyday life',
  '左二的个人技术实验室。记录 AI Agent、软件工程，以及构建过程中的思考。': 'Notes on AI agents, software engineering, and building things.',
  '跳转到正文': 'Skip to content', '左二首页': 'Zuoer home',
  '技术与日常': 'Code & everyday life', '主导航': 'Main navigation',
  '全部文章': 'All articles', '更多短记': 'More notes',
  '最近写下的': 'Latest writing', '随手记': 'Field notes',
  '文章': 'Articles', '项目': 'Projects', '短记': 'Notes', '周读': 'Weekly', '关于': 'About', '搜索': 'Search',
  '纸短，思考很长。': 'Small pages, lasting thoughts.', '隐私': 'Privacy',
  '写下思考': 'Write it down', '保持': 'Stay ', '好奇': 'curious',
  '在代码与日常之间，留一页给想法。': 'A space for ideas, between code and everyday life.',
  '关于 AI Agents、工程实践，以及沿途的发现。': 'AI agents, engineering practice, and discoveries along the way.',
  '你好，我是左二': "Hi, I'm Zuoer", '随想，随写。': 'Notes as they come.',
  '案头，': 'On my desk,', '未完的事。': 'work in progress.',
  'Agent 如何从「能生成代码」走向「能完成工程任务」。': 'How agents move from generating code to completing engineering tasks.',
  '构建中': 'Projects', '好内容，慢慢读。': 'Good reading takes its time.',
  '通过 RSS 订阅更新': 'Subscribe via RSS',
  '已上线': 'Live', '构想阶段': 'Concept', '开发中': 'In development',
  '把问题想清楚，把实践写下来。': 'Think problems through. Write down what works.',
  '从想法到实现，记录构建过程。': 'From ideas to implementation.',
  '尚未成篇，但值得留下的片段。': 'Fragments worth keeping.', '读过的东西，留下的思考。': 'Reading and reflections.',
  '篇记录': 'entries', '持续生长的手记': 'An evolving notebook', '按标签筛选': 'Filter by tag', '全部': 'All',
  '返回': 'Back to ', '继续阅读': 'Keep reading', '感谢读到这里。': 'Thanks for reading.',
  '文章目录': 'Table of contents', '本文目录': 'On this page',
  '讨论': 'Discussion', '评论暂未开启。配置 GitHub Discussions 后可接入 Giscus。': 'Comments are not enabled yet.',
  '加载 GitHub 评论': 'Load GitHub comments',
  '评论由 Giscus 提供。参与讨论需要 GitHub 账户，加载评论会连接第三方服务。': 'Comments use Giscus. A GitHub account is required; loading comments connects to a third-party service.',
  '写代码，也写下思考。': 'Writing code, and writing things down.',
  '找一找': 'Find something', '搜索文章、项目、短记与周读。': 'Search articles, projects, notes, and weekly reading. Content is in Chinese.',
  '搜索索引尚未生成，请运行 npm run build 后用 npm run preview 预览。': 'The search index is not available yet. Build the site before previewing.',
  '隐私说明': 'Privacy notice', '返回首页': 'Back to home', '回到首页': 'Back to home',
  '未找到页面': 'Page not found', '这页还没写': 'This page is missing',
  '链接可能已变更，也可能是一个尚未开始的想法。': 'The link may have changed, or the page may not exist yet.',
};
const replacements = Object.entries(labels).sort(([a], [b]) => b.length - a.length);

export const onRequest = defineMiddleware(async ({ url }, next) => {
  const response = await next();
  if (!url.pathname.startsWith('/en/') || !response.headers.get('content-type')?.includes('text/html')) return response;
  let html = await response.text();
  const preserved: string[] = [];
  // Protect prose, metadata and authored titles/descriptions, plus executable code.
  html = html.replace(/<div class="prose(?: about)?"[^>]*>[\s\S]*?<\/div>|<header class="article-heading"[\s\S]*?<\/header>|<div class="entry-body"[\s\S]*?<\/div>\s*<\/a>|<(a|h3|p)\b[^>]*lang="zh-CN"[^>]*>[\s\S]*?<\/\1>|<script\b[\s\S]*?<\/script>/g, (part) => {
    preserved.push(part);
    return `__ORIGINAL_${preserved.length - 1}__`;
  });
  const translate = (text: string) => {
    for (const [zh, en] of replacements) text = text.replaceAll(zh, en);
    return text;
  };
  // Never translate IDs, URL fragments or arbitrary attributes.
  html = html.replace(/<[^>]+>|[^<]+/g, (part) => part.startsWith('<')
    ? part.replace(/aria-label="([^"]*)"/g, (_, label) => `aria-label="${translate(label)}"`)
    : translate(part));
  html = html.replace(/__ORIGINAL_(\d+)__/g, (_, i) => preserved[Number(i)]);
  html = html.replace(/(<span class="title-comma">)，(<\/span>)/g, '$1,$2')
    .replace(/(<span class="name-dot">)。(<\/span>)/g, '$1.$2');
  // Internal navigation stays within the selected interface language. Feeds/assets stay shared.
  html = html.replace(/href="\/(?!en\/|rss\.xml|pagefind\/|favicon)([^".]*)"/g, 'href="/en/$1"');
  html = html.replace(/(<a[^>]*data-language="zh"[^>]*href=")\/en\//g, '$1/');
  return new Response(html, { status: response.status, headers: response.headers });
});
