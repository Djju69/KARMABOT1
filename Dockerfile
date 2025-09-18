FROM odoo:17.0
USER root  
COPY odoo-addons/ /mnt/extra-addons/
RUN chown -R odoo:odoo /mnt/extra-addons/
USER odoo
ENTRYPOINT ["bash", "-c", "odoo --db_host=postgres.railway.internal --db_port=5432 --db_user=postgres --db_password=waDJfQNAzaVWvlNxFNkSlknlZUITXrwJ --database=railway --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons --without-demo=all --no-database-list"]