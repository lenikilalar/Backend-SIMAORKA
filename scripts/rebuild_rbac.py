"""
Script to rebuild RBAC tables to match new schema.
"""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'

import django
django.setup()

from django.db import connection

# Drop old tables and recreate
SQL_COMMANDS = [
    "DROP TABLE IF EXISTS role_permissions CASCADE;",
    "DROP TABLE IF EXISTS permissions CASCADE;",
    "DROP TABLE IF EXISTS roles CASCADE;",
    """
    CREATE TABLE IF NOT EXISTS roles (
        id SERIAL PRIMARY KEY,
        code VARCHAR(100) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        scope VARCHAR(20) NOT NULL,
        description TEXT DEFAULT ''
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS permissions (
        id SERIAL PRIMARY KEY,
        code VARCHAR(100) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT DEFAULT ''
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS role_permissions (
        id SERIAL PRIMARY KEY,
        role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
        permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
        UNIQUE(role_id, permission_id)
    );
    """,
]

with connection.cursor() as cursor:
    for sql in SQL_COMMANDS:
        try:
            print(f"Executing: {sql[:50]}...")
            cursor.execute(sql)
            print("  OK")
        except Exception as e:
            print(f"  Error: {e}")

print("\nDatabase rebuild complete!")
