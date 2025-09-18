#!/bin/bash
exec odoo \
  --db_host=postgres.railway.internal \
  --db_port=5432 \
  --db_user=postgres \
  --db_password=waDJfQNAzaVWvlNxFNkSlknlZUITXrwJ \
  --database=railway \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons \
  --without-demo=all
