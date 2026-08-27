Yes. Based on everything we discussed, I would structure this as a service-first monitoring business that gradually becomes a platform.

The key constraint is: do not spend months building software before validating sales. Your first MVP exists to help you acquire and service the first 5–10 paying customers.

Bulgaria is a reasonable market for this because SME digitalisation remains relatively weak and cybersecurity maturity is uneven, while connectivity is strong. That creates room for a simple managed service aimed at businesses that do not want an internal IT/security team.

Stage 0 — Define the first business

Start with one clear offer:

Managed Website Monitoring & Care for SMEs

Not “cybersecurity consultancy.”
Not “DevOps.”
Not “digital transformation.”
Not “IoT.”

Those can come later.

Your initial promise should be something like:

We continuously monitor your website, keep it updated and backed up, and help when something breaks.

Your initial customer profile should be businesses where the website actually matters:

hotels and guest houses
clinics/dentists
accountants/law firms
real-estate agencies
small ecommerce stores
restaurants with booking/order systems
service businesses receiving leads through forms
small manufacturers with catalogue/contact websites
local companies running WordPress

Avoid hobby sites and businesses where the owner fundamentally does not care whether the website works.

Stage 1 — MVP offer

I'd launch with three simple plans.

Plan	Approx. price	Purpose
Monitor	€25–29/mo	Entry product
Care	€49–59/mo	Main product
Business	€89–109/mo	Business-critical sites
Monitor — €29/month

Include:

uptime monitoring
SSL expiry monitoring
DNS/HTTP availability
response-time monitoring
basic security-header monitoring
monthly report
notification if a major problem is detected

No included repair work.

That's important.

If something breaks:

€X/hour or fixed quote to repair.

This package should be nearly fully automated.

Care — €59/month

This should probably become your most popular package.

Include:

everything in Monitor
WordPress/core/plugin/theme updates
backup monitoring
backup verification
basic security checks
basic performance monitoring
30 minutes/month troubleshooting
monthly report

Additional work billed separately.

Business — €99/month

Target ecommerce, booking systems and more important sites.

Include:

everything in Care
more frequent checks
checkout/form monitoring
priority response
60 minutes/month troubleshooting
database/server monitoring where possible
staging/testing before risky updates
more detailed monthly report

Don't promise 24/7 human incident response at €99.

Stage 2 — Build only the technical MVP you need

You do not need your future monitoring platform yet.

I'd start with approximately:

Docker Compose
│
├── Uptime Kuma
├── Prometheus
├── Blackbox Exporter
├── Grafana
├── Alertmanager
├── Loki
├── PostgreSQL
└── your small internal app

Then:

MainWP
Ansible
Restic
WireGuard

where appropriate.

What each piece does

Uptime Kuma
Simple external uptime checks.

Prometheus
Metrics collection.

Blackbox Exporter
HTTP/TCP/SSL probing.

Grafana
Your operational dashboards.

Alertmanager
Internal alert routing.

Loki
Logs if/when you need them.

MainWP
Central WordPress administration.

Ansible
Repeatable updates/configuration.

Restic
Backups where you're responsible for them.

Don't introduce Kubernetes.

You can run quite a significant initial business from 1–3 well-managed VPSs.

Stage 3 — Build the prospect scanner

This is where I'd write some software yourself, but not the scanning engines.

Your scanner is essentially an aggregator.

            Domain
               ↓
        Scanner service
               ↓
  ┌────────────┼────────────┐
  ↓            ↓            ↓
 HTTP      testssl.sh      ZAP
 checks       TLS        passive
  ↓            ↓            ↓
  └────────────┼────────────┘
               ↓
         normalize data
               ↓
          score findings
               ↓
        generate report

For unsolicited prospects, keep it non-intrusive. OWASP ZAP's passive scanner analyzes traffic without modifying messages, while ZAP explicitly describes active scanning as an attack and says it should not be used against applications you don't own.

Your public scanner should check

Things such as:

Availability

HTTP status
HTTPS
redirects
response time

TLS

certificate validity
expiration
protocol configuration
obvious TLS weaknesses

HTTP

HSTS
CSP
X-Content-Type-Options
Referrer-Policy
Permissions-Policy

Cookies

Secure
HttpOnly
SameSite

Technology

obvious CMS
server headers
exposed technology information

Configuration

www/non-www behaviour
HTTP→HTTPS
obvious redirect loops
favicon/robots/sitemap availability

Performance

initial request latency
page-size estimates where appropriate
Don't initially scan

Without authorization, don't make your sales workflow depend on:

