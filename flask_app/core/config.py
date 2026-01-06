from __future__ import annotations

import logging
import os
from pathlib import Path

from browser_use.env_loader import load_secrets_env

load_secrets_env()

log_level = os.environ.get('FASTAPI_LOG_LEVEL') or os.environ.get('FLASK_LOG_LEVEL', 'INFO')
logging.basicConfig(level=log_level)
logger = logging.getLogger('flask_app.app')

APP_STATIC_DIR = Path(__file__).resolve().parents[1] / 'static'
APP_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / 'templates'
