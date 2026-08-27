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
    report: {
      title: 'Sample reports',
      description:
        'Both reports in full: the free initial assessment, and the monthly report customers receive. Real formats, example data.',
    },
    security: { title: 'Security and access', description: 'How we handle the access you give us: least privilege, vaulted credentials, EU storage, signed DPA.' },
    faq: { title: 'Frequently asked questions', description: 'Hosting, platforms, outages, backups, cancellation and what is included.' },
    about: { title: 'About', description: 'One engineer in Sofia, and a deliberately narrow service.' },
    contact: { title: 'Contact', description: 'Tell us about your website. The initial assessment costs nothing.' },
    privacy: { title: 'Privacy notice', description: 'What this website collects, why, and what you can ask us to do about it. No cookies, no analytics, no tracking.' },
    terms: { title: 'Terms of service', description: 'The standing terms for the monitoring and maintenance plans, in plain language.' },
    dpa: { title: 'Data processing agreement', description: 'How we handle personal data on your website: our role, our sub-processors, and what happens when you leave.' },
  },

  nav: { services: 'Services', pricing: 'Pricing', how: 'How it works', report: 'Sample reports', faq: 'FAQ', cta: 'Check my website' },

  hero: {
    eyebrow: 'Website monitoring and maintenance for small and medium business',
    h1: 'When your website goes down, you hear it from us — not from a customer.',
    sub: 'We watch your site around the clock, keep it updated and keep the backups honest. You hear about a problem once it is already fixed — in one clear report a month. No IT person required.',
    cta1: 'Check my website',
    cta2: 'View plans',
    note: 'Free check · no account · reviewed by hand',
    panelTitle: 'example.bg — live status',
    live: 'monitored',
    panelFoot: 'Checked every minute',
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

  /* Measured, not claimed. Every number here comes from the 1,028-site sweep in
     apps/scanner/out/sweep - recompute before changing any of them, and keep the
     CVE wording within the scanner's own rule: a version match is evidence, not
     proof. See intel/__init__.py. */
  proof: {
    label: 'What we measured',
    title: 'The question is not whether your website will go down, but when.',
    sub: 'We checked more than 1,000 Bulgarian websites — hotels, guest houses, dental clinics, law firms. This is what we found.',
    stats: [
      { big: '1,028', label: 'Bulgarian websites checked' },
      { big: '73/100', label: 'median health score' },
      { big: '1 in 6', label: 'have publicly reported vulnerabilities against the version they run*' },
      { big: '133', label: 'of those carry at least one rated high or critical' },
    ],
    body: '75 sites run software that no longer receives security updates at all. The most common by far is PHP 7.4, which stopped getting fixes in November 2022 — followed by PHP 5.6, and in a few cases PHP 5.3, unpatched since 2014. Almost none of this is a decision anybody made. It is a hosting default nobody revisited.',
    footnoteLabel: '* What is a CVE?',
    footnote:
      'A CVE is a public identifier for a weakness found in a specific version of a piece of software. Anyone can look up what a given number means in the NIST database at nvd.nist.gov. A version match does not prove a site is exploitable — the host may have applied the fix without changing the version number, which distribution packages often do. That is why every report we send says "reported against this version", never "you are vulnerable".',
    cta: 'Check your website free',
  },

  band: {
    label: 'Start here',
    text: 'In a few minutes you will know what is wrong with your website — and which part of it is urgent.',
    cta: 'Request the free check',
  },

  check: {
    label: 'Free website check',
    title: 'Free check: the results on a single page',
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
    seeFull: 'See a full sample report, with sources',
  },

  monitor: {
    label: 'What we monitor',
    title: 'What takes a website down',
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
    perYear: '/year',
    billing: { monthly: 'Monthly', annual: 'Annual', save: '2 months free' },
    instead: 'instead of',
    saveWord: 'you save',
    annualPerk: 'Setup fee waived',
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
    anchor: 'What does one day without a working website cost you? For most hotels, shops and clinics — more than a whole year of monitoring here.',
    qualify: 'If you have your own IT person, or an agency already doing this, you do not need us. If your website is maintained whenever somebody remembers, get in touch.',
    notes: [
      {
        k: 'BEYOND THE PLAN',
        v: 'Work beyond the included allowance is EUR 20/hour. For anything larger we first write down what it involves and how long it will take, and start only once you have approved it.',
      },
      {
        k: 'GETTING STARTED',
        v: 'A one-time EUR 49 covers assessment, access setup and configuration. Waived for founding customers and on annual plans.',
      },
      {
        k: 'ANNUAL',
        v: 'Pay for 10 months, use 12. Setup is waived, and your price stays locked for the term.',
      },
      {
        k: 'PLATFORMS',
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
    label: 'Monthly report',
    title: 'Monitoring is invisible when it works. So we show you.',
    sub: 'One page, once a month, in language you can forward to anyone. This is the real report format, filled in with an example customer.',
    company: 'Example Company Ltd',
    period: 'Monthly website report — July 2026',
    score: 'Overall health',
    blocks: [
      { head: 'Availability', big: '99.98%', tone: 'ok', lines: ['target 99.9%', '9 min total downtime'] },
      { head: 'SSL & domain', big: 'Valid', tone: 'ok', lines: ['certificate: 64 days left', 'domain: 212 days left'] },
      { head: 'Performance', big: '720 ms', tone: 'ok', lines: ['previous month: 810 ms', 'improved 11%'] },
      { head: 'Updates', big: '8 applied', tone: 'plain', lines: ['platform: 1 · plugins: 7', 'no service interruption'] },
      { head: 'Backups', big: '31 / 31', tone: 'ok', lines: ['all scheduled backups ok', '1 restore test completed'] },
      {
        head: 'Known vulnerabilities',
        big: '0 open',
        tone: 'ok',
        lines: ['none reported against detected versions', '2 configuration recommendations'],
      },
    ],
    incidents: 'Incidents',
    incDate: '12 July',
    inc1: 'Website unavailable — hosting provider restart',
    inc1d: 'Duration: 6 minutes',
    resolved: 'Resolved',
    updatesHead: 'Updates applied',
    updatesCols: ['Component', 'From', 'To', 'Why'],
    updates: [
      { what: 'WordPress core', from: '6.5.2', to: '6.5.5', why: 'closes 3 publicly reported issues' },
      { what: 'WooCommerce', from: '8.7.0', to: '8.9.1', why: 'maintenance release' },
      { what: 'Contact Form 7', from: '5.9.3', to: '5.9.8', why: 'closes 1 publicly reported issue' },
      { what: 'Yoast SEO', from: '22.4', to: '22.8', why: 'maintenance release' },
    ],
    updatesMore: '+ 4 further plugin updates, each backed up before and checked after.',
    foot: 'Reports are sent as PDF on the 1st of each month. No dashboard login required.',
  },

  /* The other half of the story: the one-page assessment a prospect gets for free,
     before there is any relationship. Wording follows the scanner's own rules -
     a version match is not proof of exposure, so nothing here says "you are
     vulnerable". See apps/scanner/src/vg_scanner/intel/__init__.py. */
  initial: {
    label: 'Initial assessment',
    title: 'The first report: what the free check tells you',
    sub: 'This is what arrives after the free check. One page, reviewed by a person before it is sent. Everything on it can be seen from outside the site — nothing is attacked and nothing is logged in to.',
    domain: 'primerna-firma.bg',
    reportTitle: 'Website Health Check',
    date: 'Checked on 27.08.2026',
    overall: 'Overall',
    score: 68,
    band: 'Needs some attention',
    heads: { attention: 'Worth looking at', working: 'Working well', detected: 'Detected' },
    attention: [
      {
        t: 'PHP 7.4 no longer receives security updates',
        d: 'The PHP 7.4 line reached end of life on 28 November 2022. This site runs 7.4.33, the final release on that line.',
        cves: [] as string[],
      },
      {
        t: 'Vulnerabilities have been reported against PHP 7.4.33',
        d: 'Reported publicly against this exact version, the most serious rated high. They affect PHP 7.4.33 unless your host has backported the fixes — distribution packages often do, which makes this a question for your hosting provider rather than a conclusion about your site.',
        cves: ['CVE-2023-3824', 'CVE-2022-31626', 'CVE-2021-21703'],
      },
      {
        t: 'Certificate expires soon',
        d: '19 days remaining (expires 15.09.2026). The validity period suggests it is renewed by hand, so somebody has to remember.',
        cves: [] as string[],
      },
      {
        t: 'WordPress 6.4.3 is behind its own release line',
        d: 'The 6.4 line has since reached 6.4.5, which includes the security fixes released for it in the meantime.',
        cves: [] as string[],
      },
      { t: 'Server is slow to respond', d: 'First response took 1,840 ms.', cves: [] as string[] },
      {
        t: 'HSTS is not configured',
        d: 'Without it, a visitor typing the address can still be sent over plain HTTP first.',
        cves: [] as string[],
      },
    ],
    working: [
      'HTTPS is available and HTTP redirects to it',
      'Certificate chain is complete and trusted',
      'Session cookies carry the Secure and HttpOnly flags',
      'robots.txt and sitemap.xml are present',
      'No mixed content on the homepage',
    ],
    detected: ['WordPress 6.4.3', 'PHP 7.4.33', 'Nginx 1.18.0', 'Cloudflare'],
    cveNote: 'Every reference links to the public record at nvd.nist.gov, so you can check each claim yourself rather than take our word for it.',
    disclaimer: 'This is a public, non-intrusive website health assessment. Deeper security testing requires authorization.',
    by: 'Prepared by Viridian Grids',
  },

  problems: {
    label: 'Problems we watch for',
    title: 'What a broken website costs',
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
      'This is intentionally a small, focused service. There is no call centre and no ticket queue — the person who answers your email is the person who fixes the site, and already knows how it is put together. He was alerted before you noticed.',
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

  /*
    TODO before launch: `entity` must become the registered company name, ЕИК and
    registered address once the company exists, and all three documents need a
    lawyer's eye. They are written to be accurate about what this site actually
    does - no cookies, two forms, two processors - not to be legal advice.
  */
  legal: {
    entity: 'Viridian Grids · Sofia, Bulgaria',
    updated: 'Last updated: 27 August 2026',
    contactLine: 'Questions about any of this go to hello@viridiangrids.com and reach a person, not a ticket queue.',
    privacy: {
      label: 'Privacy',
      title: 'Privacy notice',
      intro:
        'What this website collects, why, and what you can ask us to do about it. It is short because we collect very little — there are two forms and nothing else.',
      sections: [
        {
          h: 'Who is responsible',
          p: [
            'Viridian Grids, based in Sofia, Bulgaria, decides how the data described below is used and is the controller for it under the GDPR.',
          ],
          list: [],
        },
        {
          h: 'What we collect',
          p: ['Only what you type into one of the two forms, plus the ordinary request logs any web server keeps.'],
          list: [
            'Free check form — the website address, your name, your email, and optionally your company. Used to run the check and send you the report.',
            'Contact form — company, website, name, email, optional phone, what you need, and your message. Used to answer you.',
            'Server logs — IP address, browser and requested page, kept briefly by our hosting provider to run and protect the site.',
          ],
        },
        {
          h: 'Why we are allowed to',
          p: [
            'Both forms are you asking us to do something, so the processing is necessary to take steps at your request before entering a contract. Server logs rest on our legitimate interest in keeping the site working and unabused. You are never required to give us anything — not filling in a form simply means we cannot reply.',
          ],
          list: [],
        },
        {
          h: 'No cookies, no analytics, no tracking',
          p: [
            'This site sets no cookies, runs no analytics, embeds no social widgets and loads no fonts or scripts from anyone else. Nothing about your visit is shared with an advertising network, because nothing about your visit is collected beyond the server log. That is why there is no cookie banner: there is nothing to consent to.',
          ],
          list: [],
        },
        {
          h: 'Who else sees it',
          p: ['Two service providers, both acting on our instructions and both bound by contract:'],
          list: [
            'Vercel — hosts this website and serves the two form endpoints.',
            'Our email provider — delivers the form submission to our inbox and carries our reply to you.',
            'Nobody else. Your details are never sold, rented, or passed to a marketing list.',
          ],
        },
        {
          h: 'How long we keep it',
          p: [
            'An enquiry that does not lead anywhere is deleted within 24 months. If you become a customer, we keep what the contract and Bulgarian accounting law require, and no longer. You can ask us to delete an enquiry sooner and we will.',
          ],
          list: [],
        },
        {
          h: 'What you can ask for',
          p: ['Under the GDPR you can ask us to:'],
          list: [
            'tell you what we hold about you, and give you a copy',
            'correct anything wrong',
            'delete it',
            'restrict or object to what we do with it',
            'hand it to you in a portable format',
          ],
        },
        {
          h: 'If you are unhappy',
          p: [
            'Tell us first — it is one person reading, and most things are fixed the same day. If that does not resolve it, you can complain to the Bulgarian Commission for Personal Data Protection (Комисия за защита на личните данни, cpdp.bg).',
          ],
          list: [],
        },
      ],
    },
    terms: {
      label: 'Terms',
      title: 'Terms of service',
      intro:
        'The standing terms for the monitoring and maintenance plans. A signed agreement governs the actual relationship; this page is what it says, in plain language, before you sign anything.',
      sections: [
        {
          h: 'What you get',
          p: [
            'The plan you choose, as described on the pricing page: continuous monitoring, and on Care and Business the maintenance, security hygiene and troubleshooting listed there. Monitoring works with any website. Full maintenance covers the platforms we list — if yours is unusual we say so before you pay, not after.',
          ],
          list: [],
        },
        {
          h: 'Price and billing',
          p: [
            'Prices are in euro and exclude VAT. Plans are billed monthly in advance. On an annual plan you pay for 10 months and use 12, and the price stays unchanged for the term. One-time onboarding is €49, waived for founding customers and on annual plans.',
          ],
          list: [],
        },
        {
          h: 'Work beyond the plan',
          p: [
            'Care includes 30 minutes and Business 60 minutes of troubleshooting per month. Unused minutes do not carry over. Anything beyond the allowance is €20 per hour. For a larger job we first describe in writing what it involves and how long it will take, and agree it with you before the work starts. You will never receive an invoice for work you did not approve.',
          ],
          list: [],
        },
        {
          h: 'Access, and what stays yours',
          p: [
            'You give us the access we need, we ask for the least that does the job, and we document it in writing beforehand. Your hosting, domain and accounts remain yours and in your name throughout — we never take ownership of them. Your website, its content and its data are yours.',
          ],
          list: [],
        },
        {
          h: 'What we do not promise',
          p: [
            'We do not guarantee that your website cannot be compromised, and no honest provider does. Monitoring and maintenance reduce risk by closing the common ways in; they do not eliminate it. We also do not control your hosting provider, your domain registrar or your internet connection, and we cannot guarantee their uptime. What we commit to are the response times published on the pricing page.',
          ],
          list: [],
        },
        {
          h: 'Ending it',
          p: [
            'Either side can end the agreement with 30 days written notice, at the end of a monthly period. On termination we remove our accounts, hand back any credentials we hold and confirm in writing within 5 working days.',
          ],
          list: [],
        },
        {
          h: 'Liability and law',
          p: [
            'Our liability in any 12-month period is limited to the fees you paid us over the preceding three months, except where the law does not allow that limit. Bulgarian law applies.',
          ],
          list: [],
        },
      ],
    },
    dpa: {
      label: 'Data processing',
      title: 'Data processing agreement',
      intro:
        'When we monitor and maintain your website we may touch personal data belonging to your customers. This page sets out how. The signed DPA is part of the onboarding paperwork — ask and we will send it before you commit to anything.',
      sections: [
        {
          h: 'Which of us is which',
          p: [
            'For the data on your website, you are the controller and we are the processor: we act only on your documented instructions and never use your data for our own purposes.',
          ],
          list: [],
        },
        {
          h: 'What we may come into contact with',
          p: [
            'We do not go looking for your customer data, but maintaining a website means being able to reach it. In practice that can include:',
          ],
          list: [
            'contact form submissions and enquiries stored in your site',
            'customer accounts, orders and addresses on an ecommerce site',
            'names and email addresses in your CMS user list',
            'anything visible in a database backup',
          ],
        },
        {
          h: 'Sub-processors',
          p: ['We use a small number, and we tell you before adding one:'],
          list: [
            'Our VPS provider, for the monitoring infrastructure — EU region.',
            'Our backup storage provider — encrypted at rest, EU region, separate from your hosting.',
            'Your own hosting provider remains yours; we do not sit between you and them.',
          ],
        },
        {
          h: 'How it is protected',
          p: [
            'Least-privilege accounts rather than shared logins. All credentials in an encrypted password manager with two-factor authentication — never in email, chat or a spreadsheet. Backups encrypted at rest and stored in the EU. Access over encrypted connections only. Anything beyond passive checking — active security testing — happens only with your written authorisation.',
          ],
          list: [],
        },
        {
          h: 'When it ends',
          p: [
            'On termination we delete our copies and remove our accounts, and confirm both in writing within 5 working days. Backups age out on their normal retention schedule and are not kept beyond it.',
          ],
          list: [],
        },
        {
          h: 'If something goes wrong',
          p: [
            'If we become aware of a personal data breach affecting your data, we tell you without undue delay and with what we know at the time — not after we have finished investigating. You are the one with the reporting obligation, so you need the facts early rather than tidily.',
          ],
          list: [],
        },
      ],
    },
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
