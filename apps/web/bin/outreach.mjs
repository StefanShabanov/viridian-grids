#!/usr/bin/env node
/**
 * Cold-outreach batch manager.
 *
 *   node bin/outreach.mjs prep --top 100      # step 1: scaffold the worst N sites
 *   node bin/outreach.mjs prep hotelaura-bg.com   # scaffold one domain
 *   node bin/outreach.mjs publish hotelaura-bg.com # step 2: seal + go live
 *   node bin/outreach.mjs list                 # batch status
 *
 * Two-phase on purpose, mirroring the sales motion:
 *
 *   prep     picks prospects out of the scanner's queue.csv, ranked worst-first
 *            by our own score, and writes a HUMAN-READABLE working folder per
 *            prospect under apps/web/outreach/<domain>/:
 *              meta.json    slug, code, links, hook  (so the code is never lost)
 *              report.json  the scan JSON, copied here to be reviewed/edited
 *              email.txt    the Bulgarian cold email, links + code + domain filled
 *            Nothing is sealed and nothing is committed yet - outreach/ is
 *            gitignored precisely because it holds the plaintext access code.
 *
 *   publish  takes ONE domain you have already checked by eye (the "never report
 *            a failure-to-observe as a fact" rule lives in the human, here), seals
 *            outreach/<domain>/report.json into clients/<slug>/client.json, imports
 *            a demo if Web-demos/<domain>.zip exists, and rewrites email.txt with
 *            the final links. Only now does the page go live and get committed.
 *
 * The same six-digit code unlocks both /r/<slug> and /d/<slug> (they share the
 * client's slug), so the email carries one code, not two.
 */

import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import {
  WEB,
  CLIENTS,
  DEMOS,
  urlToken,
  sixDigits,
  slugify,
  seal,
  writeRecord,
  recordExists,
  unzip,
  normalizeDemo,
} from './client.mjs';
import { vendorDemo } from './vendor.mjs';

/** Normalize a hostname for comparison: lowercased, leading www dropped. */
const normHost = (d) => d.toLowerCase().replace(/^www\./, '');

/** Domains that already have a client record. As the client list grows this is
 *  the safeguard that keeps a prospect we have already onboarded (or emailed)
 *  from being scaffolded and pitched a second time. */
function onboardedDomains() {
  const set = new Set();
  if (!fs.existsSync(CLIENTS)) return set;
  for (const slug of fs.readdirSync(CLIENTS)) {
    const file = path.join(CLIENTS, slug, 'client.json');
    if (!fs.existsSync(file)) continue;
    try {
      const r = JSON.parse(fs.readFileSync(file, 'utf8'));
      if (r.domain) set.add(normHost(r.domain));
    } catch {
      /* skip an unreadable record rather than crash the batch */
    }
  }
  return set;
}

const SCANNER = path.resolve(WEB, '..', 'scanner');
const QUEUE = path.join(SCANNER, 'out', 'queue.csv');
// Two scanner outputs feed a prospect folder:
//   RAW  - the raw scan (findings, final_url, reachable); used to vet the prospect.
//   RICH - the curated Bulgarian customer report (vg-scan client-report); this is
//          what gets sealed and rendered. Produce it before prep:
//     vg-scan scan --from … --out-dir out/outreach
//     vg-scan intel out/outreach --top N
//     vg-scan client-report out/outreach --out-dir out/outreach-reports --contacts out/queue.csv
const RAW = path.join(SCANNER, 'out', 'outreach');
const RICH = path.join(SCANNER, 'out', 'outreach-reports');
const WEBDEMOS = path.resolve(WEB, '..', '..', 'Web-demos');
const OUTREACH = path.join(WEB, 'outreach');
const SITE = 'https://viridiangrids.com';

/** The two hooks that make an honest, concrete cold email: a named end-of-life
 *  runtime or a matched CVE. "You don't redirect to HTTPS" is thin by comparison
 *  and edges toward alarmism, so `--strong` leads with just these. */
const STRONG_HOOKS = new Set(['software_eol', 'known_cves']);

// --------------------------------------------------------------- csv reading

/** Minimal RFC-4180-ish parser: queue.csv quotes fields that contain commas. */
function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = '';
  let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') {
        field += '"';
        i++;
      } else if (c === '"') {
        quoted = false;
      } else {
        field += c;
      }
    } else if (c === '"') {
      quoted = true;
    } else if (c === ',') {
      row.push(field);
      field = '';
    } else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(field);
      field = '';
      if (row.length > 1 || row[0] !== '') rows.push(row);
      row = [];
    } else {
      field += c;
    }
  }
  if (field !== '' || row.length) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

