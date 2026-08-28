import type { APIRoute } from 'astro';
import { copy, type Lang } from '../../content';
import { deliver, isBot, json, looksLikeEmail, normalizeUrl, plainThanks, readSubmission, text, wantsJson } from '../../lib/submit';
import { clientIp, rateLimit } from '../../lib/ratelimit';
import { verifyTurnstile } from '../../lib/turnstile';

export const prerender = false;

export const POST: APIRoute = async ({ request, clientAddress }) => {
  const data = await readSubmission(request);
  const lang: Lang = text(data, 'lang') === 'en' ? 'en' : 'bg';
  const t = copy[lang];

  if (isBot(data)) {
    return wantsJson(request) ? json(200, { ok: true }) : plainThanks(lang, t.contact.doneSub);
  }

  const ip = clientIp(clientAddress, request);
  const limit = await rateLimit(ip, 'contact', 5, 3600);
  if (!limit.ok) {
    return wantsJson(request)
      ? json(429, { ok: false, error: 'rate_limited' })
      : new Response('Too many requests. Please try again later.', { status: 429 });
  }

  const human = await verifyTurnstile(text(data, 'cf-turnstile-response'), ip);
  if (!human) {
    return wantsJson(request)
      ? json(403, { ok: false, error: 'challenge' })
      : new Response('Challenge failed. Please try again.', { status: 403 });
  }

  const email = text(data, 'email');
  const name = text(data, 'name');
  if (!looksLikeEmail(email) || !name) {
    return wantsJson(request)
      ? json(400, { ok: false, error: 'invalid' })
      : new Response('Invalid submission', { status: 400 });
  }

  const company = text(data, 'company');
  const website = normalizeUrl(text(data, 'website')) || '-';

  const body = [
    'Contact request',
    '',
    `Company:  ${company || '-'}`,
    `Website:  ${website}`,
    `Name:     ${name}`,
    `Email:    ${email}`,
    `Phone:    ${text(data, 'phone') || '-'}`,
    `Needs:    ${text(data, 'needs') || '-'}`,
    `Language: ${lang}`,
    '',
    'Message:',
    text(data, 'message') || '-',
  ].join('\n');

  const sent = await deliver(`[contact] ${company || name}`, body, email);
  if (!sent) {
    return wantsJson(request) ? json(502, { ok: false, error: 'delivery' }) : new Response('Delivery failed', { status: 502 });
  }

  return wantsJson(request) ? json(200, { ok: true }) : plainThanks(lang, t.contact.doneSub);
};
