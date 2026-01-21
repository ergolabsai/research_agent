# ============================================
# scripts/start-api.sh (Linux/Mac)
# ============================================
#!/bin/bash
source .env
cd api
$PYTHON_PATH -m uvicorn main:app --reload --host 0.0.0.0 --port $API_PORT
