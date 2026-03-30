import { defineCollection, z } from "astro:content";

const screenshot = z.object({
  src: z.string(),
  alt: z.string(),
});

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
    how: z.object({
      title: z.string(),
      lead: z.string(),
    }),
    steps: z.array(
      z.object({
        title: z.string(),
        caption: z.string(),
      }),
    ),
    trust: z.object({
      title: z.string(),
      intro: z.string(),
      windowsTitle: z.string(),
      windowsSteps: z.array(z.string()),
      windowsImage: screenshot,
      macTitle: z.string(),
      macSteps: z.array(z.string()),
      macImages: z.array(screenshot),
      sourceCta: z.string(),
    }),
    footer: z.object({
      copyright: z.string(),
      note: z.string(),
    }),
  }),
});

export const collections = { landing };
