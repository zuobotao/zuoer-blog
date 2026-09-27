import rss from '@astrojs/rss';
import { entries } from '../lib/content';
export async function GET(context: any) {
  const items = (
    await Promise.all(
      ['articles', 'notes', 'weekly'].map(async (s) =>
        (await entries(s)).map((p) => ({
          title: p.data.title,
          description: p.data.description,
          pubDate: p.data.date,
          link: `/${s}/${p.id}/`,
        })),
      ),
    )
  )
    .flat()
    .sort((a, b) => b.pubDate.valueOf() - a.pubDate.valueOf());
  return rss({
    title: '左二 · 技术与日常',
    description: 'AI Agent、工程实践与日常思考',
    site: context.site,
    items,
    customData: '<language>zh-cn</language>',
  });
}