password attacks
fuzzing
SQLi testing
XSS attacks
directory brute forcing
aggressive crawling
exploit attempts
authenticated scanning
intrusive port scanning

Once they're a customer and give you explicit authorization, you can offer deeper assessment.

Stage 4 — Make the scanner produce a sales report

This is more important than building a fancy dashboard.

The result should be one page.

For example:

example.bg Website Health Check

Overall: 74/100

✅ HTTPS configured
✅ Certificate valid
✅ HTTP redirect working

⚠ CSP missing
⚠ HSTS missing
⚠ Server technology exposed
⚠ Initial response: 2.6 seconds
⚠ Certificate expires in 38 days

Then:

This is a public, non-intrusive website health assessment. Deeper security testing requires authorization.

That's professional and avoids claiming things you haven't actually demonstrated.

Also: don't make the scoring overly dramatic.

Avoid:

CRITICAL SECURITY RISK!!!! 38/100!!!

for a missing header.

You need prospects to trust you.

Stage 5 — Your own website

Your website doesn't need to be huge.

I'd start with:

Homepage

Simple headline:

Your website should work when your customers need it.

Subheadline:

Monitoring, updates, backups and troubleshooting for Bulgarian businesses.

Primary CTA:

Check my website

Secondary:

See plans

Pricing

Show the three packages.

Don't hide all prices behind “contact us.”

SMEs generally appreciate knowing approximately what they're getting into.

Free Website Check

This could become your biggest acquisition feature.

User enters:

website URL
name
email
company

You scan it and produce either:

instant basic result
or report emailed after review

Initially I would manually review reports before sending them.

That prevents embarrassing false positives.

How it works

Something like:

1. We check your website
2. We set up monitoring
3. We handle maintenance
4. You receive monthly reports
Security / FAQ

Explain clearly:

what you monitor
where credentials are stored
what you don't do without permission
backups
GDPR basics
cancellation
response expectations

This increases trust enormously.

Stage 6 — Do NOT automate onboarding initially

Your first onboarding process can be hilariously simple.

Customer subscribes.

You send them an onboarding form.

Collect:

Domain
CMS
Hosting provider
Business contact
Technical contact
WordPress access
Hosting access if required
Backup setup
Notification preference

Then you configure everything yourself.

Don't build:

self-service agent installation
automatic tenant creation
automated billing provisioning
customer API
complex RBAC
SaaS provisioning

yet.

Do it 10–20 times manually.

Then you'll know exactly what deserves automation.

Stage 7 — Get the first 100 prospects

This is where I'd spend more time than coding.

Build a spreadsheet or basic CRM.

Columns:

Company
Domain
Industry
City
Email
Phone
Decision maker
Website platform
Scan score
Interesting finding
Contacted
Follow-up 1
Follow-up 2
Response
Meeting
Trial
Customer
MRR
Notes

Then deliberately find companies.

Initially perhaps:

30 hotels/guest houses
20 dentists/clinics
20 professional-services businesses
20 ecommerce sites
10 random SMEs

Now you can see which vertical responds.

Don't assume hotels are best.

Let conversion data tell you.

Stage 8 — How to choose who to contact

Your scanner becomes useful here.

Instead of contacting random companies, rank them.

For example:

+3 WordPress
+3 WooCommerce
+2 slow response
+2 missing important headers
+2 outdated-looking site
+2 business-critical form
+2 booking/ecommerce
+1 local Bulgarian SME

Now your system says:

Prospect score: 14/15

That company deserves personalized outreach.

Meanwhile:

static 3-page brochure site
perfect TLS
fast
doesn't sell anything online

might not be worth spending 15 minutes contacting.

Stage 9 — Cold email strategy

Do small-volume personalized outreach initially.

Not:

Dear Sir/Madam, we are an innovative cybersecurity company offering comprehensive...

I'd immediately delete that.

Instead:

Subject: website check for company.bg

Then something short:

Hi Ivan,

I came across company.bg and ran a basic public website health check.

I noticed the site is working, but HSTS/CSP aren't configured and initial response time was around 2.4 seconds.

I'm launching a managed monitoring service for Bulgarian SMEs that watches uptime, certificates, updates and backups and handles problems when needed.

I can send you the short report if useful.

That's it.

No giant sales pitch.

Your objective is:

start conversation → not close subscription in email #1.

Stage 10 — Follow-up

Most replies will come from follow-ups.

I would probably do:

Day 0

Initial email.

Day 3–4

Short follow-up.

Just checking whether you'd like me to send over the website health report.

Day 8–10

