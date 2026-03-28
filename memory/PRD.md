# CarBridge - Платформа для импорта авто из Китая

**Последнее обновление:** 28.03.2026

## Оригинальное техзадание
Комплексная платформа для импорта автомобилей из Китая в Беларусь с интеграцией Bitrix24 CRM.

## Текущая архитектура
- FastAPI backend, React frontend, MongoDB
- Модульные роуты: catalog.py, telegram.py
- server.py: ~8950 строк

## Выполненные задачи (28.03.2026)

1. **Исправлен краш ContractorDashboard** — добавлен импорт MessageCircle
2. **Рефакторинг Telegram routes** — вынесено ~842 строки в routes/telegram.py
3. **Исправлен парсинг URL** — che168 блокировал скрапинг, переключено на Che168 API
4. **Полная заявка в тендерах подрядчика** — 30+ полей вместо 9
5. **Текстовые пометки клиента** — required_options, preferred_options, damage_comment
6. **Кликабельные фото предложений** — лайтбокс с навигацией, миниатюрами, точечными индикаторами
7. **Реальные фото в тендерах** — вместо стоковых unsplash теперь реальные из гаража
8. **Прокси для китайских изображений** — getProxiedImageUrl() в DashboardOverview, DealCars, Tenders

## Бэклог
- P1: Рефакторинг server.py (deals, moderator, contractors)
- P1: Webhook Telegram на production
- P2: WhatsApp интеграция (ожидание Meta credentials)
- P2: Рефакторинг фронтенд-компонентов
- P3: Система платежей/эскроу

## Тест-отчёты
- iteration_27.json — Images + lightbox (100%)
- iteration_26.json — Enriched tenders (100%)
- iteration_25.json — Parse URL fix (100%)
- iteration_24.json — Telegram refactoring (100%)

## Тестовые данные
- Admin: votin@tut.by / test
- Contractor: horon4ik@icloud.com / test123
