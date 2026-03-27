# CarBridge - Платформа для импорта авто из Китая

**Последнее обновление:** 27.03.2026

## Оригинальное техзадание
Комплексная платформа для импорта автомобилей из Китая в Беларусь. Включает:
- Главная страница с каталогом, калькулятором, AI-ассистентом
- Личный кабинет пользователя: гараж, заявки, тендеры, сделки, верификация
- Панель модератора: управление пользователями, документами, сделками
- Система подрядчиков: регистрация, дашборд, профиль, тендеры
- **Интеграция с Bitrix24** для автоматизации CRM
- **Telegram интеграция** — двухсторонний обмен сообщениями

## Роли пользователей
- **user**: Обычный пользователь
- **moderator**: Модератор для проверки документов и сделок
- **admin**: Полный доступ (votin@tut.by / test)
- **contractor**: Подрядчик (horon4ik@icloud.com / test123 — OLa CARS)

## Текущая архитектура (27.03.2026)

### Backend
- **Framework**: FastAPI
- **Database**: MongoDB
- **Auth**: JWT токены (отдельные для пользователей и подрядчиков)

### Структура проекта
```
/app
├── backend/
│   ├── config.py              # Конфигурация (JWT, MongoDB, uploads)
│   ├── database.py            # MongoDB подключение
│   ├── server.py              # Основной API (~8776 строк) - рефакторинг в процессе
│   ├── models/
│   │   └── schemas.py         # Pydantic модели
│   ├── routes/
│   │   ├── auth.py            # Роуты аутентификации
│   │   ├── affiliate.py       # Роуты партнёрской программы
│   │   ├── user.py            # Роуты пользователя
│   │   ├── catalog.py         # Каталог Che168
│   │   ├── leasing.py         # Роуты лизинга
│   │   └── telegram.py        # ✅ НОВЫЙ: Telegram интеграция (~600 строк)
│   ├── services/
│   │   ├── telegram_service.py # Сервис уведомлений Telegram
│   │   ├── che168.py          # API каталога
│   │   ├── calculator.py      # Калькулятор таможни
│   │   └── bitrix24.py        # Bitrix24 CRM
│   └── utils/
│       ├── auth.py            # JWT, пароли, get_current_user
│       └── cache.py           # Кэширование
├── frontend/
│   └── src/
│       └── pages/
│           ├── ContractorDashboard.js  # Кабинет подрядчика (1900+ строк)
│           ├── ModeratorPage.js        # Панель модератора (2800+ строк)
│           ├── ContractorProfilePage.js # Публичный профиль
│           └── dashboard/
│               ├── Tenders.js          # Тендеры клиента
│               ├── Documents.js        # Документы сделки
│               └── ...
└── memory/
    └── PRD.md
```

## Выполненные задачи (27.03.2026)

### ✅ Исправлен импорт MessageCircle в ContractorDashboard
- Предыдущий агент добавил секцию Telegram на страницу профиля подрядчика, но забыл импортировать `MessageCircle` из lucide-react
- Это приводило к крашу: "MessageCircle is not defined" при открытии вкладки "Профиль компании"
- Добавлен импорт, секция Telegram работает корректно

### ✅ Рефакторинг: Telegram routes вынесены из server.py
- Создан `/app/backend/routes/telegram.py` (~600 строк)
- Вынесены все эндпоинты: webhook, link/unlink/status/test (user + contractor), admin stats/invites
- Вынесены helper-функции: `get_moderator_chat_ids`, `get_user_active_chats`, `send_message_to_deal_chat`, `download_telegram_file`, `save_telegram_file_to_deal`
- server.py уменьшен с 9618 до 8776 строк (−842 строки)
- Обратная совместимость: `get_moderator_chat_ids` и `telegram_pending_verifications` реимпортированы в server.py
- **Тестирование**: 100% (21/21 backend, все frontend компоненты)

### ✅ Подтверждено: Загрузка файлов для этапов сделки уже реализована
- Backend: `POST /api/deals/{deal_id}/stages/{stage_key}/files` (клиент)
- Backend: `POST /api/contractor/deals/{deal_id}/stages/{stage_key}/files` (подрядчик)
- Frontend: StageInfographic.js — кнопка загрузки + скачивание
- Протестировано curl — файлы загружаются и возвращаются корректно

## Рефакторинг server.py — Прогресс

| Модуль | Файл | Строк | Статус |
|--------|-------|-------|--------|
| Каталог | routes/catalog.py | 703 | ✅ Готов |
| Telegram | routes/telegram.py | ~600 | ✅ Готов (27.03.2026) |
| Auth | routes/auth.py | 146 | ✅ Готов (не подключен к app) |
| Affiliate | routes/affiliate.py | 343 | ✅ Готов (не подключен к app) |
| User | routes/user.py | 169 | ✅ Готов (не подключен к app) |
| Leasing | routes/leasing.py | 70 | ✅ Готов |
| **Deals** | — | ~2000 | 🔄 Следующий |
| **Moderator** | — | ~1500 | 🔄 Планируется |
| **Contractors** | — | ~500 | 🔄 Планируется |

**Текущий размер server.py**: 8776 строк (было 9618)

## Бэклог задач

### P0 — Критический
1. ~~Привязка Telegram для подрядчиков~~ ✅ Готово
2. ~~Загрузка файлов на этапы сделки~~ ✅ Уже работает

### P1 — Высокий приоритет
1. **Продолжение рефакторинга server.py** — вынести deals, moderator, contractors
2. **Webhook Telegram на production** — пользователь должен обновить webhook для carbridge.by
3. **WhatsApp интеграция** — ожидание Meta credentials от пользователя

### P2 — Средний приоритет
1. Рефакторинг фронтенд-компонентов (ModeratorPage.js 2800+ строк, ContractorDashboard.js 1900+ строк)
2. Подключение auth.py, affiliate.py, user.py роутеров к app и удаление дублей из server.py

### P3 — Низкий приоритет
1. Система платежей/эскроу
2. Кэширование переводов описаний
3. GPS трекинг (реальные данные)

## Интеграции
- **Che168 API** (auto-api.com) — каталог авто
- **Emergent LLM Key** — AI чат
- **Bitrix24** — CRM
- **Telegram Bot** (@KARBRIDGE_Bot) — уведомления
- **WhatsApp Business API** — ожидание credentials

## Тестовые данные
- Admin: votin@tut.by / test
- Contractor: horon4ik@icloud.com / test123 (OLa CARS)

## Тест-отчёты
- iteration_24.json — Telegram refactoring + MessageCircle fix (100%)
