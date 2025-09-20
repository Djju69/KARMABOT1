#!/bin/bash
set -e

# Ждем базу данных
until pg_isready -h $PGHOST -p $PGPORT -U $PGUSER; do
  echo "Waiting for database..."
  sleep 2
done

# БЕЗОПАСНЫЙ запуск Odoo БЕЗ инициализации
exec odoo \
  --db_host=$PGHOST \
  --db_port=$PGPORT \
  --db_user=$PGUSER \
  --db_password=$PGPASSWORD \
  --database=$PGDATABASE \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons \
  --without-demo=all \
  --no-database-list
