# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# JP: UI テンプレートの配信ルート
# EN: Routes for serving UI templates
from fastapi import APIRouter, Request
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi.responses import FileResponse, Response
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi.templating import Jinja2Templates

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.config import APP_STATIC_DIR, APP_TEMPLATE_DIR, logger
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.env import _BROWSER_URL
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.exceptions import AgentControllerError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..services.agent_runtime import get_agent_controller

# EN: Assign value to templates.
# JP: templates に値を代入する。
templates = Jinja2Templates(directory=str(APP_TEMPLATE_DIR))
# EN: Assign value to router.
# JP: router に値を代入する。
router = APIRouter()


# EN: Define function `favicon`.
# JP: 関数 `favicon` を定義する。
@router.get('/favicon.ico')
def favicon() -> FileResponse:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Serve the browser agent favicon for root requests."""

	# JP: .ico 形式のファビコンを返す
	# EN: Return .ico favicon
	return FileResponse(APP_STATIC_DIR / 'icons' / 'browser-agent.ico', media_type='image/x-icon')


# EN: Define function `favicon_png`.
# JP: 関数 `favicon_png` を定義する。
@router.get('/favicon.png')
def favicon_png() -> FileResponse:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Serve the png favicon variant for clients that request it."""

	# JP: PNG 形式のファビコンを返す
	# EN: Return PNG favicon
	return FileResponse(APP_STATIC_DIR / 'icons' / 'browser-agent.png')


# EN: Define function `index`.
# JP: 関数 `index` を定義する。
@router.get('/')
def index(request: Request) -> Response:
	# JP: ブラウザセッションのウォームアップを試みて UI を返す
	# EN: Warm up browser session if possible and serve the UI
	try:
		# EN: Assign value to controller.
		# JP: controller に値を代入する。
		controller = get_agent_controller()
	except AgentControllerError:
		# EN: Assign value to controller.
		# JP: controller に値を代入する。
		controller = None
	except Exception:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Unexpected error while preparing browser controller on index load', exc_info=True)
		# EN: Assign value to controller.
		# JP: controller に値を代入する。
		controller = None

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if controller is not None:
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			controller.ensure_start_page_ready()
		except Exception:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug('Failed to warm up browser start page on index load', exc_info=True)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return templates.TemplateResponse('index.html', {'request': request, 'browser_url': _BROWSER_URL})


# EN: Define function `agent_result`.
# JP: 関数 `agent_result` を定義する。
@router.get('/agent-result')
def agent_result(request: Request) -> Response:
	# JP: 結果ページも同様にウォームアップを試みる
	# EN: Attempt warmup before serving the result page
	try:
		# EN: Assign value to controller.
		# JP: controller に値を代入する。
		controller = get_agent_controller()
	except AgentControllerError:
		# EN: Assign value to controller.
		# JP: controller に値を代入する。
		controller = None
	except Exception:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Unexpected error while preparing browser controller on agent_result load', exc_info=True)
		# EN: Assign value to controller.
		# JP: controller に値を代入する。
		controller = None

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if controller is not None:
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			controller.ensure_start_page_ready()
		except Exception:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug('Failed to warm up browser start page on agent_result load', exc_info=True)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return templates.TemplateResponse('agent_result.html', {'request': request, 'browser_url': _BROWSER_URL})
