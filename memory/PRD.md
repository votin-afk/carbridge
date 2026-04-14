# CarBridge - Платформа для импорта авто из Китая

**Последнее обновление:** 14.04.2026

## Оригинальное техзадание
Комплексная платформа для импорта автомобилей из Китая в Беларусь с интеграцией Bitrix24 CRM.

**Роли:** Администратор, Клиент, Подрядчик, Модератор.

## Текущая архитектура
- FastAPI backend, React frontend, MongoDB
- Модульные роуты: catalog.py, telegram.py, deals.py, auth.py, affiliate.py, user.py, leasing.py
- server.py: ~7000 строк
- Shared config: config.py (константы), database.py, utils/auth.py

## Выполненные задачи

### Сессия 14.04.2026 (текущая)
1. **Исправлены баги Documents.js** — proxy для фото + надёжный downloadFile
2. **Рефакторинг server.py** — deals.py (~2050 строк), config.py обновлён
3. **Обновлена главная страница** — Hero, "7 шагов к честной машине", FAQ (10 вопросов), преимущества
4. **Обновлён AI-ассистент** — навигация по платформе + подбор из каталога
5. **Публичная страница подрядчика** — endpoint GET /api/contractors/{id}/page, страница /contractor/:id
   - О компании, услуги (локализованы), контакты, команда, сертификаты, портфолио, фото офиса
   - Ссылка "Подробнее" в списке подрядчиков
   - Ссылка "Полный профиль" в тендерах
6. **Исправлен approve_contractor** — устранен KeyError при одобрении заявки
7. **Исправлен delete_contractor** — поиск в обеих коллекциях

### Предыдущие сессии
- Полная двусторонняя Telegram интеграция
- Прокси для китайских изображений
- Lightbox для фото предложений
- Добавление авто по ссылке через Che168 API
- Полная заявка в тендерах (30+ полей)

## Бэклог
- P1: Продолжить рефакторинг server.py (moderator, contractors, applications)
- P2: Telegram webhook на production (ожидает пользователя)
- P2: WhatsApp интеграция (ожидание Meta credentials)
- P2: Рефакторинг фронтенд-компонентов (ModeratorPage.js, ContractorDashboard.js)
- P3: Система платежей/эскроу
- P3: Кэширование переведённых описаний авто

## Тест-отчёты
- iteration_31.json — Публичная страница подрядчика (100%)
- iteration_30.json — Landing page + AI chat (100%)
- iteration_29.json — Deals refactoring (100%)
- iteration_28.json — Documents bugs (100%)

## Тестовые данные
- Admin: votin@tut.by / test
- User: test@test.com / test
- Contractor: test.contractor2@test.com / test123
- Test contractor ID: c1f8fc8e-b0c7-45a6-bdda-5eaf9c792a3e
