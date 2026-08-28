/**
 * Makes a demo self-contained.
 *
 * A Claude Design export points at three kinds of thing it does not own: React
 * from unpkg, the prospect's own photographs still hosted on their WordPress,
 * and Google Fonts. All three are a problem here.
 *
 *   - The site runs a strict CSP. Loading scripts from unpkg means either the
 *     demo stays broken or the policy gets punched full of holes.
 *   - Hotlinking the prospect's images sends traffic to their server every time
 *     anyone opens the demo. We are selling them monitoring; quietly consuming
 *     their bandwidth to show them a mockup is not a good look.
 *   - A demo that depends on someone else's server breaks when they move a file,
 *     and it will be sitting in an inbox for weeks.
 *
 * Downloads mirror the remote path - `assets/<host>/<path>` - rather than being
 * renamed to a hash. That matters because these exports build image URLs by
 * concatenation:
 *
 *     const IMG = "https://www.hotelchiflika.com/wp-content/uploads/";
 *     ... IMG + "2021/07/SGS_2284.jpg"
 *
 * Rewriting only the full URLs we can see would leave that base pointing at
 * their server. Mirroring the path means rewriting the *origin prefix* fixes
 * both the literal URLs and every string built from them.
 */

import fs from 'node:fs';
import path from 'node:path';

/** Files worth rewriting - the export is HTML plus a support bundle. */
const TEXT_FILES = /\.(html?|js|css)$/i;

/** Anything we can meaningfully store next to the page. */
const ASSET = /\.(js|mjs|css|jpe?g|png|gif|webp|avif|svg|ico|woff2?|ttf|otf|mp4|webm)($|\?)/i;

/** Google Fonts serves CSS from a path with no file extension. */
const STYLESHEET = /^https:\/\/fonts\.googleapis\.com\/css/i;

const URL_RE = /https?:\/\/[^\s"'()<>\\]+/g;

function findUrls(text) {
  return new Set(text.match(URL_RE) || []);
}

function walk(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full));
    else out.push(full);
  }
  return out;
}

/** `https://host/a/b.jpg?x=1` -> `host/a/b.jpg`, kept safe for a filesystem. */
function mirrorPath(url) {
  const parsed = new URL(url);
  let name = parsed.pathname.replace(/^\/+/, '') || 'index';
  if (parsed.search) name += parsed.search.replace(/[^A-Za-z0-9._-]/g, '_');
  const safe = name
    .split('/')
    .map((part) => part.replace(/[^A-Za-z0-9._-]/g, '_').slice(0, 80))
    .join('/');
  // Extension last: truncating a long query string used to eat it, which then
  // hid the stylesheet from the pass that follows its font references.
  const ext = path.extname(safe) ? '' : STYLESHEET.test(url) ? '.css' : '.bin';
  return `${parsed.hostname}/${safe}${ext}`;
}

