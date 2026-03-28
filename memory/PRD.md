# CarBridge - Платформа для импорта авто из Китая

**Последнее обновление:** 28.03.2026

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

## Текущая архитектура (28.03.2026)

### Backend
- **Framework**: FastAPI
- **Database**: MongoDB
- **Auth**: JWT токены (отдельные для пользователей и подрядчиков)

### Структура проекта
```
/app
├── backend/
│   ├── config.py              # Конфигурация
│   ├── database.py            # MongoDB подключение
│   ├── server.py              # Основной API (~8776 строк)
│   ├── models/schemas.py      # Pydantic модели
│   ├── routes/
│   │   ├── auth.py, affiliate.py, user.py  # Не подключены к app
│   │   ├── catalog.py         # Каталог Che168
│   │   ├── leasing.py         # Лизинг
│   │   └── telegram.py        # ✅ Telegram интеграция (вынесен 27.03.2026)
│   ├── services/
│   │   ├── telegram_service.py
│   │   ├── che168.py          # API каталога (используется для парсинга URL)
│   │   ├── calculator.py
│   │   └── bitrix24.py
│   └── utils/auth.py, cache.py
├── frontend/src/pages/
│   ├── ContractorDashboard.js  # ~1900 строк
│   ├── ModeratorPage.js        # ~2800 строк
│   ├── ContractorProfilePage.js
│   └── dashboard/
│       ├── MyGarage.js         # Добавление авто по ссылке
│       ├── Tenders.js
│       └── Documents.js
└── memory/PRD.md
```

## Выполненные задачи

### 28.03.2026
- ✅ **Исправлен парсинг URL** — che168.com блокировал прямой скрапинг anti-bot JS защитой. Теперь используется Che168 API (auto-api.com) для получения данных по inner_id из URL. Тестирование: 100% (iteration_25.json)

### 27.03.2026
- ✅ **Исправлен краш ContractorDashboard** — добавлен импорт `MessageCircle`
- ✅ **Рефакторинг Telegram** — вынесено ~842 строки из server.py в routes/telegram.py
- ✅ **Подтверждено**: загрузка файлов на этапы сделки уже работает

## Рефакторинг server.py — Прогресс
| Модуль | Файл | Статус |
|--------|-------|--------|
| Каталог | routes/catalog.py | ✅ |
| Telegram | routes/telegram.py | ✅ |
| **Deals** | — | 🔄 Следующий (~2000 строк) |
| **Moderator** | — | 🔄 Планируется |
| **Contractors** | — | 🔄 Планируется |

## Бэклог задач

### P1 — Высокий
1. Продолжение рефакторинга server.py
2. Webhook Telegram на production (ожидание от пользователя)
3. WhatsApp интеграция (ожидание Meta credentials)

### P2 — Средний
1. Рефакторинг фронтенд-компонентов
2. Подключение auth.py, affiliate.py, user.py роутеров

### P3 — Низкий
1. Система платежей/эскроу
2. Кэширование переводов

## Интеграции
- Che168 API (auto-api.com), Emergent LLM Key, Bitrix24, Telegram Bot, WhatsApp (ожидание)

## Тест-отчёты
- iteration_25.json — Parse URL fix (100%)
- iteration_24.json — Telegram refactoring (100%)
