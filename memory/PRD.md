# CarBridge - Платформа для импорта авто из Китая

**Последнее обновление:** 14.04.2026

## Оригинальное техзадание
Комплексная платформа для импорта автомобилей из Китая в Беларусь с интеграцией Bitrix24 CRM.

**Роли:** Администратор, Клиент, Подрядчик, Модератор.

## Текущая архитектура
- FastAPI backend, React frontend, MongoDB
- Мультиязычность: RU/EN через LanguageContext + translation files
- Модульные роуты: catalog.py, telegram.py, deals.py, auth.py, affiliate.py, user.py, leasing.py
- server.py: ~7000 строк
- Shared config: config.py, database.py, utils/auth.py

## Выполненные задачи

### Сессия 14.04.2026 (текущая)
1. **Баги Documents.js** — proxy для фото + downloadFile
2. **Рефакторинг server.py** — deals.py (~2050 строк), config.py
3. **Обновлена главная страница** — Hero, 7 шагов, FAQ (10), преимущества
4. **AI-ассистент** — навигация по платформе + подбор из каталога
5. **Публичная страница подрядчика** — endpoint + фронтенд + ссылки
6. **Мультиязычность RU/EN**:
   - LanguageContext + useTranslation hook + translation files (ru.js, en.js)
   - Переключатель RU/EN в хедере лендинга и sidebar дашборда
   - Переведены: LandingPage, ContractorsPage, ContractorProfilePage, DashboardLayout
   - AI-ассистент отвечает на выбранном языке (параметр `lang` в API)
   - Язык сохраняется в localStorage

### Предыдущие сессии
- Полная двусторонняя Telegram интеграция
- Прокси для китайских изображений
- Lightbox для фото предложений
- Добавление авто по ссылке через Che168 API

## Бэклог
- P1: Рефакторинг server.py (moderator, contractors, applications)
- P1: Добавить переводы в оставшиеся dashboard-страницы (Garage, Applications, Tenders, Documents и т.д.)
- P2: Telegram webhook на production
- P2: WhatsApp интеграция (ожидание Meta credentials)
- P2: Рефакторинг фронтенд-компонентов
- P3: Система платежей/эскроу
- P3: Кэширование переведённых описаний авто

## Тест-отчёты
- iteration_32.json — Мультиязычность RU/EN (100% backend, 90% frontend)
- iteration_31.json — Страница подрядчика (100%)
- iteration_30.json — Landing page + AI chat (100%)
- iteration_29.json — Deals refactoring (100%)

## Тестовые данные
- Admin: votin@tut.by / test
- User: test@test.com / test
- Contractor: test.contractor2@test.com / test123
