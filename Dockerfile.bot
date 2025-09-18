FROM odoo:17.0
USER root
COPY docker-entrypoint.sh /usr/local/bin/
COPY odoo-addons/ /mnt/extra-addons/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
RUN chown -R odoo:odoo /mnt/extra-addons/
USER odoo
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
