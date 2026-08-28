#!/usr/bin/env node
/**
 * Client page manager.
 *
 *   node bin/client.mjs add "Hotel Chiflika" hotelchiflika.com
 *   node bin/client.mjs demo hotel-chiflika "../../Web-demos/hotel chiflika.zip"
 *   node bin/client.mjs report hotel-chiflika ../scanner/out/hotelchiflika.json
 *   node bin/client.mjs list
 *
 * `add` prints the URL and the six-digit code once. The code is never stored -
 * only material derived from it - so if it is lost the client has to be re-added.
 * Write it into the cold email straight away.
 *
 * Everything it writes is committed and deploys as static files. There is no
 * server, no database and no admin panel, which is the point: a prospect page
 * costs one command and nothing recurring.
 */

import { webcrypto as crypto } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { vendorDemo } from './vendor.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB = path.resolve(HERE, '..');
const CLIENTS = path.join(WEB, 'clients');
const DEMOS = path.join(WEB, 'public', 'demo');
const ITERATIONS = 600_000;

const b64 = (bytes) => Buffer.from(bytes).toString('base64');
const rand = (n) => crypto.getRandomValues(new Uint8Array(n));

function slugify(name) {
  return name
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

/** 128 bits of URL. The code is the second factor, not the only one. */
const urlToken = () => Buffer.from(rand(16)).toString('hex');
const sixDigits = () => String(crypto.getRandomValues(new Uint32Array(1))[0] % 1_000_000).padStart(6, '0');

async function deriveKey(code, slug, salt) {
  const material = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(`${code}:${slug}`),
    'PBKDF2',
    false,
    ['deriveKey'],
  );
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: ITERATIONS, hash: 'SHA-256' },
    material,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt'],
  );
}

async function seal(plaintext, code, slug) {
  const salt = rand(16);
  const iv = rand(12);
  const key = await deriveKey(code, slug, salt);
  const data = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    new TextEncoder().encode(plaintext),
  );
  return { salt: b64(salt), iv: b64(iv), data: b64(new Uint8Array(data)) };
}

const recordPath = (slug) => path.join(CLIENTS, slug, 'client.json');

function readRecord(slug) {
  const file = recordPath(slug);
  if (!fs.existsSync(file)) {
    console.error(`No client "${slug}". Run: node bin/client.mjs list`);
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function writeRecord(record) {
  fs.mkdirSync(path.dirname(recordPath(record.slug)), { recursive: true });
  fs.writeFileSync(recordPath(record.slug), JSON.stringify(record, null, 2) + '\n', 'utf8');
}

/**
 * No zip library, so we borrow whatever the machine already has. The order
 * matters: busybox `tar` is often first on PATH under Git Bash and cannot read
 * zips at all, so `unzip` is tried first and the Windows system tar by full path.
 */
function unzip(zip, into) {
  fs.mkdirSync(into, { recursive: true });
  const source = path.resolve(zip);
  if (!fs.existsSync(source)) throw new Error(`no such archive: ${source}`);

  const attempts = [
    ['unzip', ['-qo', source, '-d', into]],
    ['C:/Windows/System32/tar.exe', ['-xf', source, '-C', into]],
    ['tar', ['-xf', source, '-C', into]],
    [
      'powershell',
      ['-NoProfile', '-Command', `Expand-Archive -LiteralPath '${source}' -DestinationPath '${into}' -Force`],
    ],
  ];

  for (const [command, args] of attempts) {
    try {
      execFileSync(command, args, { stdio: 'pipe' });
      if (fs.readdirSync(into).length) return;
    } catch {
      // try the next one
    }
  }
  throw new Error('could not extract the archive - install unzip, or extract it by hand into ' + into);
}

/**
 * Claude Design exports arrive as "<Name>.dc.html" plus support.js and uploads/.
 * Browsers need an index.html, so the newest export becomes it and the others
 * stay reachable under their own names.
 */
function normalizeDemo(dir) {
  const html = fs
    .readdirSync(dir)
    .filter((f) => f.toLowerCase().endsWith('.html'))
    .sort();
  if (!html.length) return null;
  if (!html.includes('index.html')) {
    const preferred = html.find((f) => /v(\d+)\.dc\.html$/i.test(f)) || html[html.length - 1];
    fs.copyFileSync(path.join(dir, preferred), path.join(dir, 'index.html'));
    return preferred;
  }
  return 'index.html';
}

// ------------------------------------------------------------------ commands

async function add(name, domain) {
  if (!name) throw new Error('usage: add "<Business name>" <domain>');
  const slug = urlToken();
  const code = sixDigits();
  writeRecord({
    slug,
    name,
    domain: domain || '',
    prepared: new Date().toISOString().slice(0, 10),
    label: slugify(name),
  });
  console.log(`\n  Client added: ${name}`);
  console.log(`  Report page:  https://viridiangrids.com/r/${slug}`);
  console.log(`  Demo page:    https://viridiangrids.com/d/${slug}   (once a demo is imported)`);
  console.log(`  Access code:  ${code}`);
  console.log('\n  Save the code now - it is not stored anywhere.\n');
  return { slug, code };
}

async function demo(slug, zip, code) {
  const record = readRecord(slug);
  if (!code) throw new Error('usage: demo <slug> <zip> <code>');
  const token = urlToken();
  const dir = path.join(DEMOS, token);
  unzip(zip, dir);
  const entry = normalizeDemo(dir);
  if (!entry) throw new Error('no .html file found in the archive');

  // Pull React, the photographs and the fonts local, so the demo is a closed
  // system and the site's CSP does not have to be opened up to accommodate it.
  await vendorDemo(dir);

  // Re-importing mints a fresh folder. Drop the previous one rather than leaving
  // orphaned copies of somebody's photographs in the repository.
  if (record.demoDir && record.demoDir !== token) {
    const old = path.join(DEMOS, record.demoDir);
    if (fs.existsSync(old)) fs.rmSync(old, { recursive: true, force: true });
  }

  // The record never reaches the browser, so the folder name can sit here in the
  // clear for housekeeping. What the page carries is only the sealed copy.
  record.demoDir = token;
  record.demo = await seal(`/demo/${token}/index.html`, code, slug);
  writeRecord(record);
  console.log(`  Demo imported for ${record.name}`);
  console.log(`  Entry point: ${entry} -> index.html`);
  console.log(`  Visit:       https://viridiangrids.com/d/${slug}\n`);
}

async function report(slug, jsonPath, code) {
  const record = readRecord(slug);
  if (!code) throw new Error('usage: report <slug> <report.json> <code>');
  const payload = fs.readFileSync(jsonPath, 'utf8');
  JSON.parse(payload); // fail loudly here rather than in the browser
  record.report = await seal(payload, code, slug);
  writeRecord(record);
  console.log(`  Report attached for ${record.name}`);
  console.log(`  Visit: https://viridiangrids.com/r/${slug}\n`);
}

function list() {
  if (!fs.existsSync(CLIENTS)) return console.log('  no clients yet');
  for (const slug of fs.readdirSync(CLIENTS)) {
    const file = recordPath(slug);
    if (!fs.existsSync(file)) continue;
    const r = JSON.parse(fs.readFileSync(file, 'utf8'));
    const has = [r.report && 'report', r.demo && 'demo'].filter(Boolean).join(' + ') || 'nothing yet';
    console.log(`  ${r.name.padEnd(26)} /r/${r.slug}  (${has})`);
  }
}

const [command, ...args] = process.argv.slice(2);
const commands = { add, demo, report, list };
if (!commands[command]) {
  console.error('commands: add | demo | report | list');
  process.exit(1);
}
await commands[command](...args);