function readQueue() {
  if (!fs.existsSync(QUEUE)) {
    throw new Error(`no queue.csv at ${QUEUE} - run: vg-scan queue out/sweep`);
  }
  const text = fs.readFileSync(QUEUE, 'utf8').replace(/^﻿/, '');
  const [header, ...lines] = parseCsv(text);
  return lines.map((cells) => Object.fromEntries(header.map((h, i) => [h, cells[i] ?? ''])));
}

/** The registrable-ish domain: last two labels, www stripped. Good enough to
 *  tell "their site" from a parked/sold domain it now redirects to. */
const base2 = (host) => host.replace(/^www\./i, '').toLowerCase().split('.').slice(-2).join('.');

/** Read the scan for the checks that decide whether a prospect is emailable at
 *  all - separate from how bad their score is. */
function scanFacts(domain) {
  const j = JSON.parse(fs.readFileSync(path.join(RAW, `${domain}.json`), 'utf8'));
  let finalHost = '';
  let offDomain = false;
  try {
    finalHost = new URL(j.final_url).host;
    offDomain = base2(finalHost) !== base2(domain);
  } catch {
    /* no usable final_url */
  }
  return { inconclusive: !!j.inconclusive, reachable: !!j.reachable, offDomain, finalHost };
}

/** Worst sites first by our own score. Excluded automatically, because a report
 *  for any of these would misrepresent reality (the "failure-to-observe reported
 *  as fact" rule), have no site to email, or double-pitch someone:
 *    - already onboarded  : a client record for this domain already exists
 *    - site_down          : never reached; there is no live page or contact
 *    - inconclusive/!reach : the scan itself is not confident
 *    - off-domain redirect : the domain now points at a different (sold/parked) site
 *  With `strong`, only end-of-life / CVE hooks are considered at all.
 *  Returns { picks, skipped } so the excluded ones are reported, not silent. */
function rankProspects(rows, top, { strong = false, onboarded = new Set() } = {}) {
  const ranked = rows
    .filter((r) => r.HookType !== 'site_down')
    .filter((r) => !strong || STRONG_HOOKS.has(r.HookType))
    .filter((r) => r.Domain && fs.existsSync(path.join(RAW, `${r.Domain}.json`)) && fs.existsSync(path.join(RICH, `${r.Domain}.json`)))
    .map((r) => ({ ...r, _score: Number.parseInt(r.Score, 10) }))
    .filter((r) => Number.isFinite(r._score))
    .sort((a, b) => a._score - b._score);

  const picks = [];
  const skipped = [];
  for (const r of ranked) {
    if (picks.length >= top) break;
    if (onboarded.has(normHost(r.Domain))) skipped.push([r.Domain, 'already onboarded']);
    else {
      const f = scanFacts(r.Domain);
      if (f.inconclusive || !f.reachable) skipped.push([r.Domain, 'inconclusive scan - re-verify by hand']);
      else if (f.offDomain) skipped.push([r.Domain, `redirects off-domain to ${f.finalHost}`]);
      else picks.push(r);
    }
  }
  return { picks, skipped };
}

// ------------------------------------------------------------------ emails

function emailBody({ domain, reportUrl, demoUrl, code }) {
  const lead = demoUrl
    ? `Попаднах на ${domain} и освен кратка публична и неинвазивна техническа проверка, подготвих и примерна концепция как сайтът Ви би могъл да изглежда в по-модерен и удобен за мобилни устройства вариант.`
    : `Попаднах на ${domain} и направих кратка публична и неинвазивна техническа проверка на сайта Ви.`;

  const links = demoUrl
    ? [
        'Техническият отчет е тук:',
        reportUrl,
        '',
        'Примерната концепция е тук:',
        demoUrl,
        '',
        `Код за достъп (важи и за двете страници): ${code}`,
      ]
    : ['Техническият отчет е тук:', reportUrl, '', `Код за достъп: ${code}`];

  const offer = demoUrl
    ? 'Според мен сайтът има добра основа като съдържание, но визуално и като потребителско изживяване вече изглежда остарял. Ако посоката Ви харесва, мога да изградя новата версия, да поема хостинга, мониторинга и последващата поддръжка.'
    : 'Според мен сайтът има добра основа като съдържание, но визуално и като потребителско изживяване вече изглежда остарял. Мога да изградя нова, модерна версия и да поема хостинга, мониторинга и последващата поддръжка.';

  return [
    `Тема: Кратка проверка на ${domain} + идея за обновяване`,
    '',
    'Здравейте,',
    '',
    'казвам се Стефан Шабанов и съм основател на Viridian Grids. Занимаваме се с мониторинг, техническа поддръжка и модернизация на бизнес сайтове.',
    '',
    lead,
    '',
    ...links,
    '',
    offer,
    '',
    'Можете да видите услугите и цените директно на сайта на Viridian Grids. Ако имате интерес или въпроси, просто ми отговорете на този имейл.',
    '',
    'Поздрави,',
    'Стефан Шабанов',
    'Founder, Viridian Grids',
    '',
  ].join('\n');
}

