from __future__ import annotations

# JP: ルート登録の集約モジュール
# EN: Central router registration module
from fastapi import FastAPI

from .api_chat import router as api_chat_router
from .api_controls import router as api_controls_router
from .api_history import router as api_history_router
from .api_models import router as api_models_router
from .api_user_profile import router as api_user_profile_router
from .ui import router as ui_router


# EN: Define function `register_routes`.
# JP: 関数 `register_routes` を定義する。
def register_routes(app: FastAPI) -> None:
	# JP: UI と API のルートをまとめて登録
	# EN: Register UI and API routes in one place
	app.include_router(ui_router)
	app.include_router(api_history_router)
	app.include_router(api_models_router)
	app.include_router(api_user_profile_router)
	app.include_router(api_chat_router)
	app.include_router(api_controls_router)
