import type { APIRoute } from 'astro';
import { copy, type Lang } from '../../content';
import { deliver, isBot, json, looksLikeEmail, normalizeUrl, plainThanks, readSubmission, text, wantsJson } from '../../lib/submit';

export const prerender = false;

/** Free-check requests. The scan is run by hand afterwards - nothing is scanned here. */
export const POST: APIRoute = async ({ request }) => {
  const data = await readSubmission(request);
  const lang: Lang = text(data, 'lang') === 'en' ? 'en' : 'bg';
  const t = copy[lang];

  // Silently accept and drop: a bot told it failed will simply try again.
  if (isBot(data)) {
    return wantsJson(request) ? json(200, { ok: true }) : plainThanks(lang, t.check.thanks);
  }

  const url = normalizeUrl(text(data, 'url'));
  const email = text(data, 'email');
  const name = text(data, 'name');

  if (!url || !looksLikeEmail(email) || !name) {
    return wantsJson(request)
      ? json(400, { ok: false, error: 'invalid' })
      : new Response('Invalid submission', { status: 400 });
  }

  const body = [
    'Free check requested',
    '',
    `Website:  ${url}`,
    `Name:     ${name}`,
    `Email:    ${email}`,
    `Company:  ${text(data, 'company') || '-'}`,
    `Language: ${lang}`,
    '',
    'Run it with:',
    `  ./bin/vg-scan scan ${new URL(url).hostname} --deep --lang ${lang} --html out/${new URL(url).hostname}.html`,
  ].join('\n');

  const sent = await deliver(`[check] ${new URL(url).hostname}`, body, email);
  if (!sent) {
    return wantsJson(request) ? json(502, { ok: false, error: 'delivery' }) : new Response('Delivery failed', { status: 502 });
  }

  return wantsJson(request) ? json(200, { ok: true }) : plainThanks(lang, t.check.thanks);
};
