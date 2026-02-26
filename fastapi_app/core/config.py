# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
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
# EN: Evaluate an expression.
# JP: 式を評価する。
logging.basicConfig(level=log_level)
# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger('fastapi_app.app')

# JP: テンプレートと静的ファイルのベースディレクトリ
# EN: Base directories for templates and static assets
APP_STATIC_DIR = Path(__file__).resolve().parents[1] / 'static'
# EN: Assign value to APP_TEMPLATE_DIR.
# JP: APP_TEMPLATE_DIR に値を代入する。
APP_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / 'templates'
