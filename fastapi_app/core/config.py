from __future__ import annotations

import logging
import os
from pathlib import Path

# JP: アプリのログ設定とパス設定をまとめる
# EN: Centralized logging and path configuration
from browser_use.env_loader import load_secrets_env

# JP: secrets.env を読み込み、環境変数に反映する
# EN: Load secrets.env into environment variables
load_secrets_env()

# JP: FastAPI / Flask 互換の環境変数を考慮してログレベルを決定
# EN: Derive log level from FastAPI/Flask compatible env vars
log_level = os.environ.get('FASTAPI_LOG_LEVEL') or os.environ.get('FLASK_LOG_LEVEL', 'INFO')
logging.basicConfig(level=log_level)
logger = logging.getLogger('fastapi_app.app')

# JP: テンプレートと静的ファイルのベースディレクトリ
# EN: Base directories for templates and static assets
APP_STATIC_DIR = Path(__file__).resolve().parents[1] / 'static'
APP_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / 'templates'
