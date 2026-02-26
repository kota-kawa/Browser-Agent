# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# JP: FastAPI アプリ本体とミドルウェアを構成するエントリポイント
# EN: Entry point that wires the FastAPI app and middleware
from typing import TYPE_CHECKING

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi import FastAPI
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi.middleware.cors import CORSMiddleware
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi.staticfiles import StaticFiles

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .core.config import APP_STATIC_DIR
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .routes import register_routes
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .services.agent_runtime import get_agent_controller
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .webarena import router as webarena_router

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from .services.agent_controller import BrowserAgentController

# JP: API サーバー本体
# EN: FastAPI application instance
app = FastAPI()
# EN: Evaluate an expression.
# JP: 式を評価する。
app.add_middleware(
	CORSMiddleware,
	allow_origins=['*'],
	allow_methods=['*'],
	allow_headers=['*'],
)
# JP: 静的アセットと WebArena ルートを登録
# EN: Register static assets and WebArena routes
app.mount('/static', StaticFiles(directory=str(APP_STATIC_DIR)), name='static')
# EN: Evaluate an expression.
# JP: 式を評価する。
app.include_router(webarena_router)
# EN: Evaluate an expression.
# JP: 式を評価する。
register_routes(app)


# EN: Define function `_get_agent_controller`.
# JP: 関数 `_get_agent_controller` を定義する。
def _get_agent_controller() -> BrowserAgentController:
	# JP: 遅延初期化されたコントローラーを取得
	# EN: Fetch the lazily initialized controller
	return get_agent_controller()


# EN: Assign value to target variable.
# JP: target variable に値を代入する。
app.state.get_agent_controller = _get_agent_controller


# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if __name__ == '__main__':
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import uvicorn

	# JP: 直接起動時のデフォルト設定
	# EN: Default settings for direct execution
	uvicorn.run('fastapi_app.app:app', host='0.0.0.0', port=5005, reload=False)
