"""Connection settings.  Order of priority: environment variables > config.json > defaults."""
import json
import os

DEFAULTS = {"host": "localhost", "port": 3306, "user": "pharmacy_app",
            "password": "pharmacy123", "database": "pharmacy_db", "unix_socket": None}
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
ENV = {"host": "PHARMACY_HOST", "port": "PHARMACY_PORT", "user": "PHARMACY_USER",
       "password": "PHARMACY_PASSWORD", "database": "PHARMACY_DB", "unix_socket": "PHARMACY_SOCKET"}


def load_config():
    cfg = dict(DEFAULTS)
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as fh:
            cfg.update({k: v for k, v in json.load(fh).items() if k in cfg})
    for key, env in ENV.items():
        if os.getenv(env):
            cfg[key] = int(os.environ[env]) if key == "port" else os.environ[env]
    return cfg


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
        json.dump({k: v for k, v in cfg.items() if k != "unix_socket"}, fh, indent=2)
