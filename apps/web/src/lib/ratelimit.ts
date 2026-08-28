/**
 * IP rate limiting for the form endpoints.
 *
 * The forms call a paid third party (email) on every accepted request, so an
 * unthrottled endpoint is a cost and a denial-of-service lever: a few hundred
 * requests exhaust the daily email quota, after which real enquiries bounce.
 * The honeypot stops naive bots; this stops the targeted floods it cannot,
 * which matters because outreach means handing our domain to exactly the
 * technical people who will poke it.
 *
 * Backed by Upstash Redis over its REST API - no SDK, no persistent connection,
 * which suits a serverless function that may be a cold start every time. A fixed
 * window is coarse but entirely adequate for abuse prevention.
 *
 * Two deliberate choices:
 *
 *   Fail OPEN. If Upstash is unreachable we allow the request and log it. A
 *   contact form that rejects real customers during a cache outage is worse than
 *   one that briefly loses its throttle - and Turnstile is the second layer.
 *
 *   Degrade quietly. With no Upstash credentials configured the limiter is a
 *   no-op, so the code ships and runs before the store exists. It warns once so
 *   the gap is visible rather than silent.
 */

const URL_ENV = 'UPSTASH_REDIS_REST_URL';
const TOKEN_ENV = 'UPSTASH_REDIS_REST_TOKEN';

export interface RateLimitResult {
  ok: boolean;
  /** Requests remaining in the current window, for a Retry hint. */
  remaining: number;
}

let warnedMissing = false;

function credentials(): { url: string; token: string } | null {
  const url = import.meta.env[URL_ENV];
  const token = import.meta.env[TOKEN_ENV];
  if (!url || !token) {
    if (!warnedMissing) {
      console.warn(`[ratelimit] ${URL_ENV}/${TOKEN_ENV} not set - form rate limiting is OFF`);
      warnedMissing = true;
    }
    return null;
  }
  return { url, token };
}

/**
 * Fixed-window counter. `INCR` returns the new count; on the first hit of a
 * window we set the expiry, so keys clean themselves up. Both run in one
 * pipeline round-trip.
 *
 * @param ip      the client address, from the platform
 * @param bucket  a name per endpoint, so the check and contact forms are separate
 * @param limit   requests allowed per window
 * @param windowSeconds  window length
 */
export async function rateLimit(
  ip: string,
  bucket: string,
  limit = 5,
  windowSeconds = 3600,
): Promise<RateLimitResult> {
  const creds = credentials();
  if (!creds) return { ok: true, remaining: limit };

  // Bucket the key by window so a new window starts a fresh count without a
  // separate reset. Uses the request's own arrival, floored to the window.
  const now = Math.floor(Date.now() / 1000);
  const windowStart = now - (now % windowSeconds);
  const key = `rl:${bucket}:${ip}:${windowStart}`;

  try {
    const response = await fetch(`${creds.url}/pipeline`, {
      method: 'POST',
      headers: { authorization: `Bearer ${creds.token}`, 'content-type': 'application/json' },
      body: JSON.stringify([
        ['INCR', key],
        ['EXPIRE', key, windowSeconds, 'NX'],
      ]),
      // A slow cache must not hold up the response; fail open past this.
      signal: AbortSignal.timeout(2500),
    });

    if (!response.ok) throw new Error(`Upstash HTTP ${response.status}`);
    const results = (await response.json()) as { result: number }[];
    const count = Number(results?.[0]?.result ?? 0);
    return { ok: count <= limit, remaining: Math.max(0, limit - count) };
  } catch (error) {
    console.error('[ratelimit] check failed, allowing request:', (error as Error).message);
    return { ok: true, remaining: limit };
  }
}

/** Best-effort client IP: the platform value, then the standard proxy header. */
export function clientIp(clientAddress: string | undefined, request: Request): string {
  if (clientAddress) return clientAddress;
  const forwarded = request.headers.get('x-forwarded-for');
  if (forwarded) return forwarded.split(',')[0].trim();
  return request.headers.get('x-real-ip') || 'unknown';
}
