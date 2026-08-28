#!/usr/bin/env node
/**
 * Generates the social share image, public/og.png (1200x630).
 *
 * Rasterised once, here, and committed - so it does not depend on font rendering
 * being available on the build server. Re-run it if the branding changes:
 *   node bin/gen-og.mjs
 */

import sharp from 'sharp';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const OUT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'public', 'og.png');
const FONT = 'Segoe UI, system-ui, Arial, sans-serif';

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="#F6F6F2"/>
  <rect x="0" y="0" width="1200" height="10" fill="#1B5E4B"/>

  <!-- brand mark: the grid -->
  <g transform="translate(90,86)">
    <rect x="0" y="0" width="46" height="46" fill="none" stroke="#1B5E4B" stroke-width="3"/>
    <rect x="3" y="3" width="20" height="20" fill="#1B5E4B"/>
    <rect x="23" y="23" width="20" height="20" fill="#1B5E4B"/>
  </g>
  <text x="152" y="120" font-family="${FONT}" font-size="34" font-weight="600" fill="#111614">Viridian Grids</text>

  <!-- headline -->
  <text x="90" y="300" font-family="${FONT}" font-size="62" font-weight="700" fill="#111614">Наблюдение и поддръжка</text>
  <text x="90" y="376" font-family="${FONT}" font-size="62" font-weight="700" fill="#111614">на сайтове за бизнеса</text>

  <!-- subline -->
  <text x="90" y="452" font-family="${FONT}" font-size="30" fill="#4A524D">Следим, обновяваме и пазим сайта ви. Един ясен отчет месечно.</text>

  <!-- footer row -->
  <text x="90" y="558" font-family="${FONT}" font-size="26" font-weight="600" fill="#1B5E4B">viridiangrids.com</text>
  <text x="1110" y="558" text-anchor="end" font-family="${FONT}" font-size="26" fill="#6B736C">От 29 &#8364;/месец</text>
</svg>`;

const size = await sharp(Buffer.from(svg)).png().toFile(OUT);
console.log(`wrote ${OUT} (${size.width}x${size.height}, ${(size.size / 1024).toFixed(0)} KB)`);