// ------------------------------------------------------------------ helpers

const folderFor = (domain) => path.join(OUTREACH, domain);
const metaPath = (domain) => path.join(folderFor(domain), 'meta.json');
const readMeta = (domain) => JSON.parse(fs.readFileSync(metaPath(domain), 'utf8'));

function writeMeta(meta) {
  fs.mkdirSync(folderFor(meta.domain), { recursive: true });
  fs.writeFileSync(metaPath(meta.domain), JSON.stringify(meta, null, 2) + '\n', 'utf8');
}

/** Web-demos/<domain>.zip, or a zip whose name loosely matches the domain. */
function findDemoZip(domain) {
  if (!fs.existsSync(WEBDEMOS)) return null;
  const zips = fs.readdirSync(WEBDEMOS).filter((f) => f.toLowerCase().endsWith('.zip'));
  const stem = domain.replace(/\.[a-z.]+$/i, '').toLowerCase();
  const norm = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, '');
  const hit =
    zips.find((z) => norm(z).startsWith(norm(stem))) ||
    zips.find((z) => norm(z).includes(norm(stem)));
  return hit ? path.join(WEBDEMOS, hit) : null;
}

// ------------------------------------------------------------------ commands

/** Scaffold one prospect's working folder. Idempotent: reuses an existing code. */
function prepOne(row) {
  const domain = row.Domain;
  const existing = fs.existsSync(metaPath(domain)) ? readMeta(domain) : null;
  const slug = existing?.slug ?? urlToken();
  const code = existing?.code ?? sixDigits();

  fs.mkdirSync(folderFor(domain), { recursive: true });
  // report.json is the curated report we seal and render; scan.json is the raw
  // scan, kept alongside it for verification.
  fs.copyFileSync(path.join(RICH, `${domain}.json`), path.join(folderFor(domain), 'report.json'));
  if (fs.existsSync(path.join(RAW, `${domain}.json`))) {
    fs.copyFileSync(path.join(RAW, `${domain}.json`), path.join(folderFor(domain), 'scan.json'));
  }
  const freshScore = JSON.parse(fs.readFileSync(path.join(folderFor(domain), 'report.json'), 'utf8')).score;

  const reportUrl = `${SITE}/r/${slug}`;
  const demoUrl = `${SITE}/d/${slug}`;
  const meta = {
    domain,
    company: row.Company || '',
    slug,
    code,
    label: slugify(row.Company) || slugify(domain),
    hookType: row.HookType || '',
    hook: row.Hook || '',
    hookDetail: row.HookDetail || '',
    score: Number.parseInt(row.Score, 10),
    freshScore,
    reportUrl,
    demoUrl,
    hasDemo: false,
    status: existing?.status === 'published' ? 'published' : 'prepared',
    preparedAt: existing?.preparedAt ?? new Date().toISOString().slice(0, 10),
  };
  writeMeta(meta);

  // Deliberately NO email.txt here. The email carries a report link that only
  // becomes live at `publish`; writing a ready-looking email into an unpublished
  // folder invites sending a 404 link. `publish` is the only writer of email.txt.
  return meta;
}

function prep(...args) {
  let top = 100;
  let strong = false;
  const domains = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--top') top = Number.parseInt(args[++i], 10) || top;
    else if (args[i] === '--strong') strong = true;
    else domains.push(args[i]);
  }

  const rows = readQueue();
  const onboarded = onboardedDomains();
  let picks;
  if (domains.length) {
    // Explicit domains bypass the score/redirect filters - you asked for these by
    // name - but the already-onboarded guard still applies, on purpose.
    const byDomain = Object.fromEntries(rows.map((r) => [r.Domain, r]));
    picks = [];
    for (const d of domains) {
      if (!byDomain[d]) console.warn(`  not in queue.csv, skipped: ${d}`);
      else if (onboarded.has(normHost(d))) console.warn(`  already onboarded, skipped: ${d}`);
      else picks.push(byDomain[d]);
    }
  } else {
    const ranked = rankProspects(rows, top, { strong, onboarded });
    picks = ranked.picks;
    if (ranked.skipped.length) {
      console.log(`  Auto-excluded ${ranked.skipped.length} (onboarded, unreachable, or would misrepresent the site):`);
      for (const [d, why] of ranked.skipped) console.log(`    - ${d.padEnd(34)} ${why}`);
      console.log('');
    }
  }
  if (strong) console.log('  --strong: leading with end-of-life / CVE hooks only\n');

  fs.mkdirSync(OUTREACH, { recursive: true });
  let n = 0;
  for (const row of picks) {
    if (!fs.existsSync(path.join(RICH, `${row.Domain}.json`))) {
      console.warn(`  no curated report for ${row.Domain} (run vg-scan client-report), skipped`);
      continue;
    }
    const meta = prepOne(row);
    n++;
    console.log(`  ${String(n).padStart(3)}. ${meta.domain.padEnd(34)} score=${String(meta.freshScore).padStart(3)}  ${meta.hookType}`);
  }
  console.log(`\n  Prepared ${n} prospect folder(s) under apps/web/outreach/`);
  console.log('  Review each report.json, then: node bin/outreach.mjs publish <domain>\n');
}

