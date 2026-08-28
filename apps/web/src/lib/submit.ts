/**
 * Form intake. Both forms land here.
 *
 * Deliberately small: it validates, refuses obvious bots, and emails the
 * submission to one inbox. There is no database and no queue, because there is
 * no volume yet - the plan says manual onboarding until 10-20 customers, and a
 * lead sitting in an inbox is a lead that gets read.
 *
 * The scan itself is NOT run here. See the comment in CheckSection.astro.
 */

export type Submission = Record<string, string | string[]>;

const MAX_FIELD = 2000;

/** Accepts JSON (from the enhanced form) and form-encoded (from a browser without JS). */
export async function readSubmission(request: Request): Promise<Submission> {
  const type = request.headers.get('content-type') || '';
  if (type.includes('application/json')) {
    const body = await request.json();
    return body && typeof body === 'object' ? (body as Submission) : {};
  }
  const form = await request.formData();
  const out: Submission = {};
  for (const key of new Set(form.keys())) {
    const values = form.getAll(key).map(String);
    out[key] = values.length > 1 ? values : values[0];
  }
  return out;
}

export function text(data: Submission, key: string): string {
  const value = data[key];
  const raw = Array.isArray(value) ? value.join(', ') : (value ?? '');
  return String(raw).trim().slice(0, MAX_FIELD);
}

/** A bot filling every field it can see, including the one nobody can. */
export function isBot(data: Submission): boolean {
  return text(data, 'website2') !== '';
}

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function looksLikeEmail(value: string): boolean {
  return EMAIL.test(value);
}

/** Accepts a bare host too - people type "example.bg", not "https://example.bg". */
export function normalizeUrl(value: string): string | null {
  if (!value) return null;
  const candidate = /^https?:\/\//i.test(value) ? value : `https://${value}`;
  try {
    const url = new URL(candidate);
    if (!url.hostname.includes('.')) return null;
    return url.toString();
  } catch {
    return null;
  }
}

/**
 * Deliver by email. Returns false when the mail provider is not configured yet,
 * so the caller can decide - we treat that as a failure rather than silently
 * dropping somebody's enquiry.
 */
export async function deliver(
  subject: string,
  body: string,
  opts: { replyTo?: string; to?: string } = {},
): Promise<boolean> {
  const key = import.meta.env.RESEND_API_KEY;
  // Per-form override (CHECK_TO_EMAIL / CONTACT_TO_EMAIL), else the shared inbox.
  const to = opts.to || import.meta.env.LEAD_TO_EMAIL;
  const from = import.meta.env.LEAD_FROM_EMAIL;
  const replyTo = opts.replyTo;

  if (!key || !to || !from) {
    console.error('[submit] mail not configured; submission was NOT delivered:\n' + body);
    return false;
  }

  const response = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { authorization: `Bearer ${key}`, 'content-type': 'application/json' },
    body: JSON.stringify({
      from,
      to: [to],
      subject,
      text: body,
      ...(replyTo && looksLikeEmail(replyTo) ? { reply_to: replyTo } : {}),
    }),
  });

  if (!response.ok) {
    console.error('[submit] resend rejected the message', response.status, await response.text());
    return false;
  }
  return true;
}

/** What a browser without JavaScript gets back after a successful post. */
export function plainThanks(lang: string, message: string): Response {
  const home = lang === 'en' ? '/en' : '/';
  const html = `<!doctype html><html lang="${lang === 'en' ? 'en' : 'bg'}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>OK</title>
<style>body{font:16px/1.6 system-ui,sans-serif;background:#F6F6F2;color:#111614;margin:0;
display:grid;place-items:center;min-height:100vh;padding:24px}
main{max-width:44ch}a{color:#1B5E4B}</style></head>
<body><main><p>${escapeHtml(message)}</p><p><a href="${home}">&larr; ${lang === 'en' ? 'Back to the site' : 'Обратно към сайта'}</a></p></main></body></html>`;
  return new Response(html, { status: 200, headers: { 'content-type': 'text/html; charset=utf-8' } });
}

export function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] as string,
  );
}

export function json(status: number, body: Record<string, unknown>): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

export function wantsJson(request: Request): boolean {
  return (request.headers.get('accept') || '').includes('application/json');
}
