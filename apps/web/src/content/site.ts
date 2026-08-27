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

/** Published rates. Both are still marked "to decide" in docs/offer-and-pricing.md. */
export const rates = {
  hourly: 45,
  setup: 90,
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
  | 'contact';

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
  home: ['hero', 'band', 'monitor', 'how', 'pricing', 'sla', 'report', 'problems', 'trust', 'faq', 'final'],
  check: ['check', 'final'],
  pricing: ['pricing', 'sla', 'faq', 'final'],
  services: ['services', 'problems', 'final'],
  how: ['how', 'pricing', 'sla', 'final'],
  report: ['report', 'final'],
  security: ['trust', 'faq', 'final'],
  faq: ['faq', 'final'],
  about: ['about', 'final'],
  contact: ['contact'],
};

export function shows(page: PageId, section: string): boolean {
  return SECTIONS[page].includes(section);
}
