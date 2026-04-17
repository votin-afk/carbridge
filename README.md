# CarBridge — Импорт авто из Китая

Платформа для безопасного импорта автомобилей из Китая: тендеры, верификация подрядчиков, калькулятор растаможки, AI-ассистент.

---

## Локальная разработка

### Требования

- **Node.js** 18+ и **yarn**
- **Python** 3.10+ и **pip**
- **Docker** и **Docker Compose** (для MongoDB)

### 1. Клонировать репозиторий

```bash
git clone <repo-url> carbridge
cd carbridge
```

### 2. Поднять MongoDB

```bash
docker compose up -d
```

MongoDB будет доступна на `localhost:27017`, база `test_database`.

### 3. Настроить переменные окружения

**Бэкенд:**

```bash
cp backend/.env.example backend/.env
```

Для базовой работы (логин, калькулятор, подрядчики) достаточно значений по умолчанию.
Для Telegram, AI-ассистента, каталога Che168 — раскомментируйте и заполните соответствующие ключи в `backend/.env`.

**Фронтенд:**

```bash
cp frontend/.env.example frontend/.env
```

### 4. Установить зависимости

```bash
# Бэкенд
cd backend
pip install -r requirements.txt
cd ..

# Фронтенд
cd frontend
yarn install
cd ..
```

### 5. Запустить

В двух терминалах:

```bash
# Терминал 1 — Бэкенд (порт 8001)
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Терминал 2 — Фронтенд (порт 3000)
cd frontend
yarn start
```

Откройте `http://localhost:3000` в браузере.

### 6. Первый вход

При первом запуске бэкенд **автоматически создаёт**:

| Роль       | Email              | Пароль |
|------------|--------------------|--------|
| Админ      | votin@tut.by       | test   |
| Админ      | admin@carbridge.by | test   |
| Тест-юзер  | test@test.com      | test   |

Подрядчики регистрируются через `/contractor-register` и одобряются админом в модерации.

---

## Синхронизация БД с продакшена

Чтобы скопировать данные из удалённой MongoDB в локальную:

```bash
# Установить mongodb-database-tools:
#   macOS:   brew install mongodb-database-tools
#   Ubuntu:  sudo apt install mongodb-database-tools

# Задать URI удалённой БД (НЕ коммитить в репозиторий!)
export REMOTE_MONGO_URL="mongodb+srv://user:password@cluster.mongodb.net"

# Запустить скрипт
bash scripts/sync-db.sh
```

Скрипт сделает `mongodump` удалённой базы `test_database` и `mongorestore` в локальную MongoDB.

---

## Структура проекта

```
├── docker-compose.yml          # MongoDB для локальной разработки
├── scripts/
│   └── sync-db.sh              # Копирование удалённой БД в локальную
├── backend/
│   ├── .env.example            # Шаблон переменных окружения
│   ├── server.py               # Главный FastAPI-сервер
│   ├── routes/                 # Модульные роуты (deals, telegram, catalog)
│   ├── services/               # Bitrix24, Telegram, Che168
│   └── requirements.txt
├── frontend/
│   ├── .env.example            # Шаблон переменных фронтенда
│   ├── src/
│   │   ├── pages/              # Страницы приложения
│   │   ├── contexts/           # Auth, Language (i18n)
│   │   ├── translations/       # ru.js, en.js
│   │   └── components/ui/      # Shadcn/UI компоненты
│   └── package.json
└── README.md
```

## Ключевые API

| Метод  | Эндпоинт                              | Описание                    |
|--------|----------------------------------------|-----------------------------|
| POST   | `/api/auth/register`                   | Регистрация                 |
| POST   | `/api/auth/login`                      | Вход                        |
| GET    | `/api/contractors`                     | Список подрядчиков          |
| POST   | `/api/calculator`                      | Калькулятор растаможки      |
| POST   | `/api/chat`                            | AI-ассистент                |
| GET    | `/api/moderator/applications`          | Заявки подрядчиков (админ)  |
| POST   | `/api/moderator/applications/:id/approve` | Одобрить подрядчика      |
