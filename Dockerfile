FROM odoo:17.0

USER root
COPY odoo-addons/ /mnt/extra-addons/
RUN chown -R odoo:odoo /mnt/extra-addons/

# Проверка что модули скопировались
RUN ls -la /mnt/extra-addons/ && \
    find /mnt/extra-addons/ -name "__manifest__.py"

USER odoo
EXPOSE 8069

<<<<<<< HEAD

=======
# Запуск БЕЗ конфигурационного файла
>>>>>>> refs/remotes/origin/main
CMD ["odoo", "--addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons"]
