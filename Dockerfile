FROM odoo:17.0
USER root  
COPY odoo-addons/ /mnt/extra-addons/
COPY odoo.conf /etc/odoo/
RUN chown -R odoo:odoo /mnt/extra-addons/
USER odoo