FROM odoo:17.0
USER root
COPY odoo.conf /etc/odoo/
COPY odoo-addons/ /mnt/extra-addons/
RUN chown -R odoo:odoo /mnt/extra-addons/
RUN chown odoo:odoo /etc/odoo/odoo.conf
USER odoo
ENV ODOO_RC=/etc/odoo/odoo.conf
CMD ["odoo", "--dev=reload,all"]