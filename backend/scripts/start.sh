#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source .venv/Scripts/activate
python scripts/kill_port.py 8000
if netstat -ano | grep -q "127.0.0.1:8000.*LISTENING"; then
  echo ""
  echo "UYARI: Port 8000 hala dolu. Tüm python.exe süreçlerini sonlandırın:"
  echo "  taskkill //IM python.exe //F"
  echo ""
  exit 1
fi
echo "Backend baslatiliyor..."
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
