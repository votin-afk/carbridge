# CarBridge - Платформа для импорта авто из Китая

**Последнее обновление:** 28.03.2026

## Оригинальное техзадание
Комплексная платформа для импорта автомобилей из Китая в Беларусь с интеграцией Bitrix24 CRM.

**Роли:** Администратор, Клиент, Подрядчик, Модератор.

## Текущая архитектура
- FastAPI backend, React frontend, MongoDB
- Модульные роуты: catalog.py, telegram.py, deals.py, auth.py, affiliate.py, user.py, leasing.py
- server.py: ~6950 строк (уменьшено с ~8990)
- Shared config: config.py (константы), database.py, utils/auth.py

## Выполненные задачи

### Сессия 28.03.2026 (текущая)
1. **Исправлены баги Documents.js** — добавлен getProxiedImageUrl для фото авто в сделках, исправлен downloadFile (замена window.open на <a> tag)
2. **Исправлен импорт Che168API** — добавлен top-level import в server.py, устранена ошибка NameError в /api/chat
3. **Рефакторинг: deals.py** — вынесено ~2050 строк из server.py в routes/deals.py (CRUD сделок, сообщения, файлы, этапы, подрядчик-сделки)
4. **Рефакторинг: config.py** — перенесены DEAL_STAGES, CONSULTANT_FEE, COMMISSION_RATE, AFFILIATE_SHARE, PARTNER_THRESHOLD, PLATFORM_COMMISSION, PLATFORM_PAYMENT_FEE, NEW_DEAL_STAGES

### Предыдущие сессии
- Полная двусторонняя Telegram интеграция
- Привязка Telegram пользователей (авто и массовая)
- Уведомления модератору через Telegram
- AI-чат на лендинге
- Clickable brand exclusion badges в каталоге
- Прокси для китайских изображений (autoimg.cn)
- Lightbox для фото предложений подрядчиков
- Реальные фото из гаража вместо стоковых
- Исправлен парсинг URL (переход на Che168 API)
- Полная заявка в тендерах подрядчика (30+ полей)

## Бэклог
- P1: Продолжить рефакторинг server.py (moderator, contractors, applications — ~6950 строк)
- P2: Telegram webhook на production (ожидает действий пользователя)
- P2: WhatsApp интеграция (ожидание Meta credentials)
- P2: Рефакторинг фронтенд-компонентов (ModeratorPage.js, ContractorDashboard.js)
- P3: Система платежей/эскроу
- P3: Кэширование переведённых описаний авто

## Тест-отчёты
- iteration_29.json — Deals refactoring (100%)
- iteration_28.json — Documents bugs fix (100%)
- iteration_27.json — Images + lightbox (100%)
- iteration_26.json — Enriched tenders (100%)

## Тестовые данные
- Admin: votin@tut.by / test
- User: test@test.com / test
- Contractor: horon4ik@icloud.com / test123
