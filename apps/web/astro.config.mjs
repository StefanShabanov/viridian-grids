// @ts-check
import { defineConfig } from 'astro/config';
import vercel from '@astrojs/vercel';
import sitemap from '@astrojs/sitemap';

// Static pages, with the two form endpoints as serverless functions.
// Set SITE_URL in Vercel once the domain is decided.
export default defineConfig({
  site: process.env.SITE_URL || 'https://viridiangrids.com',
  output: 'static',
  adapter: vercel(),
  integrations: [sitemap()],
  build: { format: 'directory' },
  trailingSlash: 'ignore',
});
