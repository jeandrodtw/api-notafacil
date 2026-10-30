"""
Configurações do projeto NotaFácil API.

Valores sensíveis são lidos de variáveis de ambiente, com um padrão
seguro apenas para desenvolvimento (aula / máquina local).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Lê o arquivo .env (se existir) e coloca os valores nas variáveis de ambiente
load_dotenv(BASE_DIR / ".env")


def env_bool(nome, padrao):
    """Lê uma variável de ambiente como booleano ("True"/"False")."""
    return os.environ.get(nome, str(padrao)).lower() in ("1", "true", "yes", "sim")


# --- Segurança (troque em produção!) ---
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-inseguro-troque-esta-chave-em-producao",
)
DEBUG = env_bool("DJANGO_DEBUG", True)

# "*" permite acessar pelo IP da máquina na rede (celular, emulador)
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceiros
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "drf_spectacular",
    # Nosso app
    "notas",
]

MIDDLEWARE = [
    # O CORS precisa vir antes do CommonMiddleware
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Banco de dados (MySQL) ---
# Os dados de conexão vêm do arquivo .env (veja o .env.example).
# O driver é o PyMySQL, ativado em config/__init__.py.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME", "notafacil"),
        "USER": os.environ.get("DB_USER", "root"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        "OPTIONS": {
            # utf8mb4 guarda qualquer caractere (acentos, emojis)
            "charset": "utf8mb4",
            # modo estrito: o MySQL recusa dados inválidos em vez de cortá-los
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        "TEST": {
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_unicode_ci",
        },
    }
}

# Usamos as regras de senha do próprio serializer de registro (mínimo 6),
# então os validadores padrão do Django não são aplicados na API.
AUTH_PASSWORD_VALIDATORS = []


# --- Idioma e fuso horário ---
# pt-br faz o Django e o DRF responderem as mensagens de erro em português
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Campo_Grande"
USE_I18N = True
USE_TZ = True


# --- Arquivos estáticos e mídia (fotos das notas) ---
STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Django REST Framework ---
REST_FRAMEWORK = {
    # Só Token: sem SessionAuthentication, token ausente/inválido gera 401 (e não 403)
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    # Tudo exige login, exceto as views marcadas com AllowAny (login e registro)
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Documentação Swagger (/api/docs/)
SPECTACULAR_SETTINGS = {
    "TITLE": "NotaFácil API",
    "DESCRIPTION": "API para gestão de notas fiscais e garantias de produtos.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}


# --- CORS (liberado em desenvolvimento) ---
CORS_ALLOW_ALL_ORIGINS = env_bool("DJANGO_CORS_ALLOW_ALL", DEBUG)
