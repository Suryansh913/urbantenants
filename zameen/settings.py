from pathlib import Path
import os
import sys
import cloudinary
import cloudinary.uploader
from urllib.parse import urlparse
import cloudinary.api
print("🔥🔥🔥 MARKER_TEST_12345 - YE NAYA CODE HAI 🔥🔥🔥")
BASE_DIR = Path(__file__).resolve().parent.parent
from dotenv import load_dotenv
load_dotenv()

# ── EMAIL ──────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp-relay.brevo.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = "noreply@urbantenants.com"

# ── SECURITY ───────────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-3a@=a=ir!)nxbf3ru342_6(3o@b0m4!8$v5dyuy*c9!4=fy_%0')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']

# ── APPS ───────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'cloudinary',
    'cloudinary_storage',
    'listings',
    'login',
    'chatbot',
    'partner',
    'notifications',
]

# ── MIDDLEWARE ─────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'zameen.urls'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR, "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'zameen.wsgi.application'
from django.conf import settings
# ── DATABASE ───────────────────────────────────────────
# SQLite for everything (local + production)
import os
import os
import dj_database_url

from urllib.parse import urlparse
import os

url = urlparse(os.environ["DATABASE_URL"])

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": url.path[1:],
        "USER": url.username,
        "PASSWORD": url.password,
        "HOST": url.hostname,
        "PORT": url.port,
    }
}

print(DATABASES)

# import dj_database_url
# DATABASES = {
#         "default": {
#             "ENGINE": "django.db.backends.sqlite3",
#             "NAME": BASE_DIR / "db.sqlite3",
#         }
#     }
# ── DATABASE ───────────────────────────────────────────
# raw_db_url = os.environ.get("DATABASE_URL")
# print("RAW DATABASE_URL REPR:", repr(raw_db_url))

# if not raw_db_url or not raw_db_url.strip():
#     raise Exception(
#         "DATABASE_URL env variable Render dashboard pe set nahi hai ya khaali hai! "
#         "Environment tab mein jaake add karo."
#     )

# DATABASES = {
#     "default": dj_database_url.parse(
#         raw_db_url.strip(),
#         conn_max_age=600,
#     )
# }

# print("FINAL DATABASES:", {k: v for k, v in DATABASES["default"].items() if k != "PASSWORD"})
# print("USING SQLITE DATABASE")

# ── PASSWORD VALIDATION ────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── I18N ───────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ── STATIC FILES ───────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── CLOUDINARY ─────────────────────────────────────────
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'ddl8p87bb',
    'API_KEY': '793691793625374',
    'API_SECRET': 'e-ChdO_6MFfEM7wpPCuKbXnt-ys',
}
cloudinary.config(
    cloud_name="ddl8p87bb",
    api_key="793691793625374",
    api_secret="e-ChdO_6MFfEM7wpPCuKbXnt-ys",
    secure=True,
)

# ── AUTH & ALLAUTH ─────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

LOGIN_URL = 'loginv'
LOGIN_REDIRECT_URL = 'base'
LOGOUT_REDIRECT_URL = 'loginv'

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# ── MISC ───────────────────────────────────────────────
CSRF_FAILURE_VIEW = 'zameen.views.csrf_failure'
X_FRAME_OPTIONS = "SAMEORIGIN"
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
            'secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
            'key': ''
        }
    }
}
SITE_ID = int(os.environ.get('SITE_ID', 1))
print("FINAL DATABASES:", DATABASES)
print("hi")