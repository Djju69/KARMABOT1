#!/bin/bash
# Backup script for KarmaBot
# Usage: ./backup.sh [backup_name]

set -euo pipefail

# Configuration
BACKUP_DIR="/var/backups/karmabot"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${1:-karmabot_${TIMESTAMP}}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_PATH}"

# Ensure the backup directory is writable
if [ ! -w "${BACKUP_PATH}" ]; then
    echo "Error: Backup directory is not writable: ${BACKUP_PATH}" >&2
    exit 1
fi

echo "Starting backup: ${BACKUP_NAME}"

# Backup database
if [ -f "data/prod.db" ]; then
    echo "Backing up database..."
    sqlite3 data/prod.db ".backup '${BACKUP_PATH}/prod.db'"
    if [ $? -ne 0 ]; then
        echo "Warning: Database backup failed" >&2
    fi
fi

# Backup important files
echo "Backing up configuration..."
tar -czf "${BACKUP_PATH}/config.tar.gz" .env* config/

# Create a restore script
cat > "${BACKUP_PATH}/RESTORE_README.txt" <<EOL
# KarmaBot Restore Instructions

1. Stop the application:
   sudo systemctl stop karmabot

2. Restore the database:
   cp prod.db /path/to/karmabot/data/

3. Restore configuration:
   tar -xzf config.tar.gz -C /path/to/karmabot/

4. Restart the application:
   sudo systemctl start karmabot
EOL

# Create a tarball of the backup
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
rm -rf "${BACKUP_NAME}"

# Keep only the last 7 backups
ls -t | grep '^karmabot_.*\.tar\.gz$' | tail -n +8 | xargs -r rm -f

echo "Backup completed: ${BACKUP_PATH}.tar.gz"

# Optional: Upload to remote storage
# echo "Uploading to remote storage..."
# rclone copy "${BACKUP_PATH}.tar.gz" remote:backups/karmabot/
