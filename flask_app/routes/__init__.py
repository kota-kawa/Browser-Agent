from __future__ import annotations

from flask import Flask

from .api_chat import api_chat_bp
from .api_controls import api_controls_bp
from .api_conversation import api_conversation_bp
from .api_history import api_history_bp
from .api_models import api_models_bp
from .ui import ui_bp


def register_routes(app: Flask) -> None:
	app.register_blueprint(ui_bp)
	app.register_blueprint(api_history_bp)
	app.register_blueprint(api_models_bp)
	app.register_blueprint(api_chat_bp)
	app.register_blueprint(api_controls_bp)
	app.register_blueprint(api_conversation_bp)
