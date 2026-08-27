import { bg } from './bg';
import { en, type Copy } from './en';
import type { Lang } from './site';

export const copy: Record<Lang, Copy> = { bg, en };
export type { Copy };
export * from './site';
