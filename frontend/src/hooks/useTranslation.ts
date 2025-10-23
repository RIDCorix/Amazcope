import { useEffect, useState } from 'react';

import { getMessages } from '@/i18n';
import { getLocaleFromCookie, type Locale } from '@/i18n/config';

type Messages = Record<string, any>;

export function useTranslation() {
  const [locale, setLocale] = useState<Locale>('en');
  const [messages, setMessages] = useState<Messages>({});

  useEffect(() => {
    const currentLocale = getLocaleFromCookie();
    setLocale(currentLocale);

    getMessages(currentLocale).then(msgs => {
      setMessages(msgs);
    });
  }, []);

  const t = (key: string, params?: Record<string, string | number>): string => {
    const keys = key.split('.');
    let value: any = messages;

    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return key; // Return key if translation not found
      }
    }

    if (typeof value !== 'string') {
      return key;
    }

    // Replace parameters - support both {{param}} and {param} formats
    if (params) {
      return Object.entries(params).reduce((str, [paramKey, paramValue]) => {
        // Replace {{param}} format
        str = str.replace(
          new RegExp(`\\{\\{${paramKey}\\}\\}`, 'g'),
          String(paramValue)
        );
        // Replace {param} format
        str = str.replace(
          new RegExp(`\\{${paramKey}\\}`, 'g'),
          String(paramValue)
        );
        return str;
      }, value);
    }

    return value;
  };

  return { t, locale };
}
