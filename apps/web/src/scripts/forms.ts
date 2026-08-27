/**
 * Progressive enhancement for the two forms.
 *
 * Bundled rather than inlined so the Content-Security-Policy can stay at
 * `script-src 'self'` - prospects run our own kind of check against us, and a
 * site selling website hygiene should not need 'unsafe-inline' to work.
 *
 * Without JavaScript both forms still post normally and the endpoint replies
 * with a plain confirmation page.
 */

type Strings = { error: string; mail: string; sending: string; label: string; thanks?: string };

function stringsOf(form: HTMLFormElement, button: HTMLButtonElement): Strings {
  return {
    error: form.dataset.error || 'Something went wrong.',
    mail: form.dataset.mail || '',
    sending: button.dataset.sending || '…',
    label: button.dataset.label || button.textContent || '',
    thanks: form.dataset.thanks,
  };
}

async function post(form: HTMLFormElement): Promise<boolean> {
  const data = new FormData(form);
  const payload: Record<string, unknown> = Object.fromEntries(data);
  const needs = data.getAll('needs');
  if (needs.length) payload.needs = needs;

  const response = await fetch(form.action, {
    method: 'POST',
    headers: { 'content-type': 'application/json', accept: 'application/json' },
    body: JSON.stringify(payload),
  });
  return response.ok;
}

function enhance(form: HTMLFormElement): void {
  const button = form.querySelector<HTMLButtonElement>('button[type="submit"]');
  const message = form.querySelector<HTMLElement>('[data-msg]');
  if (!button || !message) return;

  const s = stringsOf(form, button);
  const done = form.dataset.done ? document.getElementById(form.dataset.done) : null;

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    button.disabled = true;
    button.textContent = s.sending;
    message.hidden = true;

    let ok = false;
    try {
      ok = await post(form);
    } catch {
      ok = false;
    }

    if (!ok) {
      message.className = 'formMsg formMsg--err';
      message.textContent = `${s.error} ${s.mail}`.trim();
      message.hidden = false;
      button.disabled = false;
      button.textContent = s.label;
      return;
    }

    if (done) {
      form.hidden = true;
      done.hidden = false;
      done.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }

    form.querySelectorAll('.fields, button[type="submit"]').forEach((el) => el.remove());
    message.className = 'formMsg formMsg--ok';
    message.textContent = s.thanks || '';
    message.hidden = false;
  });
}

document.querySelectorAll<HTMLFormElement>('form[data-enhance]').forEach(enhance);
