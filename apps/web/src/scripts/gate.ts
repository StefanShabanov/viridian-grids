/**
 * Unlocks a client page.
 *
 * Bundled, not inlined, so `script-src 'self'` stays intact. Everything happens
 * locally: the code is never sent anywhere, because there is nowhere to send it.
 */

import { unseal, type Sealed } from '../lib/gate';
import { renderReport } from './report';

const form = document.getElementById('gate') as HTMLFormElement | null;
const out = document.getElementById('gate-out');

if (form && out) {
  const message = form.querySelector<HTMLElement>('[data-msg]')!;
  const button = form.querySelector<HTMLButtonElement>('button[type="submit"]')!;
  const input = form.querySelector<HTMLInputElement>('input[name="code"]')!;
  const slug = form.dataset.slug!;
  const mode = form.dataset.mode!;
  const sealed: Sealed = JSON.parse(form.dataset.sealed!);

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const code = input.value.trim();
    message.hidden = true;
    button.disabled = true;
    button.textContent = form.dataset.working!;

    // 600k PBKDF2 iterations is deliberately slow - about a second on a phone,
    // and the reason a stolen link is not trivially brute-forced.
    const plain = await unseal(sealed, code, slug);

    if (plain === null) {
      message.textContent = form.dataset.wrong!;
      message.hidden = false;
      button.disabled = false;
      button.textContent = form.dataset.cta!;
      input.select();
      return;
    }

    if (mode === 'demo') {
      window.location.href = plain;
      return;
    }

    form.hidden = true;
    out.hidden = false;
    renderReport(out, JSON.parse(plain));
  });
}
