#!/bin/bash

# Создать конфигурационный файл с переменными окружения
cat > /etc/odoo/odoo.conf << EOF
[options]
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/var/lib/odoo/addons/17.0,/mnt/extra-addons
data_dir = /var/lib/odoo
db_host = $PGHOST
db_port = $PGPORT
db_user = $PGUSER
db_password = $PGPASSWORD
db_name = $PGDATABASE
EOF

# Запустить Odoo
exec odoo
