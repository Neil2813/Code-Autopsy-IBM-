#!/bin/bash
set -euo pipefail

APP_DIR=/opt/codeautopsy
AWS_REGION=$(cat "$APP_DIR/deploy/aws-region")
SECRET_FILE=$(mktemp)
ERROR_FILE=$(mktemp)
ENV_FILE=$(mktemp "$APP_DIR/deploy/llm.env.XXXXXX")
trap 'rm -f "$SECRET_FILE" "$ERROR_FILE" "$ENV_FILE"' EXIT

if aws secretsmanager get-secret-value \
    --secret-id codeautopsy/llm \
    --region "$AWS_REGION" \
    --query SecretString \
    --output text > "$SECRET_FILE" 2> "$ERROR_FILE"; then
    python3 - "$SECRET_FILE" "$ENV_FILE" <<'PY'
import json
import re
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    secret = json.load(source)
allowed = {
    "WATSONX_API_KEY", "WATSONX_PROJECT_ID", "WATSONX_URL", "WATSONX_MODEL",
    "OPENAI_API_KEY", "OPENAI_MODEL", "GROQ_API_KEY", "GROQ_MODEL",
    "PRIMARY_LLM_PROVIDER",
}
with open(sys.argv[2], "w", encoding="utf-8") as target:
    for key, value in secret.items():
        if key not in allowed:
            continue
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9._:/+=-]*", value):
            raise ValueError(f"{key} contains unsupported characters for the container env file")
        target.write(f"{key}={value}\n")
    target.flush()
PY
    chmod 0600 "$ENV_FILE"
    mv "$ENV_FILE" "$APP_DIR/deploy/llm.env"
    echo "Loaded LLM configuration from Secrets Manager."
elif grep -q 'ResourceNotFoundException' "$ERROR_FILE"; then
    : > "$ENV_FILE"
    chmod 0600 "$ENV_FILE"
    mv "$ENV_FILE" "$APP_DIR/deploy/llm.env"
    echo "No codeautopsy/llm secret found; the app will use its configured fallback provider."
else
    cat "$ERROR_FILE" >&2
    exit 1
fi

if [[ "${1:-}" != "--no-restart" ]]; then
    cd "$APP_DIR"
    /usr/local/bin/docker-compose -f docker-compose.production.yml up -d --no-deps --force-recreate backend
fi
