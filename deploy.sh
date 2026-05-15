#!/usr/bin/env bash
# =====================================================
#   H A Q Q I  -  V P S   D E P L O Y
#   Usage: bash deploy.sh <SERVER_IP> [DOMAIN]
#   Example: bash deploy.sh 123.123.123.123 haqqi.ma
# =====================================================
set -euo pipefail

SERVER="${1:?Usage: deploy.sh <SERVER_IP> [DOMAIN]}"
DOMAIN="${2:-}"
KEY="${3:-${HOME}/.ssh/id_rsa}"

echo "=== 1. Installing Docker on VPS ==="
ssh -i "$KEY" "root@${SERVER}" '
  if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker; systemctl start docker
  fi
  if ! command -v docker compose &>/dev/null; then
    DOCKER_CONFIG=/usr/local/lib/docker/cli-plugins
    mkdir -p "$DOCKER_CONFIG"
    curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o "$DOCKER_CONFIG/docker-compose"
    chmod +x "$DOCKER_CONFIG/docker-compose"
  fi
'

echo "=== 2. Copying project files ==="
rsync -avz --exclude '__pycache__/' --exclude '.git/' \
  --exclude 'chroma_db/' --exclude '.env' \
  -e "ssh -i $KEY" ./ "root@${SERVER}:~/haqqi/"

echo "=== 3. Setting up .env ==="
ssh -i "$KEY" "root@${SERVER}" '
  if [ ! -f ~/haqqi/.env ]; then
    echo "WARNING: No .env file on server!"
    echo "Create ~/haqqi/.env with:"
    echo "  GROQ_API_KEY=..."
    echo "  SUPABASE_URL=..."
    echo "  SUPABASE_KEY=..."
  fi
'

echo "=== 4. Updating Caddyfile with domain ==="
if [ -n "$DOMAIN" ]; then
  ssh -i "$KEY" "root@${SERVER}" "sed -i 's/haqqi.ma, www.haqqi.ma/$DOMAIN, www.$DOMAIN/' ~/haqqi/Caddyfile"
fi

echo "=== 5. Deploying with Docker Compose ==="
ssh -i "$KEY" "root@${SERVER}" '
  cd ~/haqqi
  mkdir -p data/chromadb data/laws data/judgements data/ingested
  docker compose up -d --build
'

echo ""
echo "=== Done! ==="
if [ -n "$DOMAIN" ]; then
  echo "  https://$DOMAIN"
else
  echo "  http://$(ssh -i "$KEY" "root@${SERVER}" 'curl -s ifconfig.me'):8000"
fi
echo ""
echo "Next steps:"
echo "  1. Set DNS A-record for your domain to the server IP"
echo "  2. Seed data: docker exec haqqi-app-1 python scripts/update_db.py"
echo "  3. Seed jurisprudence: docker exec haqqi-app-1 python scripts/seed_jurisprudence.py"
echo "  4. Check logs: docker compose -f ~/haqqi/docker-compose.yml logs -f"
