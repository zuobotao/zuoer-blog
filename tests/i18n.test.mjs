import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
const read = (p) => readFileSync(`dist/${p}`, 'utf8');
test('English UI routes are built with English navigation and matching switch targets', () => {
  for (const route of ['', 'articles/', 'projects/', 'notes/', 'weekly/', 'about/', 'privacy/', 'search/', 'articles/android-phone-server/']) {
    const file = `en/${route}index.html`;
    assert.ok(existsSync(`dist/${file}`), `missing ${file}`);
    const html = read(file);
    assert.match(html, /<html lang="en"/);
    assert.ok(html.includes('href="/en/articles/"'));
    assert.ok(html.includes(`href="/${route}"`), `Chinese counterpart: ${route}`);
    assert.match(html, /hreflang="en"/);
    assert.match(html, /hreflang="zh-CN"/);
  }
});
test('Chinese intro is replaced and untranslated articles remain explicitly Chinese', () => {
  assert.ok(read('index.html').includes('hi 你好，我是左二，一个写代码的家伙！'));
  const en = read('en/articles/android-phone-server/index.html');
  assert.ok(en.includes('This article is in Chinese.'));
  assert.match(en, /class="prose" lang="zh-CN"/);
  assert.match(en, /data-pagefind-ignore/);
  assert.ok(en.includes('旧 Android 手机搭个服务器'));
});

test('language shells preserve every authored article body and share external services', () => {
  for (const route of ['articles/android-phone-server/', 'articles/worktree/', 'projects/ledger/', 'notes/writing/', 'weekly/001/']) {
    const prose = (html) => html.match(/<div class="prose" lang="zh-CN">([\s\S]*?)<\/div>/)?.[1];
    assert.ok(prose(read(`${route}index.html`)), route);
    assert.equal(prose(read(`en/${route}index.html`)), prose(read(`${route}index.html`)), route);
    assert.doesNotMatch(read(`en/${route}index.html`), /data-pagefind-body/);
  }
  for (const prefix of ['', 'en/']) {
    assert.ok(read(`${prefix}index.html`).includes('https://ledger-game.zuo2.cc/'));
    assert.ok(read(`${prefix}projects/ledger/index.html`).includes('https://ledger-game.zuo2.cc/'));
    assert.ok(read(`${prefix}index.html`).includes('href="/rss.xml"'));
  }
});

test('English table-of-contents links retain Chinese headings and valid fragments', () => {
  const html = read('en/articles/static-blog/index.html');
  assert.ok(html.includes('href="#搜索也可以是静态的"'));
  const ids = new Set([...html.matchAll(/id="([^"]+)"/g)].map((match) => match[1]));
  for (const match of html.matchAll(/href="#([^"]+)"/g)) assert.ok(ids.has(decodeURIComponent(match[1])), match[1]);
  assert.match(read('en/index.html'), /lang="zh-CN"/);
});
