import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';

const root = 'src/content/articles';
const files = readdirSync(root)
  .filter((year) => /^20\d{2}$/.test(year))
  .flatMap((year) => readdirSync(`${root}/${year}`)
    .filter((name) => name.includes('-modb-') && name.endsWith('.md'))
    .map((name) => `${year}/${name}`));

test('imported archives retain publication dates, author and all source records', () => {
  assert.equal(files.length, 124);
  const sources = new Set();
  for (const file of files) {
    const text = readFileSync(`${root}/${file}`, 'utf8');
    const date = text.match(/^date: (\d{4}-\d{2}-\d{2})$/m)?.[1];
    const original = JSON.parse(text.match(/^originalPublishedAt: (.+)$/m)?.[1]);
    assert.equal(date, original.slice(0, 10), file);
    assert.ok(original.endsWith('+08:00'), file);
    assert.ok(file.startsWith(date.slice(0, 4)), file);
    assert.match(text, /^author: "左二"$/m);
    assert.match(text, /^draft: false$/m);
    assert.ok(text.includes(`原文发表：${original.slice(0, 19).replace('T', ' ')}`), file);
    for (const match of text.matchAll(/https:\/\/www\.modb\.pro\/db\/(\d+)/g)) sources.add(match[1]);
    assert.doesNotMatch(text, /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/);
    assert.doesNotMatch(text, /\bgh[pousr]_[A-Za-z0-9]{25,}\b/);
  }
  assert.equal(sources.size, 127);
});

test('every imported article is published in both language shells with its original day', () => {
  const listing = readFileSync('dist/articles/index.html', 'utf8');
  for (const file of files) {
    const id = file.replace(/\.md$/, '');
    const text = readFileSync(`${root}/${file}`, 'utf8');
    const date = text.match(/^date: (.+)$/m)[1].replaceAll('-', '.');
    assert.ok(listing.includes(`href="/articles/${id}/"`), id);
    for (const prefix of ['', 'en/']) {
      const page = readFileSync(`dist/${prefix}articles/${id}/index.html`, 'utf8');
      assert.ok(page.includes(date), id);
      assert.ok(page.includes('左羊公社'), id);
      assert.ok(page.includes('https://www.modb.pro/db/'), id);
    }
  }
});
