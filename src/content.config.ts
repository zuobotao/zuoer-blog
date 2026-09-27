import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';
const schema = z.object({
  title: z.string(),
  description: z.string(),
  date: z.coerce.date(),
  tags: z.array(z.string()).default([]),
  draft: z.boolean().default(false),
  sample: z.boolean().default(false),
  status: z.string().optional(),
});
export const collections = Object.fromEntries(
  ['articles', 'notes', 'weekly', 'projects'].map((name) => [
    name,
    defineCollection({
      loader: glob({ pattern: '**/*.md', base: `./src/content/${name}` }),
      schema,
    }),
  ]),
);
