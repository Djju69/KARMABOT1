FROM odoo:17.0
USER root  
COPY odoo-addons/ /mnt/extra-addons/
RUN chown -R odoo:odoo /mnt/extra-addons/
USER odoo
CMD ["odoo", "--db_host=$PGHOST", "--db_port=$PGPORT", "--db_user=$PGUSER", "--db_password=$PGPASSWORD", "--database=$PGDATABASE", "--addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons", "--without-demo=all", "--no-database-list"]