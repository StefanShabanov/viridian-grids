/**
 * Renders a decrypted client report.
 *
 * Two audiences at once. A hotel owner should get the point from the first
 * screen without meeting the word "header"; an engineer they forward it to
 * should find nothing overstated. So the order is: verdict, what it means for
 * the business, the one urgent thing, then the technical detail with every
 * claim traceable to a public source.
 *
 * Built with the DOM rather than innerHTML on purpose. The payload is ours, but
 * a report page that pastes decrypted text into innerHTML is one careless scan
 * result away from being an XSS hole.
 */

export interface Cve {
  id: string;
  severity: string;
  what: string;
}

export interface CveGroup {
  product: string;
  version: string;
  reported: number;
  shown: number;
  critical: number;
  high: number;
  note: string;
  items: Cve[];
}

export interface Report {
  domain: string;
  business?: string;
  date?: string;
  score: number;
  band: string;
  bandTone?: 'good' | 'fair' | 'bad';
  headline?: string;
  summary?: { title: string; text: string }[];
  urgent?: { label: string; title: string; detail: string; note?: string };
  cveCaveat?: string;
  cveGroups?: CveGroup[];
  attention?: { title: string; detail?: string }[];
  working?: string[];
  detected?: string[];
  next?: { step: string; title: string; effort?: string; text: string }[];
  checks?: { label: string; note: string; engines?: string };
  disclaimer?: string;
  prepared?: string;
}

