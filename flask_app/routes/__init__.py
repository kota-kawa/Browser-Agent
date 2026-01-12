from __future__ import annotations

from fastapi import FastAPI

from .api_chat import router as api_chat_router
from .api_controls import router as api_controls_router
from .api_history import router as api_history_router
from .api_models import router as api_models_router
from .ui import router as ui_router


def register_routes(app: FastAPI) -> None:
	app.include_router(ui_router)
	app.include_router(api_history_router)
	app.include_router(api_models_router)
	app.include_router(api_chat_router)
	app.include_router(api_controls_router)
