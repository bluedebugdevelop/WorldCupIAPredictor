#!/usr/bin/env bash
# WorldCupIAPredictor - arranque (Linux/macOS)
set -e
cd "$(dirname "$0")/backend"

if [ ! -d ".venv" ]; then
  echo "Creando entorno virtual..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

echo ""
echo "Abre http://127.0.0.1:8000 en el navegador"
echo ""
uvicorn app.main:app --reload
