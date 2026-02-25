from __future__ import annotations

# JP: UI テンプレートの配信ルート
# EN: Routes for serving UI templates
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from ..core.config import APP_STATIC_DIR, APP_TEMPLATE_DIR, logger
from ..core.env import _BROWSER_URL
from ..core.exceptions import AgentControllerError
from ..services.agent_runtime import get_agent_controller

templates = Jinja2Templates(directory=str(APP_TEMPLATE_DIR))
router = APIRouter()


@router.get('/favicon.ico')
def favicon() -> FileResponse:
	"""Serve the browser agent favicon for root requests."""

	# JP: .ico 形式のファビコンを返す
	# EN: Return .ico favicon
	return FileResponse(APP_STATIC_DIR / 'icons' / 'browser-agent.ico', media_type='image/x-icon')


@router.get('/favicon.png')
def favicon_png() -> FileResponse:
	"""Serve the png favicon variant for clients that request it."""

	# JP: PNG 形式のファビコンを返す
	# EN: Return PNG favicon
	return FileResponse(APP_STATIC_DIR / 'icons' / 'browser-agent.png')


@router.get('/')
def index(request: Request):
	# JP: ブラウザセッションのウォームアップを試みて UI を返す
	# EN: Warm up browser session if possible and serve the UI
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

	return templates.TemplateResponse('index.html', {'request': request, 'browser_url': _BROWSER_URL})


@router.get('/agent-result')
def agent_result(request: Request):
	# JP: 結果ページも同様にウォームアップを試みる
	# EN: Attempt warmup before serving the result page
	try:
		controller = get_agent_controller()
	except AgentControllerError:
		controller = None
	except Exception:
		logger.debug('Unexpected error while preparing browser controller on agent_result load', exc_info=True)
		controller = None

	if controller is not None:
		try:
			controller.ensure_start_page_ready()
		except Exception:
			logger.debug('Failed to warm up browser start page on agent_result load', exc_info=True)

	return templates.TemplateResponse('agent_result.html', {'request': request, 'browser_url': _BROWSER_URL})
