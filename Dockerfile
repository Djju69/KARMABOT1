# Multi-stage build
ARG SERVICE_TYPE=bot

# Stage for bot
FROM python:3.11-slim AS bot
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main_v2.py"]

# Stage for odoo  
FROM odoo:17.0 AS odoo
USER root
COPY odoo-addons/ /mnt/extra-addons/
RUN chown -R odoo:odoo /mnt/extra-addons/
USER odoo

# Final stage - выбирается через ARG
FROM ${SERVICE_TYPE}