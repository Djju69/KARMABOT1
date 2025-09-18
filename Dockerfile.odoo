FROM odoo:17.0
USER root
COPY odoo-addons/ /mnt/extra-addons/
COPY odoo.conf /etc/odoo/
RUN chown -R odoo:odoo /mnt/extra-addons/
RUN chown odoo:odoo /etc/odoo/odoo.conf
USER odoo
EXPOSE 8069