/** Step 2: seal the (verified) report, attach a demo if present, go live. */
async function publish(domain) {
  if (!domain) throw new Error('usage: publish <domain>');
  if (!fs.existsSync(metaPath(domain))) throw new Error(`not prepared: ${domain} (run prep first)`);
  const meta = readMeta(domain);
  const { slug, code } = meta;

  const reportJson = fs.readFileSync(path.join(folderFor(domain), 'report.json'), 'utf8');
  JSON.parse(reportJson); // fail here, not in the browser

  const record = recordExists(slug)
    ? JSON.parse(fs.readFileSync(path.join(CLIENTS, slug, 'client.json'), 'utf8'))
    : { slug, name: meta.company || domain, domain, prepared: meta.preparedAt, label: meta.label };

  record.report = await seal(reportJson, code, slug);

  // Optional demo: only if you have designed one and dropped the zip.
  const zip = findDemoZip(domain);
  let demoUrl = null;
  if (zip) {
    const token = urlToken();
    const dir = path.join(DEMOS, token);
    unzip(zip, dir);
    if (!normalizeDemo(dir)) throw new Error(`no .html in ${zip}`);
    await vendorDemo(dir);
    if (record.demoDir && record.demoDir !== token) {
      const old = path.join(DEMOS, record.demoDir);
      if (fs.existsSync(old)) fs.rmSync(old, { recursive: true, force: true });
    }
    record.demoDir = token;
    record.demo = await seal(`/demo/${token}/index.html`, code, slug);
    demoUrl = meta.demoUrl;
    console.log(`  demo imported from ${path.basename(zip)}`);
  }

  writeRecord(record);

  // Rewrite the email now that we know whether it carries a demo.
  meta.hasDemo = Boolean(demoUrl);
  meta.status = 'published';
  meta.publishedAt = new Date().toISOString().slice(0, 10);
  writeMeta(meta);
  fs.writeFileSync(
    path.join(folderFor(domain), 'email.txt'),
    emailBody({ domain, reportUrl: meta.reportUrl, demoUrl, code }),
    'utf8',
  );

  console.log(`\n  Published ${domain}`);
  console.log(`  Report: ${meta.reportUrl}`);
  if (demoUrl) console.log(`  Demo:   ${demoUrl}`);
  console.log(`  Code:   ${code}`);
  console.log(`  Email ready: apps/web/outreach/${domain}/email.txt`);
  console.log('  Commit clients/ + public/demo/ and deploy, then send.\n');
}

function list() {
  if (!fs.existsSync(OUTREACH)) return console.log('  nothing prepared yet');
  const domains = fs.readdirSync(OUTREACH).filter((d) => fs.existsSync(metaPath(d)));
  if (!domains.length) return console.log('  nothing prepared yet');
  const metas = domains.map(readMeta).sort((a, b) => a.score - b.score);
  for (const m of metas) {
    const flags = [m.status, m.hasDemo ? 'demo' : 'report-only'].join(' + ');
    console.log(`  ${m.domain.padEnd(34)} score=${String(m.score).padStart(3)}  ${flags}`);
  }
  const pub = metas.filter((m) => m.status === 'published').length;
  console.log(`\n  ${metas.length} prepared, ${pub} published.`);
}

const [command, ...args] = process.argv.slice(2);
const commands = { prep, publish, list };
if (import.meta.url === pathToFileURL(process.argv[1] || '').href) {
  if (!commands[command]) {
    console.error('commands: prep [--top N] [--strong] [domain...] | publish <domain> | list');
    process.exit(1);
  }
  await commands[command](...args);
}
