FROM odoo:17.0

# Копировать модуль
COPY odoo-addons/ /mnt/extra-addons/

# Проверить что модуль скопировался
RUN ls -la /mnt/extra-addons/ && \
    ls -la /mnt/extra-addons/karmabot_webapp/

# Создать конфигурационный файл
RUN echo '[options]' > /etc/odoo/odoo.conf && \
    echo 'addons_path = /usr/lib/python3/dist-packages/odoo/addons,/var/lib/odoo/addons/17.0,/mnt/extra-addons' >> /etc/odoo/odoo.conf && \
    echo 'data_dir = /var/lib/odoo' >> /etc/odoo/odoo.conf

# Запустить Odoo
CMD ["python3", "/usr/bin/odoo"]
