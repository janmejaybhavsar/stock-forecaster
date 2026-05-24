#!/bin/bash
set -e

echo "Starting Stock Forecaster..."

# Start FastAPI in background
uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API..."
for i in $(seq 1 30); do
    if python -c "import httpx; httpx.get('http://localhost:8000/health')" 2>/dev/null; then
        echo "API is ready!"
        break
    fi
    sleep 1
done

# Start Streamlit
echo "Starting Streamlit dashboard..."
streamlit run src/dashboard/app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false &
STREAMLIT_PID=$!

echo "Stock Forecaster running!"
echo "  API:       http://localhost:8000"
echo "  Dashboard: http://localhost:8501"
echo "  API Docs:  http://localhost:8000/docs"

# Wait for either process to exit
wait $API_PID $STREAMLIT_PID
