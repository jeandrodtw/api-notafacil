#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Desativa a verificação de versão mínima e o suporte a cláusulas RETURNING no MariaDB < 10.5
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures

BaseDatabaseWrapper.check_database_version_supported = lambda self: None
DatabaseFeatures.can_return_rows_from_insert = False
DatabaseFeatures.can_return_columns_from_insert = False


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()