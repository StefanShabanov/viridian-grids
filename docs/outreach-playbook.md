# Outreach playbook

Objective of every first touch: **start a conversation.** Not close a subscription in email #1.

Rule: outreach volume is small and personalized. The scanner exists so that every message contains
one specific, true, useful observation about *that* company's site.

## Translate the finding into their business

A dentist does not know what Divi 4.19.5 is and does not want to. Every email leads with what the
finding costs them; the finding itself is the evidence that earns the right to say it.

| What the scanner found | What it means to the business |
|---|---|
| Certificate expires in N days | Browsers will show "Not secure" and patients stop booking — with a date on it |
| HTTP does not redirect to HTTPS | Visitors on the plain address already see "Not secure" in the address bar |
| Old CMS / theme version | The contact form quietly stops delivering, or the site breaks when the host upgrades PHP |
| Site is slow to respond | Visitors leave before the page appears; Google notices too |
| www and non-www both serve | Google sees two competing sites and splits the ranking between them |
| Site blocked our request | Nothing. Do not send this report at all |
| Missing HSTS / CSP / headers | **Nothing.** 78-89% of Bulgarian SME sites are missing these. Never lead with them |

The last row matters most. Across the first 18 sites scanned, every security header finding appeared
on four sites in five. Leading with one tells the recipient nothing about themselves, and they can
tell. Use the Mozilla Observatory grade as a *supporting* line instead - an independent tool grading
their site D carries weight that our own opinion does not.

**Never claim what was not tested.** "Формата ви не работи" is a claim we cannot support and cannot
recover from if they check and it works. "В такива случаи най-често" marks it as inference, which is
what it is.

## Email

Subject: `website check for company.bg`

```
Hi Ivan,

I came across company.bg and ran a basic public website health check.

I noticed the site is working, but HSTS/CSP aren't configured and initial response
time was around 2.4 seconds.

I'm launching a managed monitoring service for Bulgarian SMEs that watches uptime,
certificates, updates and backups and handles problems when needed.

I can send you the short report if useful.
```

That's it. Never: *"Dear Sir/Madam, we are an innovative cybersecurity company offering
comprehensive…"* — that gets deleted.

### Bulgarian templates

Lead with a question about their business - even a one-line "everything is fine" is a reply, and a
reply is the objective.

**Outdated CMS or theme**

> Здравейте,
>
> Бърз въпрос: получавате ли редовно запитвания през формата на сайта?
>
> Питам, защото направих кратка публична проверка на company.bg. Сайтът работи и се зарежда бързо,
> но темата и WordPress са от няколко години назад.
>
> В такива случаи най-често се случва едно от двете: формата спира да изпраща имейли без никакъв
> видим признак, или сайтът се чупи, когато хостингът обнови PHP. И в двата случая се забелязва
> седмици по-късно — по това, че телефонът звъни по-малко.
>
> Занимавам се с наблюдение и поддръжка на сайтове на малки фирми: следя дали сайтът работи, дали
> формите стигат до вас, правя обновленията и архивите.
>
> Ако искате, мога да ви изпратя краткия отчет — без ангажимент.

**Certificate expiring** (the sharpest opener: a date, a visible consequence, a deadline)

> Здравейте,
>
> Сертификатът на company.bg изтича на 27 септември.
>
> Ако не се поднови навреме, браузърите показват предупреждение „Сайтът не е сигурен" и посетителите
> спират да записват часове. Обикновено се случва през уикенда, когато никой не гледа.
>
> Възможно е да се подновява автоматично — затова питам, вместо да предполагам.
>
> Занимавам се с наблюдение на сайтове на малки фирми: следя точно такива неща, за да не се разберат
> постфактум.

> **Bulgarian in this file has not been reviewed by a native speaker.** Do that before the first send.

## Follow-up sequence

| When | What |
|---|---|
| Day 0 | Initial email |
| Day 3–4 | Short nudge: *"Just checking whether you'd like me to send over the website health report."* |
| Day 8–10 | One more useful finding: *"The certificate currently has X days remaining. Not urgent, but this is exactly the type of thing the monitoring catches automatically."* |
| Day 18–21 | Close it out: *"I'll leave this here rather than keep bothering you. If you'd ever like monitoring/maintenance for the site, feel free to reach out."* |

Then **stop**. Most replies come from follow-ups; none come from becoming spam.

## Calling

Often more effective than email for Bulgarian SMEs — `info@`/`office@` inboxes swallow messages,
but the phone number is published. The goal of the call is to find the responsible person, not to close.

> Здравейте, казвам се X. Занимавам се с мониторинг и поддръжка на бизнес сайтове. Попаднах на
> сайта ви и направих кратка публична проверка — има няколко неща, които бих могъл да ви изпратя
> безплатно. С кого е най-добре да говоря за сайта?

## Facebook groups

Post useful content, never ads. No `🔥🔥 WEBSITE SECURITY ONLY €29!!! 🔥🔥`.

> Проверих 50 сайта на малки фирми през последната седмица. Най-честите проблеми бяха изтичащи
> сертификати, липса на външен uptime monitoring, бавен hosting и WordPress updates.
>
> Ако някой иска, мога да направя кратка публична проверка на сайта му.

People then volunteer their own domains. Far better lead generation than advertising.

## LinkedIn

For slightly larger companies. Post mini case studies that build credibility rather than shouting
about the €59 package. E.g. *"A website can look perfectly healthy while its contact form has stopped
delivering email — that's why uptime monitoring alone isn't enough"*, then explain how it's tested.

## Partnerships — potentially the best channel

One web studio sending 20 sites at €49/mo = €980 MRR. Better than acquiring 20 companies individually.

| Partner | Pitch |
|---|---|
| Web designers | "You build it. I'll maintain it." |
| Marketing agencies | White-label maintenance so client sites keep working |
| Freelance developers | Take the ongoing WordPress support they hate off their hands |
| Hosting providers | Referral relationship |
| IT support companies | Cross-referral — they often don't do websites/DevOps |
| ERP implementers | Later, once infrastructure monitoring exists |

Target: contact 10–20 agencies/freelancers in the first 60 days.

## Ads — later

Do not start by spending on Meta ads. First discover which customer + which problem + which wording
converts. Then:

- **Google Ads** for high intent: "WordPress maintenance", "website maintenance", "hacked WordPress",
  "website support", "WordPress support".
- **Facebook/Instagram** to promote the **Free Website Health Check**, never "subscribe to monitoring".
  Lead magnet first.

## Language

All prospect-facing material needs a Bulgarian version: email templates, call script, report,
website copy. Internal docs stay English.
