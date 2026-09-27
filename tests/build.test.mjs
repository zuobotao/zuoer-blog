import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
const root = resolve('dist');
test('all main routes, content and search index are generated', () => {
  for (const p of [
    'index.html',
    'articles/index.html',
    'projects/index.html',
    'notes/index.html',
    'weekly/index.html',
    'about/index.html',
    'search/index.html',
    '404.html',
    'articles/worktree/index.html',
    'rss.xml',
    'sitemap-index.xml',
    'pagefind/pagefind.js',
  ])
    assert.ok(existsSync(resolve(root, p)), p);
});
test('all generated internal links point to existing output', () => {
  const walk = (d) =>
    readdirSync(d, { withFileTypes: true }).flatMap((e) =>
      e.isDirectory() ? walk(resolve(d, e.name)) : [resolve(d, e.name)],
    );
  for (const file of walk(root).filter((f) => f.endsWith('.html')))
    for (const match of readFileSync(file, 'utf8').matchAll(
      /href="(\/[^"]*)"/g,
    )) {
      const path = decodeURI(match[1].split(/[?#]/)[0]);
      assert.ok(
        existsSync(resolve(root, '.' + path)) ||
          existsSync(resolve(root, '.' + path, 'index.html')),
        `${file}: ${path}`,
      );
    }
});
test('marked content remains public without visible sample labels', () => {
  assert.match(readFileSync(resolve(root, 'rss.xml'), 'utf8'), /<item>/);
  const markedRoutes = [
    ['articles/worktree/index.html', '为什么多 Agent 写代码需要 Git Worktree'],
    ['articles/harness/index.html', '给 Agent 一个可以验证的工作环境'],
    ['articles/static-blog/index.html', '一个技术博客，为什么选择静态生成'],
    ['notes/task-boundary/index.html', '好的任务边界，比更多 Agent 更重要'],
    ['notes/writing/index.html', '留下当时为什么这样做'],
    ['weekly/001/index.html', '周读 001：从工具到工作环境'],
  ];
  for (const [route, title] of markedRoutes) {
    assert.ok(existsSync(resolve(root, route)), route);
    const html = readFileSync(resolve(root, route), 'utf8');
    assert.ok(html.includes(title), route);
    assert.doesNotMatch(
      html,
      /class="sample(?:-notice)?"|示例项目|Sample project|Sample content/,
    );
  }
  for (const route of [
    'index.html',
    'articles/index.html',
    'notes/index.html',
    'weekly/index.html',
    'projects/index.html',
    'about/index.html',
    'en/index.html',
    'en/articles/worktree/index.html',
  ]) {
    const html = readFileSync(resolve(root, route), 'utf8');
    assert.doesNotMatch(
      html,
      /class="sample(?:-notice)?"|示例项目|Sample project|Sample content/,
    );
  }
  assert.match(
    readFileSync(resolve(root, 'articles/worktree/index.html'), 'utf8'),
    /为什么多 Agent 写代码需要 Git Worktree/,
  );
});
test('draft content is absent from routes, lists and RSS', () => {
  assert.ok(!existsSync(resolve(root, 'articles/writing-workflow-draft')));
  for (const file of ['index.html', 'articles/index.html', 'rss.xml'])
    assert.doesNotMatch(
      readFileSync(resolve(root, file), 'utf8'),
      /Agent 写作流程草稿/,
    );
});
