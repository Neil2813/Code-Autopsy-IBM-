#!/bin/bash
set -euo pipefail

APP_DIR=/opt/codeautopsy
LOG_FILE=/var/log/codeautopsy-bootstrap.log
BACKUP_BUCKET=${BACKUP_BUCKET:?BACKUP_BUCKET is required}
AWS_REGION=${AWS_REGION:?AWS_REGION is required}

exec > >(tee -a "$LOG_FILE") 2>&1
umask 077

dnf install -y docker unzip jq
systemctl enable --now docker

if ! command -v docker-compose >/dev/null 2>&1; then
    curl -fsSL https://github.com/docker/compose/releases/download/v2.37.1/docker-compose-linux-x86_64 \
        -o /usr/local/bin/docker-compose
    chmod 0755 /usr/local/bin/docker-compose
fi

mkdir -p "$APP_DIR/deploy" "$APP_DIR/data/uploads" "$APP_DIR/data/temp" "$APP_DIR/data/logs"
cd "$APP_DIR"

DB_PASSWORD=$(openssl rand -hex 32)
SECRET_KEY=$(openssl rand -hex 32)
printf 'DB_PASSWORD=%s\n' "$DB_PASSWORD" > .env

cat > deploy/runtime.env <<EOF
APP_NAME=Code-Autopsy
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_TYPE=postgresql
REDIS_PASSWORD=
STORAGE_TYPE=local
UPLOAD_DIR=/app/uploads
TEMP_DIR=/app/temp
MAX_UPLOAD_SIZE_MB=100
SECRET_KEY=$SECRET_KEY
ALLOWED_ORIGINS=*
ALLOW_CREDENTIALS=false
LOG_LEVEL=INFO
MAX_CONCURRENT_JOBS=5
JOB_TIMEOUT_SECONDS=3600
PRIMARY_LLM_PROVIDER=watsonx
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL=ibm/granite-13b-chat-v2
MCP_ENABLED=false
MCP_MOCK_MODE=true
EOF

printf '%s\n' "$AWS_REGION" > deploy/aws-region
bash deploy/refresh-llm-secret.sh --no-restart

cat > deploy/backup.sh <<EOF
#!/bin/bash
set -euo pipefail
APP_DIR=/opt/codeautopsy
BACKUP_BUCKET=$BACKUP_BUCKET
AWS_REGION=$AWS_REGION
STAMP=\$(date -u +%Y%m%dT%H%M%SZ)
WORK_DIR=\$(mktemp -d)
trap 'rm -rf "\$WORK_DIR"' EXIT

DB_PASSWORD=\$(sed -n 's/^DB_PASSWORD=//p' "\$APP_DIR/.env")
docker exec -e PGPASSWORD="\$DB_PASSWORD" codeautopsy-postgres \\
  pg_dump -U legacy_copilot -d legacy_copilot -Fc > "\$WORK_DIR/database.dump"
tar -czf "\$WORK_DIR/uploads.tar.gz" -C "\$APP_DIR/data" uploads
aws s3 cp "\$WORK_DIR/database.dump" "s3://\$BACKUP_BUCKET/backups/\$STAMP/database.dump" --region "\$AWS_REGION"
aws s3 cp "\$WORK_DIR/uploads.tar.gz" "s3://\$BACKUP_BUCKET/backups/\$STAMP/uploads.tar.gz" --region "\$AWS_REGION"
EOF
chmod 0750 deploy/backup.sh

cat > /etc/systemd/system/codeautopsy-backup.service <<EOF
[Unit]
Description=Back up Code Autopsy database and uploads to S3
After=docker.service

[Service]
Type=oneshot
ExecStart=$APP_DIR/deploy/backup.sh
EOF

cat > /etc/systemd/system/codeautopsy-backup.timer <<'EOF'
[Unit]
Description=Daily Code Autopsy backup

[Timer]
OnCalendar=*-*-* 02:30:00 UTC
Persistent=true

[Install]
WantedBy=timers.target
EOF

cat > /etc/systemd/system/codeautopsy.service <<EOF
[Unit]
Description=Code Autopsy application containers
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose -f docker-compose.production.yml up -d --build
ExecStop=/usr/local/bin/docker-compose -f docker-compose.production.yml stop
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now codeautopsy-backup.timer
systemctl enable codeautopsy.service
systemctl start codeautopsy.service
