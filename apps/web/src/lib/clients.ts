/**
 * Reads the per-client records at build time.
 *
 * One JSON file per client under `clients/<slug>/client.json`, written by
 * `bin/client.mjs`. Nothing here reaches the browser except the sealed payload.
 */

import fs from 'node:fs';
import path from 'node:path';
import type { ClientRecord } from './gate';

const DIR = path.resolve(process.cwd(), 'clients');

export function allClients(): ClientRecord[] {
  if (!fs.existsSync(DIR)) return [];
  return fs
    .readdirSync(DIR)
    .map((slug) => path.join(DIR, slug, 'client.json'))
    .filter((file) => fs.existsSync(file))
    .map((file) => JSON.parse(fs.readFileSync(file, 'utf8')) as ClientRecord);
}
