#!/usr/bin/env bash
# ============================================================
#  sync-db.sh — Копирование удалённой MongoDB в локальную
# ============================================================
#
#  Использование:
#    export REMOTE_MONGO_URL="mongodb+srv://user:pass@cluster.mongodb.net"
#    bash scripts/sync-db.sh
#
#  Требования:
#    - mongodump и mongorestore (пакет mongodb-database-tools)
#    - Локальная MongoDB на localhost:27017 (docker-compose up -d)
#
# ============================================================

set -euo pipefail

DB_NAME="test_database"
DUMP_DIR="./dump_carbridge"
LOCAL_URL="mongodb://localhost:27017"

# --- Проверка переменной ---
if [ -z "${REMOTE_MONGO_URL:-}" ]; then
  echo "Ошибка: задайте переменную REMOTE_MONGO_URL"
  echo ""
  echo "  export REMOTE_MONGO_URL=\"mongodb+srv://user:pass@cluster.mongodb.net\""
  echo "  bash scripts/sync-db.sh"
  exit 1
fi

# --- Проверка утилит ---
for cmd in mongodump mongorestore; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Ошибка: $cmd не найден."
    echo "Установите mongodb-database-tools:"
    echo "  macOS:   brew install mongodb-database-tools"
    echo "  Ubuntu:  sudo apt install mongodb-database-tools"
    echo "  Windows: https://www.mongodb.com/try/download/database-tools"
    exit 1
  fi
done

# --- Дамп удалённой БД ---
echo "==> Дамп удалённой БД ($DB_NAME) ..."
rm -rf "$DUMP_DIR"
mongodump \
  --uri="$REMOTE_MONGO_URL" \
  --db="$DB_NAME" \
  --out="$DUMP_DIR"

echo "==> Дамп готов: $DUMP_DIR/$DB_NAME"

# --- Восстановление в локальную ---
echo "==> Восстановление в локальную MongoDB ..."
mongorestore \
  --uri="$LOCAL_URL" \
  --db="$DB_NAME" \
  --drop \
  "$DUMP_DIR/$DB_NAME"

echo "==> Готово! БД '$DB_NAME' скопирована в localhost:27017"

# --- Очистка ---
rm -rf "$DUMP_DIR"
echo "==> Временные файлы удалены."