Provide one useful finding.

One additional thing I noticed: the certificate currently has X days remaining. Not urgent, but this is exactly the type of thing the monitoring catches automatically.

Day 18–21

Close it.

I'll leave this here rather than keep bothering you. If you'd ever like monitoring/maintenance for the site, feel free to reach out.

Then stop.

Don't become spam.

Stage 11 — Calls can be surprisingly effective

For Bulgarian SMEs, I would absolutely experiment with calling.

Email may go to:

info@
office@
contact@

and disappear.

But many small companies have a phone number publicly listed.

Something simple:

Здравейте, казвам се X. Занимавам се с мониторинг и поддръжка на бизнес сайтове. Попаднах на сайта ви и направих кратка публична проверка — има няколко неща, които бих могъл да ви изпратя безплатно. С кого е най-добре да говоря за сайта?

You aren't trying to close them immediately.

You want the responsible person.

Stage 12 — Facebook groups

Yes, but don't spam advertisements.

Bad:

🔥🔥 WEBSITE SECURITY ONLY €29!!! 🔥🔥

Better:

Проверих 50 сайта на малки фирми през последната седмица. Най-честите проблеми бяха изтичащи сертификати, липса на външен uptime monitoring, бавен hosting и WordPress updates.

Ако някой иска, мога да направя кратка публична проверка на сайта му.

That's useful content.

Then people volunteer their domains.

That's far better lead generation.

Stage 13 — LinkedIn

I would use LinkedIn for slightly larger companies.

Post mini case studies.

For example:

A website can look perfectly healthy while its contact form has stopped delivering email.

That's why uptime monitoring alone isn't enough.

Then explain how you test it.

You're building credibility rather than shouting about your €59 package.

Stage 14 — Partnerships may become your best channel

This is potentially much bigger than cold outreach.

Contact:

Web designers

They build the site but don't want long-term support.

Offer:

You build it. I'll maintain it.

Marketing agencies

They need client websites functioning.

Offer white-label maintenance.

Freelance developers

They often hate ongoing WordPress support.

Hosting providers

Potential referral relationship.

ERP implementers

Later, when you add infrastructure.

IT support companies

They might not specialize in websites/DevOps.

Potential cross-referrals.

Imagine one web studio sends you:

20 sites × €49/month = €980 MRR.

That's better than acquiring 20 companies individually.

Stage 15 — Ads come later

Do not start by throwing money at Meta ads.

You first need to discover:

which customer

which problem

which wording

=

conversion

Once you know that:

Google Ads

Could make sense for high-intent terms around:

WordPress maintenance
website maintenance
hacked WordPress
website support
WordPress support

These users already want something.

Facebook/Instagram

Could eventually promote:

Free Website Health Check

rather than:

Subscribe to website monitoring.

Lead magnet first.

Stage 16 — First validation milestone

Do not evaluate the business after sending 20 emails.

My first target would be something like:

250 carefully selected prospects

From that I'd hope for perhaps:

250 prospects
↓
150 actually contacted
↓
20–40 responses/conversations
↓
10–15 serious discussions
↓
3–8 paying customers

Don't treat those exact numbers as guaranteed benchmarks.

You're looking for signal.

If you contact 250 targeted SMEs and nobody will pay €29–59/month, something is wrong with:

target audience
pain
positioning
credibility
pricing
sales approach

Better to discover that before building SaaS.

Stage 17 — First financial milestone

I'd target:

10 customers / €500–800 MRR

At that point don't celebrate by rebuilding your backend.

Instead ask:

What takes most of my time?

Maybe it is:

WordPress updates
reports
onboarding
alerts
billing
credential management

Automate whichever one hurts.

Stage 18 — At 20–30 customers

Now I'd start building your internal platform seriously.

Something like:

                 Web UI
                    ↓
                API/backend
                    ↓
               PostgreSQL
                    ↓
         ┌──────────┴──────────┐
         ↓                     ↓
    Customer config        Job system
                               ↓
                          scan workers
                               ↓
           ┌───────────────────┼──────────────┐
           ↓                   ↓              ↓
       HTTP checks         testssl         passive checks

Your system now manages:

tenants
domains
subscriptions
scan history
monitoring configuration
findings
reports
tickets
alert routing
Stage 19 — Don't immediately replace Grafana

Your custom application doesn't need to become another Grafana.

Keep using good open-source components.

Your platform can become the control plane.

For example:

Your application
      ↓
Customer
sites
plans
billing
configuration
reports
permissions
      ↓
