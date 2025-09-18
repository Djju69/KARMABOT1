FROM odoo:17.0
USER root
COPY odoo-addons/ /mnt/extra-addons/
RUN chown -R odoo:odoo /mnt/extra-addons/
USER odoo  
ENV ODOO_RC=/dev/null
CMD ["odoo", "--dev=all", "--without-demo=all"]