function el(tag: string, className?: string, text?: string): HTMLElement {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function severityClass(severity: string): string {
  const s = severity.toUpperCase();
  if (s === 'CRITICAL') return 'sev sev--critical';
  if (s === 'HIGH') return 'sev sev--high';
  if (s === 'MEDIUM') return 'sev sev--medium';
  return 'sev sev--low';
}

const SEVERITY_BG: Record<string, string> = {
  CRITICAL: 'критична',
  HIGH: 'висока',
  MEDIUM: 'средна',
  LOW: 'ниска',
};

function heading(root: HTMLElement, text: string): void {
  root.append(el('h2', 'rp__h', text));
}

export function renderReport(root: HTMLElement, r: Report): void {
  root.textContent = '';
  const page = el('div', 'rp');

  // ---------------------------------------------------------------- verdict
  const head = el('header', 'rp__head');
  const id = el('div');
  if (r.business) id.append(el('div', 'rp__business', r.business));
  id.append(el('div', 'rp__domain', r.domain));
  if (r.date) id.append(el('div', 'rp__date', `Проверено на ${r.date}`));
  head.append(id);

  const scoreBox = el('div', 'rp__scoreBox');
  scoreBox.append(el('div', 'rp__scoreLabel', 'Обща оценка'));
  const score = el('div', `rp__score is-${r.bandTone || 'fair'}`);
  score.append(el('b', undefined, String(r.score)), el('span', undefined, '/100'));
  scoreBox.append(score, el('div', 'rp__band', r.band));
  head.append(scoreBox);
  page.append(head);

  if (r.headline) page.append(el('p', 'rp__headline', r.headline));

  // ------------------------------------------------- what it means for them
  if (r.summary?.length) {
    const grid = el('div', 'rp__summary');
    for (const s of r.summary) {
      const card = el('div', 'rp__card');
      card.append(el('div', 'rp__cardTitle', s.title), el('p', 'rp__cardText', s.text));
      grid.append(card);
    }
    page.append(grid);
  }

  // ------------------------------------------------------ the one urgent thing
  if (r.urgent) {
    const box = el('section', 'rp__urgent');
    box.append(el('div', 'rp__urgentLabel', r.urgent.label));
    box.append(el('h2', 'rp__urgentTitle', r.urgent.title));
    box.append(el('p', 'rp__urgentText', r.urgent.detail));
    if (r.urgent.note) {
      const note = el('div', 'rp__urgentNote');
      note.append(el('p', undefined, r.urgent.note));
      box.append(note);
    }
    page.append(box);
  }

  // ------------------------------------------------------------------- CVEs
  if (r.cveGroups?.length) {
    heading(page, 'Публично докладвани уязвимости');
    if (r.cveCaveat) page.append(el('p', 'rp__caveat', r.cveCaveat));

    for (const g of r.cveGroups) {
      const box = el('section', 'cveg');

      const gh = el('div', 'cveg__head');
      gh.append(el('div', 'cveg__name', `${g.product} ${g.version}`));
      const counts = el('div', 'cveg__counts');
      if (g.critical) counts.append(el('span', 'sev sev--critical', `${g.critical} критични`));
      if (g.high) counts.append(el('span', 'sev sev--high', `${g.high} високи`));
      counts.append(el('span', 'cveg__total', `${g.shown} от ${g.reported} докладвани`));
      gh.append(counts);
      box.append(gh);

      if (g.note) box.append(el('p', 'cveg__note', g.note));

      const list = el('ul', 'cveg__list');
      for (const item of g.items) {
        const li = el('li', 'cve__row');
        const top = el('div', 'cve__top');
        const link = document.createElement('a');
        link.className = 'cve__id';
        link.href = `https://nvd.nist.gov/vuln/detail/${encodeURIComponent(item.id)}`;
        link.rel = 'noopener nofollow';
        link.target = '_blank';
        link.textContent = item.id;
        top.append(link);
        top.append(el('span', severityClass(item.severity), SEVERITY_BG[item.severity.toUpperCase()] || item.severity));
        li.append(top);
        li.append(el('p', 'cve__what', item.what));
        list.append(li);
      }
      box.append(list);
      page.append(box);
    }
  }

  // -------------------------------------------------------- other findings
  if (r.attention?.length) {
    heading(page, 'Останалото, което намерихме');
    const list = el('ul', 'findings');
    for (const f of r.attention) {
      const li = el('li', 'finding finding--warn');
      li.append(el('span', 'finding__t', f.title));
      if (f.detail) li.append(el('p', 'finding__d', f.detail));
      list.append(li);
    }
    page.append(list);
  }

  if (r.working?.length) {
    heading(page, 'Какво вече работи както трябва');
    const list = el('ul', 'findings');
    for (const w of r.working) {
      const li = el('li', 'finding finding--ok');
      li.append(el('span', 'finding__t', w));
      list.append(li);
    }
    page.append(list);
  }

  if (r.detected?.length) {
    heading(page, 'Разпознати технологии');
    const wrap = el('p', 'detected');
    for (const d of r.detected) wrap.append(el('span', 'detected__item', d));
    page.append(wrap);
  }

  // ---------------------------------------------------------- what we'd do
  if (r.next?.length) {
    heading(page, 'Какво бихме направили, в този ред');
    const steps = el('ol', 'rp__steps');
    for (const n of r.next) {
      const li = el('li', 'rp__step');
      li.append(el('div', 'rp__stepN', n.step));
      const body = el('div');
      const title = el('div', 'rp__stepTitle', n.title);
      if (n.effort) title.append(el('span', 'rp__effort', n.effort));
      body.append(title, el('p', 'rp__stepText', n.text));
      li.append(body);
      steps.append(li);
    }
    page.append(steps);
  }

  // ------------------------------------------------------------------- foot
  const foot = el('footer', 'rp__foot');
  if (r.checks) {
    foot.append(el('div', 'rp__checksLabel', r.checks.label));
    foot.append(el('p', undefined, r.checks.note));
    if (r.checks.engines) foot.append(el('p', 'rp__engines', r.checks.engines));
  }
  if (r.disclaimer) foot.append(el('p', 'rp__disclaimer', r.disclaimer));
  if (r.prepared) foot.append(el('p', 'rp__prepared', r.prepared));
  page.append(foot);

  root.append(page);
}
