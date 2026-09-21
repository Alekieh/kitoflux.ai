#!/usr/bin/env bash
set -e

echo "==================================================="
echo "  KITOFLUX.AI | FLOW. ADAPT. EXECUTE."
echo "==================================================="

# Start Python backend
echo "[1/2] Starting Python Asynchronous Kernel..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt --quiet
python3 main.py &
BACKEND_PID=$!
cd ..

# Start Frontend
echo "[2/2] Starting Frontend UI..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install --quiet
fi

# Trap exit to kill backend
trap "kill $BACKEND_PID" EXIT
npm run dev
