FROM odoo:17.0
USER root
COPY odoo-addons/ /mnt/extra-addons/
RUN chown -R odoo:odoo /mnt/extra-addons/
USER odoo
CMD ["odoo", "--db_host=postgres.railway.internal", "--db_user=postgres", "--db_password=waDJfQNAzaVWvlNxFNkSlknlZUITXrwJ", "--database=railway", "--dev=all", "--without-demo=all"]