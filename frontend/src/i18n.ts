// Can be imported from a shared config
export const locales = ['en', 'zh', 'es', 'fr', 'de', 'ja'] as const;
export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = 'en';

export const localeNames: Record<Locale, string> = {
  en: 'English',
  zh: '中文',
  es: 'Español',
  fr: 'Français',
  de: 'Deutsch',
  ja: '日本語',
};

export async function getMessages(locale: string) {
  try {
    return (await import(`../messages/${locale}.json`)).default;
  } catch {
    return (await import(`../messages/en.json`)).default;
  }
}

// Client-side locale utilities
export function getLocaleFromCookie(): Locale {
  if (typeof window === 'undefined') return defaultLocale;

  const cookies = document.cookie.split('; ');
  const localeCookie = cookies.find(c => c.startsWith('NEXT_LOCALE='));
  const locale = localeCookie?.split('=')[1];

  return locale && locales.includes(locale as Locale)
    ? (locale as Locale)
    : defaultLocale;
}

export function setLocaleCookie(locale: Locale) {
  if (typeof window === 'undefined') return;

  const maxAge = 365 * 24 * 60 * 60; // 1 year
  document.cookie = `NEXT_LOCALE=${locale}; path=/; max-age=${maxAge}; SameSite=Lax`;
}
