import { getCollection, type CollectionKey } from 'astro:content';
export const sections = {
  articles: {
    name: '文章',
    en: 'Articles',
    description: '把问题想清楚，把实践写下来。',
  },
  projects: {
    name: '项目',
    en: 'Projects',
    description: '从想法到实现，记录构建过程。',
  },
  notes: {
    name: '短记',
    en: 'Notes',
    description: '尚未成篇，但值得留下的片段。',
  },
  weekly: {
    name: '周读',
    en: 'Weekly',
    description: '读过的东西，留下的思考。',
  },
};
export async function entries(section: string) {
  return (await getCollection(section as CollectionKey))
    .filter((p) => !p.data.draft && p.data.date <= new Date())
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
}
export const dateLabel = (date: Date) =>
  date.toISOString().slice(0, 10).replaceAll('-', '.');
