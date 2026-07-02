# #!/usr/bin/env bash
# set -o errexit

# echo "Installing dependencies..."
# pip install --upgrade pip setuptools wheel
# pip install -r requirements.txt

# echo "Collecting static files..."
# python manage.py collectstatic --noinput || echo "Static files collection failed but continuing"

# echo "Running migrations..."
# python manage.py migrate --noinput || echo "Migrations failed but continuing"

# echo "✅ Build completed!"
