import { defineCollection, z } from "astro:content";

const landing = defineCollection({
  type: "content",
  schema: z.object({
    hero: z.object({
      titleJa: z.string(),
      titleEn: z.string(),
      subtitle: z.string(),
      downloadLabel: z.string(),
      downloadMacLabel: z.string(),
      badge: z.string(),
    }),
    features: z.array(
      z.object({
        id: z.string(),
        title: z.string(),
        description: z.string(),
      }),
    ),
    steps: z.array(
      z.object({
        title: z.string(),
        caption: z.string(),
      }),
    ),
    footer: z.object({
      copyright: z.string(),
      note: z.string(),
    }),
  }),
});

export const collections = { landing };
