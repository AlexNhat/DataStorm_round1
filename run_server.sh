#!/bin/bash
echo "Starting Supply Chain Analytics Dashboard..."
echo ""
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