--------------------------------
Underlying infrastructure
--------------------------------
Prometheus
Grafana
Zabbix
Loki
Alertmanager
MainWP
Ansible

That's much faster than rewriting everything.

Stage 20 — Move into server monitoring

When customers start asking:

Can you also monitor our VPS?

Say yes.

Then introduce something like:

Infrastructure Care — €199–399/month

Monitor:

Linux
Windows where appropriate
CPU
RAM
disks
databases
Docker
backups
NAS
VPN
router
internet
UPS

Now your existing €59 customer can become €299.

That's where economics improve substantially.

Stage 21 — Add Zabbix

Once you have more traditional infrastructure, I'd introduce Zabbix.

This makes it easier to handle:

servers
SNMP
switches
routers
UPS
printers
NAS
IPMI
VMware
physical equipment

Your architecture evolves:

Web → Blackbox/Prometheus
Servers → Prometheus/Zabbix
Network → Zabbix
Logs → Loki
Visualization → Grafana
Stage 22 — IoT

Only when real customers create the need.

Introduce:

Mosquitto
Node-RED
Telegraf
ESPHome where appropriate
VictoriaMetrics
Grafana

Then offer:

Facility Monitoring

For example:

€300 setup + €99/month

for:

server-room temperature
leak detector
UPS
Internet
freezer temperature

Then expand.

Stage 23 — Commercial property

This is where I would go before mass consumer smart homes.

Think:

hotel

warehouse

restaurant

office

Airbnb portfolio

guest house

instead of one apartment owner paying €9.99/month.

Monitor:

internet
UPS
temperature
humidity
water
freezers
boilers
HVAC
cameras/NVR
access systems

Now you're protecting business operations.

Stage 24 — Industrial

This is much later.

By then you may add:

Modbus
RS485
OPC-UA
PLC integrations
industrial gateways
power meters
vibration
machine runtime
counters

Then you've evolved from:

website maintenance company

to:

managed monitoring company

without making a giant speculative leap.

The long-term architecture

Eventually I could see your company looking something like:

                         YOUR PLATFORM
                              │
               ┌──────────────┼──────────────┐
               │              │              │
           Monitoring      Automation      Support
               │              │              │
       ┌───────┼──────┐       │              │
       ↓       ↓      ↓       ↓              ↓
      Web    Servers Network  Ansible      Tickets
       │       │      │
       │       │      │
       └───────┼──────┘
               ↓
              IoT
               ↓
           Facilities
               ↓
            Industry

That is a coherent company.

What I would build in the first 30 days
Week 1

Business:

choose name
buy domain
basic branding
define €29 / €59 / €99 packages
define terms of service
define exactly what is/not included

Technology:

VPS
Docker
Uptime Kuma
Prometheus
Grafana
Blackbox Exporter
Alertmanager
Week 2

Build:

scanner CLI/API
HTTP checks
testssl integration
passive ZAP integration if useful
normalized JSON result
basic scoring algorithm
Week 3

Build website:

homepage
pricing
free website check
FAQ/security
contact
basic privacy/GDPR setup

Create:

branded 1-page report
onboarding form
customer spreadsheet/CRM
Week 4

Stop building.

Start prospecting.

Seriously.

Days 30–60

Target:

10 new prospects every working day.

That gives:

~200/month.

For each:

find company
↓
scan website
↓
manually inspect results
↓
identify one useful observation
↓
contact
↓
record result

Also:

contact 10–20 web agencies/freelancers
post educational content in relevant groups
contact your existing network
try direct calls
offer 3–5 early adopter slots
Your early-adopter offer

I'd consider:

First 3 months: €39/month
Normal Care price: €59/month

Not lifetime discount.

You don't want:

“€19 forever because you were customer #2.”

You can instead say:

Founding customers receive free onboarding and their first three months discounted.

That creates urgency without permanently damaging pricing.

Months 3–6

Objective:

10–20 paying customers

Now review your numbers:

MRR
average customer revenue
hours per customer
customer acquisition source
response rate
meeting rate
trial conversion
cancellations
support tickets
incidents

Especially track:

Revenue per support hour

A €59 customer consuming 15 minutes/month is excellent.

A €29 customer consuming 3 hours/month is disastrous.

This is why measurement matters.

Months 6–12

If website maintenance is working:

Target:

30–50 websites

Potential MRR:

Perhaps around €2k–4k, depending on package mix.

Then add your first infrastructure offering.

You now have existing customers to whom you can say:

We're already monitoring your website. Would you like us to monitor the server and backups too?

Much easier than selling infrastructure cold.

One metric I'd obsess over

