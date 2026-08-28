/**
 * Per-client gated pages.
 *
 * A prospect gets a link and a six-digit code in the same email. The page ships
 * only ciphertext: the code plus the page salt derives an AES-GCM key, and the
 * browser decrypts on entry. A wrong code fails to decrypt - there is nothing
 * readable sitting in the HTML for someone to pull out of devtools.
 *
 * What this is and is not:
 *
 *   Six digits is a million combinations. Against an offline attack that alone
 *   would not hold, which is why the URL slug carries 128 bits of randomness.
 *   An attacker needs the link *and* the code, and the link only ever comes from
 *   the client. For a report about somebody's own public website that is the
 *   right amount of protection - enough that the gate means something, not so
 *   much that we are pretending it is a vault.
 *
 * Everything runs in the browser with Web Crypto. No server, no session, no
 * database - the pages stay static and deploy like the rest of the site.
 */

export const CODE_LENGTH = 6;
export const PBKDF2_ITERATIONS = 600_000;

export interface Sealed {
  /** base64 salt for the key derivation */
  salt: string;
  /** base64 AES-GCM initialisation vector */
  iv: string;
  /** base64 ciphertext */
  data: string;
}

export interface ClientRecord {
  slug: string;
  /** Business name, shown before the code is entered so they know it is theirs. */
  name: string;
  /** Their website, also shown unencrypted - they already know it. */
  domain: string;
  /** Sealed report payload, when a report has been prepared. */
  report?: Sealed;
  /** Sealed path to the demo folder under /demo/. */
  demo?: Sealed;
  /** ISO date, shown on the report. */
  prepared: string;
}

const encoder = new TextEncoder();

export function toBase64(bytes: Uint8Array): string {
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

export function fromBase64(value: string): Uint8Array {
  const binary = atob(value);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) out[i] = binary.charCodeAt(i);
  return out;
}

/**
 * The slug is mixed into the key material, so the same code on two different
 * clients produces two different keys.
 */
export async function deriveKey(code: string, slug: string, salt: Uint8Array): Promise<CryptoKey> {
  const material = await crypto.subtle.importKey(
    'raw',
    encoder.encode(`${code}:${slug}`),
    'PBKDF2',
    false,
    ['deriveKey'],
  );
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt: salt as BufferSource, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
    material,
    { name: 'AES-GCM', length: 256 },
    false,
    ['decrypt'],
  );
}

/** Returns the decrypted payload, or null when the code is wrong. */
export async function unseal(sealed: Sealed, code: string, slug: string): Promise<string | null> {
  try {
    const key = await deriveKey(code, slug, fromBase64(sealed.salt));
    const plain = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv: fromBase64(sealed.iv) as BufferSource },
      key,
      fromBase64(sealed.data) as BufferSource,
    );
    return new TextDecoder().decode(plain);
  } catch {
    // AES-GCM authentication failed: wrong code, or tampered ciphertext.
    return null;
  }
}
