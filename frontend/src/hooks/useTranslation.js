import { useCallback } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import ru from '../translations/ru';
import en from '../translations/en';

const translations = { ru, en };

export const useTranslation = () => {
  const { lang, toggleLang, setLang } = useLanguage();

  const t = useCallback((key) => {
    const keys = key.split('.');
    let value = translations[lang];
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return key;
      }
    }
    return value;
  }, [lang]);

  return { t, lang, toggleLang, setLang };
};