Not website traffic.

Not number of scans.

Not number of Grafana dashboards.

MRR per customer versus support time.

Something like:

Customer A
€59 MRR
8 minutes support
excellent

Customer B
€99 MRR
35 minutes
good

Customer C
€29 MRR
3.5 hours
problem

Then improve your product around that.

One thing I'd avoid

Don't market yourself primarily as “security.”

If you advertise:

We secure your website.

customers may reasonably assume significant cybersecurity responsibility.

I'd position it more conservatively:

Monitoring, maintenance and website security hygiene.

Then sell deeper security separately with a clear scope.

What makes this potentially scalable

Initially:

Revenue = your time

But gradually:

monitoring → automated
reports → automated
updates → mostly automated
onboarding → automated
billing → automated
alerts → automated
scanner → automated

Eventually one engineer might support hundreds of relatively simple sites, while higher-value infrastructure customers get more human involvement.

That's the transition you're looking for:

Freelancer
    ↓
Managed service
    ↓
Standardized managed service
    ↓
Platform-enabled service
    ↓
Monitoring platform

And importantly, you get paid through almost every stage instead of spending two years building before knowing whether anyone cares.

One final strategic point: Bulgaria adopted the euro on 1 January 2026, so I'd price and invoice publicly in euros from the beginning rather than designing the new business around lev-denominated packages.

If you execute this, I'd consider your true MVP complete the moment you have the website + safe scanner + monitoring stack + onboarding process + billing + first real prospect list. Everything beyond that should increasingly be driven by what those prospects and customers actually need.

The business idea is a subscription-based managed monitoring and maintenance service for SMEs, starting with websites and gradually expanding into servers, networks, physical infrastructure, IoT, facilities, and eventually industrial monitoring.

The initial product is simple: help small businesses keep their websites online, updated, backed up, secure, and monitored without needing an internal IT person. Customers pay a monthly fee for uptime monitoring, SSL/domain checks, WordPress updates, backups, basic security hygiene, performance monitoring, reports, and troubleshooting.

The business starts service-first rather than SaaS-first. Existing open-source tools such as Grafana, Prometheus, Blackbox Exporter, Uptime Kuma, Alertmanager, MainWP, Ansible, Restic, and later Zabbix provide most of the technical functionality. A small custom backend is built only where necessary, initially to aggregate website scans, generate reports, manage prospects, and eventually manage customers and monitoring configuration.

Customer acquisition begins with a public, non-intrusive website health scanner. Potential customers are identified, their publicly accessible websites are checked for measurable issues such as SSL configuration, response time, missing security headers, redirects, availability, and obvious configuration problems. These findings are used to create short personalized reports and highly targeted cold outreach instead of generic sales emails.

The initial pricing is aimed at Bulgarian SMEs, with entry-level plans around €29/month, a core website-care package around €59/month, and a business-critical package around €99/month. Cheap tiers remain highly automated, while troubleshooting beyond the included allowance is billed separately.

The first goal is not to build a sophisticated platform. It is to acquire roughly 5–10 paying customers, deliver the service partly manually, and identify which tasks repeat. Those repetitive processes are then automated. As customer numbers increase, the custom backend gradually becomes a proper control plane for customer accounts, monitoring, reports, alerts, billing, onboarding, and integrations.

The expansion path is:

Website Monitoring
        ↓
Website Maintenance & Security Hygiene
        ↓
Server / VPS Monitoring
        ↓
Networks / NAS / Routers / UPS
        ↓
Business Hardware Monitoring
        ↓
IoT / Facility Monitoring
        ↓
Hotels / Warehouses / Commercial Properties
        ↓
Industrial Monitoring
        ↓
Machines / PLC / Modbus / OPC-UA

The same underlying concept remains throughout the business:

System / Device
      ↓
Collect metrics/events
      ↓
Store and analyze
      ↓
Detect problems
      ↓
Alert
      ↓
Troubleshoot / automate
      ↓
Report to customer

The long-term vision is to evolve from a small website-monitoring company into a managed operations and monitoring platform for SMEs and industrial businesses.

Instead of competing as a generic web agency or IT freelancer, the company sells one clear outcome:

We monitor the systems your business depends on and help keep them running.

The scalable advantage comes from building one reusable monitoring and automation platform underneath many services. Early revenue comes from website subscriptions; larger future revenue comes from infrastructure, facilities, IoT, and industrial customers.

In short, the business model is:

start narrow → sell early → deliver manually → automate repetition → expand into adjacent infrastructure → productize the platform → scale recurring revenue.