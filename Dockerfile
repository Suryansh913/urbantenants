# Python base image (stable version)
FROM python:3.11.9
ENV DJANGO_SETTINGS_MODULE=zameen.settings
# Working directory set karo
WORKDIR /app

# Project files copy karo
COPY . /app

# pip upgrade



RUN pip install --upgrade pip

# dependencies install



RUN pip install -r requirements.txt

# static files collect (Django)
RUN python manage.py collectstatic --noinput

# port expose (Render auto uses PORT env)
EXPOSE 8000

# start command
CMD gunicorn zameen.wsgi:application --bind 0.0.0.0:$PORT