#!/usr/bin/env bash
set -o errexit

echo "============================================"
echo "Step 1: Installing dependencies..."
echo "============================================"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo ""
echo "============================================"
echo "Step 2: Collecting static files..."
echo "============================================"
python manage.py collectstatic --noinput || true

echo ""
echo "============================================"
echo "Step 3: Running migrations..."
echo "============================================"
if [ -n "$DATABASE_URL" ]; then
    echo "DATABASE_URL is set. Running migrations..."
    python manage.py migrate --noinput
else
    echo "⚠️  WARNING: DATABASE_URL not found!"
    python manage.py migrate --noinput || true
fi

echo ""
echo "✅ Build completed successfully!"
