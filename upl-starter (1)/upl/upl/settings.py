from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DJANGO_DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")           # no default: app must not start without it
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "django.contrib.sitemaps", "django.contrib.postgres",
    "axes", "csp", "django_otp", "django_otp.plugins.otp_totp",
    "apps.core", "apps.accounts", "apps.catalog", "apps.payments",
    "apps.bookings", "apps.placements", "apps.subscriptions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "upl.urls"
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["axes.backends.AxesStandaloneBackend",
                           "django.contrib.auth.backends.ModelBackend"]

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "apps.core.context_processors.site_settings",
    ]},
}]

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = 60

CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache",
                      "LOCATION": env("REDIS_URL")}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]  # add Argon2 + `argon2-cffi` if desired

# ---- Brute-force protection
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1            # hours
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]

# ---- Sessions / cookies / HTTPS
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

# ---- CSP (tighten per page as you add third-party scripts)
CONTENT_SECURITY_POLICY = {"DIRECTIVES": {
    "default-src": ("'self'",),
    "img-src": ("'self'", "data:", "https://res.cloudinary.com"),
    "script-src": ("'self'", "https://js.paystack.co"),
    "style-src": ("'self'", "'unsafe-inline'"),
    "frame-src": ("https://checkout.paystack.com",),
    "frame-ancestors": ("'none'",),
}}

# ---- Files: paid files live OUTSIDE the web root and are served only by views
PRIVATE_MEDIA_ROOT = env("PRIVATE_MEDIA_ROOT")
MAX_UPLOAD_MB = 50
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o640
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# ---- Payments / email (secrets only from environment)
PAYSTACK_SECRET_KEY = env("PAYSTACK_SECRET_KEY")
PAYSTACK_PUBLIC_KEY = env("PAYSTACK_PUBLIC_KEY")
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST"); EMAIL_PORT = env.int("EMAIL_PORT", 587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
UPL_NOTIFY_EMAIL = env("UPL_NOTIFY_EMAIL")
ADMIN_URL = env("ADMIN_URL", default="admin/")

CELERY_BROKER_URL = env("REDIS_URL")
CELERY_TASK_ALWAYS_EAGER = DEBUG

LOGGING = {"version": 1, "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"upl.payments": {"handlers": ["console"], "level": "INFO"},
                "upl.security": {"handlers": ["console"], "level": "INFO"}}}

LANGUAGE_CODE = "en-ng"; TIME_ZONE = "Africa/Lagos"; USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- Auth routes
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "home"
PASSWORD_RESET_TIMEOUT = 60 * 60       # reset links valid 1 hour
WSGI_APPLICATION = "upl.wsgi.application"
