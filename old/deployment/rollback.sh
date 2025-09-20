#!/bin/bash
# Rollback script for KarmaBot
# Usage: ./rollback.sh <backup_file.tar.gz>

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    echo "Available backups:"
    ls -l /var/backups/karmabot/karmabot_*.tar.gz 2>/dev/null || echo "No backups found in /var/backups/karmabot/"
    exit 1
fi

BACKUP_FILE="$1"
TEMP_DIR="/tmp/karmabot_rollback_$(date +%s)"
SERVICE_NAME="karmabot"

# Validate backup file
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}" >&2
    exit 1
fi

# Create temporary directory
mkdir -p "${TEMP_DIR}"

# Extract backup
echo "Extracting backup..."
tar -xzf "${BACKUP_FILE}" -C "${TEMP_DIR}"

# Stop the service
echo "Stopping ${SERVICE_NAME} service..."
systemctl stop "${SERVICE_NAME}" || true

# Restore database
if [ -f "${TEMP_DIR}/prod.db" ]; then
    echo "Restoring database..."
    cp "${TEMP_DIR}/prod.db" "data/prod.db"
    chmod 660 "data/prod.db"
fi

# Restore configuration
if [ -f "${TEMP_DIR}/config.tar.gz" ]; then
    echo "Restoring configuration..."
    tar -xzf "${TEMP_DIR}/config.tar.gz" -C .
fi

# Clean up
rm -rf "${TEMP_DIR}"

# Start the service
echo "Starting ${SERVICE_NAME} service..."
systemctl start "${SERVICE_NAME}"

# Verify service status
echo "Verifying service status..."
sleep 5
systemctl status "${SERVICE_NAME}" --no-pager

echo "Rollback completed successfully!"
echo "Please verify the application is working as expected."
