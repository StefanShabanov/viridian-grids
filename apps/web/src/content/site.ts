/**
 * Everything about the business that is a number or a fact, in one place.
 *
 * Prices, allowances and response times are duplicated in `docs/offer-and-pricing.md`.
 * They are in the same repository for exactly this reason: if one changes, both change
 * in the same commit. If you edit a number here, edit it there too.
 */

export const LANGS = ['bg', 'en'] as const;
export type Lang = (typeof LANGS)[number];
export const DEFAULT_LANG: Lang = 'bg';

export const site = {
  name: 'Viridian Grids',
  email: 'hello@viridiangrids.com',
  city: 'Sofia, BG',
  year: 2026,
} as const;

/** Plan prices. EUR only - Bulgaria adopted the euro on 2026-01-01. */
export const plans = [
  { id: 'monitor', price: 29, featured: false },
  { id: 'care', price: 59, featured: true },
  { id: 'business', price: 99, featured: false },
] as const;

/** Published rates and terms. Mirrored in docs/offer-and-pricing.md - change both. */
export const rates = {
  hourly: 30,
  setup: 49,
  /** Annual plans: pay for this many months, use twelve. */
  annualMonths: 10,
} as const;

/** The pages, and which sections each one shows - mirrors the design's show* flags. */
export type PageId =
  | 'home'
  | 'check'
  | 'pricing'
  | 'services'
  | 'how'
  | 'report'
  | 'security'
  | 'faq'
  | 'about'
  | 'contact'
  | 'privacy'
  | 'terms'
  | 'dpa'
  | 'methodology';

export const PAGES: PageId[] = [
  'home',
  'check',
  'pricing',
  'services',
  'how',
  'report',
  'security',
  'faq',
  'about',
  'contact',
  'privacy',
  'terms',
  'dpa',
  'methodology',
];

/** Slug per language. Bulgarian slugs for the Bulgarian site; `/en/` prefix for English. */
const SLUGS: Record<Lang, Record<PageId, string>> = {
  bg: {
    home: '',
    check: 'proverka',
    pricing: 'ceni',
    services: 'uslugi',
    how: 'kak-raboti',
    report: 'otchet',
    security: 'sigurnost',
    faq: 'vaprosi',
    about: 'za-nas',
    contact: 'kontakt',
    privacy: 'poveritelnost',
    terms: 'usloviya',
    dpa: 'obrabotvane-na-danni',
    methodology: 'metodologiya',
  },
  en: {
    home: '',
    check: 'check',
    pricing: 'pricing',
    services: 'services',
    how: 'how-it-works',
    report: 'sample-report',
    security: 'security',
    faq: 'faq',
    about: 'about',
    contact: 'contact',
    privacy: 'privacy',
    terms: 'terms',
    dpa: 'data-processing',
    methodology: 'methodology',
  },
};

/** Absolute path for a page in a language. */
export function href(lang: Lang, page: PageId): string {
  const prefix = lang === DEFAULT_LANG ? '' : `/${lang}`;
  const slug = SLUGS[lang][page];
  return slug ? `${prefix}/${slug}` : prefix || '/';
}

/** The `[...path]` param for a page, or undefined for a language's home page. */
export function param(lang: Lang, page: PageId): string | undefined {
  const path = href(lang, page).replace(/^\//, '');
  return path || undefined;
}

/**
 * Which sections appear on which page. Taken verbatim from the design, which puts
 * the whole story on the home page and lets the nav deep-link into slices of it.
 */
export const SECTIONS: Record<PageId, string[]> = {
  // Homepage sells; the dedicated pages prove. Report and trust run compact here
  // and link through, so the main sales page stays quick to scan.
  home: ['hero', 'proof', 'band', 'flows', 'monitor', 'how', 'pricing', 'sla', 'report', 'problems', 'trust', 'faq', 'final'],
  check: ['check', 'proof', 'final'],
  pricing: ['pricing', 'sla', 'faq', 'final'],
  services: ['services', 'modernize', 'flows', 'problems', 'final'],
  how: ['how', 'pricing', 'sla', 'final'],
  report: ['initial', 'report', 'final'],
  security: ['trust', 'faq', 'final'],
  faq: ['faq', 'final'],
  about: ['about', 'final'],
  contact: ['contact'],
  privacy: ['legal:privacy', 'final'],
  terms: ['legal:terms', 'final'],
  dpa: ['legal:dpa', 'final'],
  methodology: ['legal:methodology', 'final'],
};

/** The three legal pages share one component; this says which document to render. */
/** Pages rendered by the shared long-form document component. */
export const DOC_PAGES = ['privacy', 'terms', 'dpa', 'methodology'] as const;
export type DocId = (typeof DOC_PAGES)[number];

export function docId(page: PageId): DocId | null {
  return (DOC_PAGES as readonly string[]).includes(page) ? (page as DocId) : null;
}

export function shows(page: PageId, section: string): boolean {
  return SECTIONS[page].includes(section);
}
