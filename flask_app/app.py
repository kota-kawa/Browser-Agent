from __future__ import annotations

# JP: FastAPI アプリ本体とミドルウェアを構成するエントリポイント
# EN: Entry point that wires the FastAPI app and middleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import APP_STATIC_DIR
from .routes import register_routes
from .services.agent_runtime import get_agent_controller
from .webarena import router as webarena_router

# JP: API サーバー本体
# EN: FastAPI application instance
app = FastAPI()
app.add_middleware(
	CORSMiddleware,
	allow_origins=['*'],
	allow_methods=['*'],
	allow_headers=['*'],
)
# JP: 静的アセットと WebArena ルートを登録
# EN: Register static assets and WebArena routes
app.mount('/static', StaticFiles(directory=str(APP_STATIC_DIR)), name='static')
app.include_router(webarena_router)
register_routes(app)


def _get_agent_controller():
	# JP: 遅延初期化されたコントローラーを取得
	# EN: Fetch the lazily initialized controller
	return get_agent_controller()


app.state.get_agent_controller = _get_agent_controller


if __name__ == '__main__':
	import uvicorn

	# JP: 直接起動時のデフォルト設定
	# EN: Default settings for direct execution
	uvicorn.run('flask_app.app:app', host='0.0.0.0', port=5005, reload=False)
