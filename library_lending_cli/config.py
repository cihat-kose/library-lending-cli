"""Load project-local connection settings without changing the process environment."""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
KEYS = {"DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"}


def database_config(env_file: Path | None = None) -> dict:
    values = {}
    path = ENV_FILE if env_file is None else env_file
    if path.is_file():
        for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, separator, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if not separator or key not in KEYS:
                raise ValueError(f"Invalid .env setting on line {number}; use DB_KEY=value")
            if value.startswith(("'", '"')):
                if len(value) < 2 or value[-1] != value[0]:
                    raise ValueError(f"Unclosed quote in .env on line {number}")
                value = value[1:-1]
            values[key] = value
    values.update({key: os.environ[key] for key in KEYS if key in os.environ})
    try:
        port = int(values.get("DB_PORT", "3306"))
    except ValueError as exc:
        raise ValueError("DB_PORT must be an integer") from exc
    if not 1 <= port <= 65535:
        raise ValueError("DB_PORT must be between 1 and 65535")
    name = values.get("DB_NAME", "library_lending")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", name):
        raise ValueError("DB_NAME must use ASCII letters, digits or underscores (max 64)")
    return {
        "host": values.get("DB_HOST", "127.0.0.1"),
        "port": port,
        "user": values.get("DB_USER", "library_app"),
        "password": values.get("DB_PASSWORD", ""),
        "database": name,
        "autocommit": True,
        "connection_timeout": 5,
    }