async function download(url) {
  const response = await fetch(url, {
    redirect: 'follow',
    headers: {
      // Google Fonts serves woff2 only to browsers that say they understand it.
      'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36',
    },
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return Buffer.from(await response.arrayBuffer());
}

/**
 * Downloads every external asset a demo references and rewrites references to a
 * relative path. Requests are sequential with a pause: the photographs belong to
 * a prospect we have not spoken to yet, and a burst of parallel requests at
 * somebody's WordPress is exactly the behaviour this business warns people about.
 */
export async function vendorDemo(dir, { pauseMs = 200, log = console.log } = {}) {
  const assetsDir = path.join(dir, 'assets');
  const saved = new Map(); // url -> relative path under the demo folder
  const failed = [];
  let bytes = 0;

  const fetchOne = async (url) => {
    if (saved.has(url)) return null;
    const rel = path.posix.join('assets', mirrorPath(url));
    const target = path.join(dir, rel);
    try {
      if (!fs.existsSync(target)) {
        const body = await download(url);
        fs.mkdirSync(path.dirname(target), { recursive: true });
        fs.writeFileSync(target, body);
        bytes += body.length;
        await new Promise((r) => setTimeout(r, pauseMs));
        saved.set(url, rel);
        return body;
      }
      saved.set(url, rel);
      return fs.readFileSync(target);
    } catch (error) {
      failed.push(`${url} (${error.message})`);
      return null;
    }
  };

  // Pass 1: everything referenced by the HTML and JS.
  const files = walk(dir).filter((f) => TEXT_FILES.test(f));
  const first = new Set();
  for (const file of files) {
    for (const url of findUrls(fs.readFileSync(file, 'utf8'))) {
      if (ASSET.test(url) || STYLESHEET.test(url)) first.add(url);
    }
  }
  for (const url of first) await fetchOne(url);

  // Pass 2: a stylesheet has its own dependencies. Google Fonts CSS is nothing
  // but url() references to woff2 files, so without this the fonts stay remote.
  for (const [url, rel] of [...saved]) {
    // Decide from the URL, not the saved filename - the filename is derived and
    // has been wrong before.
    if (!STYLESHEET.test(url) && !url.split('?')[0].endsWith('.css')) continue;
    const cssPath = path.join(dir, rel);
    let css = fs.readFileSync(cssPath, 'utf8');
    for (const inner of findUrls(css)) {
      const body = await fetchOne(inner);
      if (body === null && !saved.has(inner)) continue;
      // Inside the stylesheet, point at the file relative to the stylesheet.
      const from = path.posix.join('assets', mirrorPath(url), '..');
      const to = path.posix.join('assets', mirrorPath(inner));
      css = css.split(inner).join(path.posix.relative(from, to));
    }
    fs.writeFileSync(cssPath, css, 'utf8');
  }

  // Rewrite pass. Full URLs first, longest to shortest so no URL corrupts
  // another; then bare origins, which is what fixes concatenated paths.
  const origins = new Set();
  for (const url of saved.keys()) {
    const { protocol, host } = new URL(url);
    origins.add(`${protocol}//${host}/`);
  }

  const fullUrls = [...saved.keys()].sort((a, b) => b.length - a.length);
  for (const file of files) {
    let text = fs.readFileSync(file, 'utf8');
    const before = text;
    for (const url of fullUrls) text = text.split(url).join(saved.get(url));
    for (const origin of origins) {
      const { hostname } = new URL(origin);
      text = text.split(origin).join(`assets/${hostname}/`);
      // Some markup carries the http:// twin of an https:// asset.
      text = text.split(origin.replace(/^https:/, 'http:')).join(`assets/${hostname}/`);
    }
    if (text !== before) fs.writeFileSync(file, text, 'utf8');
  }

  // Whatever is left cannot be stored next to the page - an embedded map, a
  // social link. Report it so the CSP is a decision rather than an accident.
  const remaining = new Set();
  for (const file of files) {
    for (const url of findUrls(fs.readFileSync(file, 'utf8'))) {
      try {
        remaining.add(new URL(url).origin);
      } catch {
        /* not a URL we can parse */
      }
    }
  }

  // The preconnect hints pointed at hosts we no longer use.
  for (const file of files.filter((f) => /\.html?$/i.test(f))) {
    const text = fs.readFileSync(file, 'utf8');
    const stripped = text.replace(/<link[^>]+rel="preconnect"[^>]*>\s*/gi, '');
    if (stripped !== text) fs.writeFileSync(file, stripped, 'utf8');
  }

  log(`  vendored ${saved.size} files (${(bytes / 1024 / 1024).toFixed(1)} MB)`);
  if (failed.length) {
    log(`  could not fetch ${failed.length}:`);
    for (const f of failed) log(`    ${f}`);
  }
  if (remaining.size) log(`  still external: ${[...remaining].join(', ')}`);

  return { downloaded: saved.size, failed, external: [...remaining], bytes };
}
