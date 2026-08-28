/**
 * Cloudflare Turnstile verification.
 *
 * Turnstile is a privacy-preserving CAPTCHA alternative: the visitor solves an
 * invisible or low-friction challenge, the widget hands back a token, and the
 * server confirms that token with Cloudflare before trusting the request. It is
 * free and it does not profile the user, which matters on a site whose own
 * privacy notice promises no third-party tracking - a challenge on two form
 * submissions is a defensible, disclosed exception.
 *
 * Layered with the IP rate limit rather than replacing it: Turnstile stops
 * automated submissions, the rate limit stops a determined flood from one
 * source even if a token farm is in play.
 *
 * Degrades quietly. With no secret key configured, verification is skipped and
 * the endpoint behaves as before. So the code ships now and the protection
 * switches on the moment the keys are set - no redeploy of logic, just config.
 */

const SECRET_ENV = 'TURNSTILE_SECRET_KEY';
const VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';

let warnedMissing = false;

/** Whether Turnstile is switched on (a secret is present). */
export function turnstileEnabled(): boolean {
  return Boolean(import.meta.env[SECRET_ENV]);
}

/**
 * Verify a client token. Returns true when Turnstile is off (nothing to check),
 * and when the token is genuinely valid; false only when it is enabled and the
 * token is missing or rejected.
 */
export async function verifyTurnstile(token: string | undefined, ip?: string): Promise<boolean> {
  const secret = import.meta.env[SECRET_ENV];
  if (!secret) {
    if (!warnedMissing) {
      console.warn(`[turnstile] ${SECRET_ENV} not set - challenge verification is OFF`);
      warnedMissing = true;
    }
    return true;
  }

  if (!token) return false;

  const form = new URLSearchParams({ secret, response: token });
  if (ip && ip !== 'unknown') form.set('remoteip', ip);

  try {
    const response = await fetch(VERIFY_URL, {
      method: 'POST',
      headers: { 'content-type': 'application/x-www-form-urlencoded' },
      body: form,
      signal: AbortSignal.timeout(4000),
    });
    if (!response.ok) throw new Error(`siteverify HTTP ${response.status}`);
    const outcome = (await response.json()) as { success: boolean };
    return outcome.success === true;
  } catch (error) {
    // A Cloudflare outage should not silently disable the gate: if the challenge
    // is enabled and we cannot verify, we reject rather than wave it through.
    console.error('[turnstile] verification failed, rejecting:', (error as Error).message);
    return false;
  }
}
