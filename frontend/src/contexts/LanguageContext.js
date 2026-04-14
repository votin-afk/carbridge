import { createContext, useContext, useState, useCallback } from 'react';

const LanguageContext = createContext(null);

export const LanguageProvider = ({ children }) => {
  const [lang, setLang] = useState(localStorage.getItem('carbridge_lang') || 'ru');

  const switchLang = useCallback((newLang) => {
    setLang(newLang);
    localStorage.setItem('carbridge_lang', newLang);
  }, []);

  const toggleLang = useCallback(() => {
    const newLang = lang === 'ru' ? 'en' : 'ru';
    setLang(newLang);
    localStorage.setItem('carbridge_lang', newLang);
  }, [lang]);

  return (
    <LanguageContext.Provider value={{ lang, setLang: switchLang, toggleLang }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) throw new Error('useLanguage must be used within LanguageProvider');
  return context;
};

export default LanguageContext;
