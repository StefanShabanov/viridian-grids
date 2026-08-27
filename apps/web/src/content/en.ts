/**
 * English copy. The Bulgarian file is the one customers read - this one exists for
 * EU prospects and for reviewing wording quickly. `bg.ts` is type-checked against
 * this shape, so a key added here must be added there.
 */

export const en = {
  htmlLang: 'en',
  meta: {
    home: {
      title: 'Website monitoring and maintenance for small and medium businesses',
      description:
        'We monitor uptime, certificates, updates and backups, fix what breaks, and send one clear report a month. From EUR 29/month.',
    },
    check: {
      title: 'Free website health check',
      description:
        'A non-intrusive, read-only check of what your website already shows publicly. Reviewed by hand, sent within one working day.',
    },
    pricing: {
      title: 'Pricing',
      description: 'Three plans with published prices: Monitor EUR 29, Care EUR 59, Business EUR 99 per month.',
    },
    services: { title: 'Services', description: 'Monitoring, maintenance, security hygiene, troubleshooting and business-critical checks.' },
    how: { title: 'How it works', description: 'Assessment, setup, monitoring, response, reporting.' },
    report: { title: 'Sample monthly report', description: 'One page a month, in plain language, no dashboard login required.' },
    security: { title: 'Security and access', description: 'How we handle the access you give us: least privilege, vaulted credentials, EU storage, signed DPA.' },
    faq: { title: 'Frequently asked questions', description: 'Hosting, platforms, outages, backups, cancellation and what is included.' },
    about: { title: 'About', description: 'One engineer in Sofia, and a deliberately narrow service.' },
    contact: { title: 'Contact', description: 'Tell us about your website. The initial assessment costs nothing.' },
  },

  nav: { services: 'Services', pricing: 'Pricing', how: 'How it works', report: 'Sample report', faq: 'FAQ', cta: 'Check my website' },

  hero: {
    eyebrow: 'Managed monitoring for small and medium business',
    h1: 'Website monitoring and maintenance for small and medium businesses',
    sub: 'We monitor uptime, certificates, updates and backups, fix what breaks, and send you one clear report a month. No IT person required.',
    cta1: 'Check my website',
    cta2: 'View plans',
    note: 'Free check · no account · reviewed by hand',
    panelTitle: 'example.bg — live status',
    live: 'monitored',
    panelFoot: 'Checked every 60s from 2 locations',
    panelNote: 'Illustration of a monitored site, not live data.',
    rows: [
      { k: 'uptime (30d)', v: '99.99%', warn: false },
      { k: 'ssl certificate', v: 'valid · 64d', warn: false },
      { k: 'domain expiry', v: '212 days', warn: false },
      { k: 'avg response', v: '610 ms', warn: false },
      { k: 'backups (last 7)', v: '7 / 7 ok', warn: false },
      { k: 'pending updates', v: '2', warn: true },
      { k: 'open incidents', v: '0', warn: false },
    ],
  },

  band: {
    label: 'Start here',
    text: 'See what an outsider can already tell about your website.',
    cta: 'Request the free check',
  },

  check: {
    label: 'Free website check',
    title: 'Find out what your website is telling the internet',
    sub: 'We run a non-intrusive, read-only check of what is already publicly visible: HTTPS, certificate, response time, security headers and redirects. Nothing is attacked, nothing is logged in to.',
    disclaimer: 'Public endpoints only · no login attempts · no scanning of private systems',
    exampleLabel: 'Example output',
    exampleTitle: 'What you get back',
    exampleNote:
      'Below is what a completed check looks like. The values are from an example site — your own report will contain your results, reviewed by a person before it is sent.',
    basic: 'Basic assessment',
    results: [
      { k: 'HTTPS', v: 'PASS', tone: 'ok', note: 'Site serves over HTTPS and redirects HTTP traffic.' },
      { k: 'Certificate', v: 'PASS', tone: 'ok', note: 'Valid certificate, 64 days until renewal.' },
      { k: 'Response time', v: 'REVIEW', tone: 'warn', note: '1,840 ms first byte — slower than we would expect for this page.' },
      { k: 'Security headers', v: 'REVIEW', tone: 'warn', note: '2 common headers missing. Low risk, easy to fix.' },
      { k: 'Redirects', v: 'PASS', tone: 'ok', note: 'Single clean redirect to the canonical domain.' },
      { k: 'Platform', v: 'INFO', tone: 'info', note: 'Platform and version identified — eligible for full maintenance plans.' },
    ],
    formTitle: 'Request your check',
    formSub:
      'We review every report by hand before sending it, and include what we would actually change first. Usually within one working day.',
    fields: { url: 'Website', name: 'Your name', email: 'Email', company: 'Company (optional)' },
    ph: { url: 'https://example.bg', email: 'you@company.bg' },
    cta: 'Send me the full report',
    sending: 'Sending…',
    consent:
      'By sending this you agree that we may check the public pages of this website and reply by email. We do not pass your details to anyone.',
    thanks: 'Thanks — we will review your website and send the full report within one working day.',
    error: 'Something went wrong sending the form. Email us directly at',
  },

  monitor: {
    label: 'What we monitor',
    title: 'The things that quietly break your platform',
    items: [
      { code: '01', name: 'Uptime', desc: 'Checked every minute from more than one location, so a blip is not a false alarm.' },
      { code: '02', name: 'SSL & domain', desc: 'Certificate and domain expiry tracked well before anyone sees a warning page.' },
      { code: '03', name: 'Updates', desc: 'WordPress, Node.js, PHP, Laravel — whatever you run, updated on a schedule rather than when someone remembers.' },
      { code: '04', name: 'Backups', desc: 'We watch that backups actually complete — and test a restore periodically.' },
      { code: '05', name: 'Security hygiene', desc: 'Configuration checks, headers, exposed files, admin access review.' },
      { code: '06', name: 'Performance', desc: 'Response times tracked month over month so slow decline is visible.' },
      { code: '07', name: 'Forms & checkout', desc: 'On Business plans, the paths that make you money are checked, not just the homepage.' },
      { code: '08', name: 'One monthly report', desc: 'Plain language, one page, no dashboard login required.' },
    ],
  },

  how: {
    label: 'How it works',
    title: 'Five steps, then it is our problem',
    steps: [
      { n: 'STEP 01', name: 'Assessment', desc: 'We inspect your website and tell you what state it is actually in — before you pay anything.' },
      { n: 'STEP 02', name: 'Setup', desc: 'We configure monitoring, backups, update schedules and alert routing.' },
      { n: 'STEP 03', name: 'Monitoring', desc: 'Automated checks run continuously. Alerts go to us first, not to you.' },
      { n: 'STEP 04', name: 'Response', desc: 'When something breaks we investigate and fix within your plan allowance.' },
      { n: 'STEP 05', name: 'Reporting', desc: 'One clear monthly summary of what happened and what we did.' },
    ],
  },

  pricing: {
    label: 'Pricing',
    title: 'Three plans, published prices',
    per: '/month',
    sub: 'No sales call required to find out the price. All plans are monthly, cancellable with 30 days notice. Prices exclude VAT.',
    badge: 'Most popular',
    cta: 'Start with an assessment',
    plans: {
      monitor: {
        name: 'Monitor',
        blurb: 'For businesses that want to know when something goes wrong.',
        f: [
          'Uptime checks every 5 minutes',
          'SSL & domain expiry monitoring',
          'Response time monitoring',
          'Basic health checks',
          'Alerts by email and SMS',
          'Monthly report',
        ],
      },
      care: {
        name: 'Care',
        blurb: 'Monitoring plus the maintenance that prevents most incidents.',
        f: [
          'Everything in Monitor',
          'Uptime checks every minute',
          'Platform, dependency & plugin updates',
          'Backup monitoring & restore tests',
          'Basic security hygiene',
          '30 minutes troubleshooting included',
        ],
      },
      business: {
        name: 'Business',
        blurb: 'For websites that are part of daily operations or revenue.',
        f: [
          'Everything in Care',
          'Checks every 30 seconds',
          'Forms & checkout flow monitoring',
          'Deeper performance checks',
          'Priority response',
          '60 minutes troubleshooting included',
        ],
      },
    },
    notes: [
      {
        k: 'ADDITIONAL WORK',
        v: 'Work beyond the included allowance is EUR 45/hour, or quoted upfront for larger jobs. We always ask before starting.',
      },
      {
        k: 'SETUP',
        v: 'One-time onboarding of EUR 90 covers assessment, access setup and configuration. Waived for founding customers and on annual plans.',
      },
      {
        k: 'ANY PLATFORM',
        v: 'Monitoring works with any website. Full maintenance covers WordPress, Node.js, PHP/Laravel and static sites — ask about yours.',
      },
    ],
  },

  sla: {
    title: 'Response times — what we commit to',
    head: ['', 'Monitor', 'Care', 'Business'],
    rows: [
      { label: 'Site down — we start investigating', v: ['60 min', '30 min', '15 min'] },
      { label: 'Coverage window', v: ['09:00–18:00', '08:00–20:00', '07:00–22:00'] },
      { label: 'Non-urgent request reply', v: ['2 business days', '1 business day', '4 business hours'] },
    ],
    foot: 'Coverage windows are Monday to Friday. Monitoring itself runs 24/7 and overnight alerts are recorded, but human response starts at the beginning of the next window.',
  },

  report: {
    label: 'Sample report',
    title: 'Monitoring is invisible when it works. So we show you.',
    sub: 'One page, once a month, in language you can forward to anyone. This is the real report format, filled in with an example customer.',
    company: 'Example Company Ltd',
    period: 'Monthly website report — July 2026',
    score: 'Overall health',
    blocks: [
      { head: 'Availability', big: '99.98%', tone: 'ok', lines: ['target 99.9%', '9 min total downtime'] },
      { head: 'SSL & domain', big: 'Valid', tone: 'ok', lines: ['certificate: 64 days left', 'domain: 212 days left'] },
      { head: 'Performance', big: '720 ms', tone: 'ok', lines: ['previous month: 810 ms', 'improved 11%'] },
      { head: 'Updates', big: '8 applied', tone: 'plain', lines: ['platform: 1 · dependencies: 6', 'no service interruption'] },
      { head: 'Backups', big: '31 / 31', tone: 'ok', lines: ['all scheduled backups ok', '1 restore test completed'] },
      { head: 'Security hygiene', big: '0 critical', tone: 'warn', lines: ['2 configuration recommendations', 'admin accounts reviewed'] },
    ],
    incidents: 'Incidents',
    incDate: '12 July',
    inc1: 'Website unavailable — hosting provider restart',
    inc1d: 'Duration: 6 minutes',
    resolved: 'Resolved',
    foot: 'Reports are sent as PDF on the 1st of each month. No dashboard login required.',
  },

  problems: {
    label: 'Problems we watch for',
    title: 'The failures that cost SMEs money',
    items: [
      { title: 'Your website goes offline', desc: 'We detect availability problems ourselves, instead of waiting for a customer to tell you the site is down.' },
      { title: 'Your SSL certificate expires', desc: 'Browsers show a full-page security warning. We track certificate and domain expiry weeks in advance.' },
      { title: 'An update is forgotten', desc: 'An outdated plugin, an old Node.js version, an unsupported PHP release — the most common way a site gets compromised.' },
      { title: 'Your backup is not actually working', desc: 'A backup is only useful if it completes and can be restored. We verify both.' },
      { title: 'Your contact form silently breaks', desc: 'On Business plans we check the form and checkout paths, not just whether the homepage loads.' },
      { title: 'Nobody knows who to call', desc: 'When something breaks, you have one contact who already has the access and the history.' },
    ],
  },

  trust: {
    label: 'Security & access',
    title: 'You are giving us access. Here is exactly how we handle it.',
    sub: 'We do not make guarantees about your website being unhackable. We do make commitments about how we treat the access you give us.',
    items: [
      { t: 'Least privilege by default', d: 'We ask for the smallest access that lets us do the job — usually a dedicated account, not your personal login.' },
      { t: 'Credentials stored in a vault', d: 'Secrets live in an encrypted password manager with 2FA. Nothing sits in email, chat or spreadsheets.' },
      { t: 'We document what we need', d: 'Before onboarding you get a written list of exactly which access is required and why.' },
      { t: 'Access is revoked when you leave', d: 'On cancellation we remove our accounts and confirm in writing within 5 working days.' },
      { t: 'Backups are encrypted', d: 'Backup copies are encrypted at rest and stored in the EU, separate from your hosting.' },
      { t: 'Your data is never sold', d: 'Monitoring data belongs to you. It is not resold, shared or used to train anything.' },
      { t: 'Testing only with authorisation', d: 'Anything beyond passive checks — active security testing — happens only with written permission.' },
      { t: 'GDPR handling', d: 'We act as a processor, with a signed DPA, EU-based storage and a documented retention period.' },
    ],
    foot: 'We deliberately avoid words like "protected" or "secured". Monitoring and maintenance reduce risk. They do not eliminate it, and any provider who tells you otherwise is selling something.',
  },

  services: {
    label: 'Services',
    title: 'Five services. That is the whole list.',
    sub: 'Focused on what small businesses actually need to keep a website working. Everything below is delivered by us, not resold.',
    soon: 'Coming later: server monitoring · network monitoring',
    items: [
      { n: '01', name: 'Website monitoring', plans: 'ALL PLANS', desc: 'Uptime, SSL, DNS, domain expiry, response times and availability, checked continuously from multiple locations. Alerts reach us before they reach you.' },
      { n: '02', name: 'Website maintenance', plans: 'CARE · BUSINESS', desc: 'Scheduled updates — WordPress core and plugins, Node.js and npm dependencies, PHP versions, Laravel packages — with a backup before every update and a check afterwards that the site still works.' },
      { n: '03', name: 'Security hygiene', plans: 'CARE · BUSINESS', desc: 'Configuration checks, security headers, exposed file review, admin account review and update discipline. Reduces the common paths in — it is not a guarantee.' },
      { n: '04', name: 'Troubleshooting', plans: 'CARE · BUSINESS', desc: 'Application errors, hosting issues, performance problems and configuration faults — WordPress, Node.js or custom code alike. A monthly allowance is included; anything beyond is quoted before we start.' },
      { n: '05', name: 'Business-critical monitoring', plans: 'BUSINESS', desc: 'Contact forms, booking pages, ecommerce checkout and other important endpoints are tested end to end, so a broken form is found in minutes rather than weeks.' },
    ],
  },

  faq: {
    label: 'FAQ',
    title: 'The questions we actually get asked',
    items: [
      { q: 'Do I need to change hosting?', a: 'Usually no. We work with your existing hosting provider. If your hosting is the actual cause of repeated problems we will tell you, but changing it is your decision.' },
      { q: 'Which platforms do you support?', a: 'Monitoring works with any website, whatever it is built on. Full maintenance covers WordPress, Node.js applications, PHP and Laravel, static sites and most standard stacks — version, dependency and package updates. If you run something less usual, tell us and we will say honestly whether we can support it well.' },
      { q: 'What happens when my website goes down?', a: 'Our system alerts us, not you. We confirm the outage, identify whether it is hosting, DNS, certificate or application, and start fixing or escalating to your host. You get a notification and a short written summary afterwards.' },
      { q: 'Do you guarantee my website cannot be hacked?', a: 'No, and nobody honestly can. Monitoring and maintenance significantly reduce risk by closing the common paths in — outdated software, weak configuration, missing updates. They cannot make a system impossible to compromise.' },
      { q: 'Do you make design or content changes?', a: 'Small content edits fall inside the troubleshooting allowance on Care and Business. Redesigns and new features are quoted separately as project work.' },
      { q: 'Are fixes included in the price?', a: 'Care includes 30 minutes and Business 60 minutes of troubleshooting per month. Beyond that we quote before doing any work — you will never receive a surprise invoice. Unused minutes do not roll over.' },
      { q: 'Can I cancel?', a: 'Yes, monthly with 30 days notice. We remove our access, hand over any credentials we hold and confirm in writing.' },
      { q: 'Where are backups stored?', a: 'Encrypted, in EU-based object storage, separate from your hosting provider so a hosting failure does not take the backups with it.' },
      { q: 'Will you need my passwords?', a: 'We need access, not your personal passwords. We create a dedicated administrator account where possible and store all credentials in an encrypted vault.' },
      { q: 'Do you provide 24/7 support?', a: 'Not yet, and we would rather say so. Monitoring runs 24/7 and alerts are recorded overnight; human response follows the coverage window in your plan.' },
    ],
  },

  about: {
    label: 'About',
    title: 'One engineer, and a deliberately narrow service',
    paras: [
      'I am a DevOps engineer who works with infrastructure, monitoring and automation. I started Viridian Grids because a lot of small businesses depend on a website every day but do not need — and do not want — an internal IT team.',
      'The usual alternatives are a freelancer who disappears, an agency that only responds to new project work, or nobody at all until something breaks. None of those are monitoring. So the website goes down on a Saturday and someone finds out on Monday from a customer.',
      'This is intentionally a small, focused service. I do not run a 40-person company, and telling you otherwise would be the first thing I got wrong. What you get instead is one person who knows your setup, has documented the access, and has already been alerted before you notice.',
      'Based in Sofia, working with businesses across Bulgaria and the EU.',
    ],
    stackLabel: 'What runs behind the scenes',
    stack: 'Prometheus · Grafana · Blackbox Exporter · Uptime Kuma · Alertmanager · MainWP · Ansible · Restic',
    stackNote: 'Listed for the technically curious. You never have to touch any of it — that is the point of the service.',
  },

  contact: {
    label: 'Contact',
    title: 'Tell us about your website',
    sub: 'The more you tell us here, the more useful the first reply is. No obligation, and the initial assessment costs nothing.',
    fields: { company: 'Company', website: 'Website', name: 'Your name', email: 'Email', phone: 'Phone (optional)' },
    ph: { company: 'Example Company Ltd', website: 'https://example.bg', email: 'name@company.bg', phone: '+359 ...' },
    needs: 'What do you need?',
    msg: 'Anything else',
    msgPh: 'Existing problems, hosting provider, who currently maintains the site…',
    options: ['Monitoring', 'Maintenance & updates', 'Backups', 'Security check', 'Troubleshooting', 'I am not sure yet'],
    cta: 'Send request',
    sending: 'Sending…',
    note: 'We reply within one working day.',
    consent: 'We use what you send here to reply to you, and for nothing else.',
    doneTitle: 'Request received',
    doneSub: 'We will look at your website before replying, so the first message you get already contains something useful. Usually within one working day.',
    error: 'Something went wrong sending the form. Email us directly at',
  },

  final: {
    title: 'Get a free website health check',
    sub: 'No account, no sales call. We look at your site and tell you what we would fix first.',
    cta1: 'Check my website',
    cta2: 'Talk to us',
  },

  footer: {
    blurb: 'Managed website monitoring and maintenance for small and medium businesses.',
    c1: 'Service',
    c2: 'Start',
    c3: 'Company',
    about: 'About',
    security: 'Security & trust',
    contact: 'Contact',
    legal: 'Privacy · Terms · DPA',
  },

  a11y: { skip: 'Skip to content', language: 'Language', menu: 'Menu' },
};

export type Copy = typeof en;
