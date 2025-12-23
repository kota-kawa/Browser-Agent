from __future__ import annotations

from flask import Blueprint, render_template, send_from_directory
from flask.typing import ResponseReturnValue

from ..core.config import APP_STATIC_DIR, logger
from ..core.env import _BROWSER_URL
from ..core.exceptions import AgentControllerError
from ..services.agent_runtime import get_agent_controller

ui_bp = Blueprint('ui', __name__)


@ui_bp.route('/favicon.ico')
def favicon() -> ResponseReturnValue:
	"""Serve the browser agent favicon for root requests."""

	return send_from_directory(
		APP_STATIC_DIR / 'icons',
		'browser-agent.ico',
		mimetype='image/x-icon',
	)


@ui_bp.route('/favicon.png')
def favicon_png() -> ResponseReturnValue:
	"""Serve the png favicon variant for clients that request it."""

	return send_from_directory(APP_STATIC_DIR / 'icons', 'browser-agent.png')


@ui_bp.route('/')
def index() -> str:
	try:
		controller = get_agent_controller()
	except AgentControllerError:
		controller = None
	except Exception:
		logger.debug('Unexpected error while preparing browser controller on index load', exc_info=True)
		controller = None

	if controller is not None:
		try:
			controller.ensure_start_page_ready()
		except Exception:
			logger.debug('Failed to warm up browser start page on index load', exc_info=True)

	return render_template('index.html', browser_url=_BROWSER_URL)
