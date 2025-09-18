#!/bin/bash  
exec odoo \
  --db_host=$ODOO_DATABASE_HOST \
  --db_user=$ODOO_DATABASE_USER \
  --db_password=$ODOO_DATABASE_PASSWORD \
  --database=$ODOO_DATABASE_NAME \
  --dev=all \
  --without-demo=all