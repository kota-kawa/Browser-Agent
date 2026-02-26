# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import datetime
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import math
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import statistics
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import string
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import subprocess
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import urllib.error
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import urllib.request
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from contextlib import suppress
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from difflib import SequenceMatcher
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING, Any, Mapping, Sequence, TypedDict, cast
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from urllib.parse import urlparse

# JP: WebArena ベンチマーク実行用ルート
# EN: Routes for running WebArena benchmark tasks
from fastapi import Request
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi.responses import JSONResponse
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi.templating import Jinja2Templates
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from starlette.responses import Response

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.core.config import APP_TEMPLATE_DIR
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.core.env import _BROWSER_URL, _WEBARENA_MAX_STEPS, _normalize_start_url
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.services.formatting import _format_history_messages
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.routes.utils import read_json_payload

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from . import router

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)

# EN: Assign value to templates.
# JP: templates に値を代入する。
templates = Jinja2Templates(directory=str(APP_TEMPLATE_DIR))

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.agent.views import AgentHistoryList

	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from fastapi_app.services.agent_controller import BrowserAgentController


# EN: Define class `WebArenaTask`.
# JP: クラス `WebArenaTask` を定義する。
class WebArenaTask(TypedDict, total=False):
	# EN: Assign annotated value to task_id.
	# JP: task_id に型付きの値を代入する。
	task_id: int | str
	# EN: Assign annotated value to intent.
	# JP: intent に型付きの値を代入する。
	intent: str
	# EN: Assign annotated value to start_url.
	# JP: start_url に型付きの値を代入する。
	start_url: str
	# EN: Assign annotated value to require_login.
	# JP: require_login に型付きの値を代入する。
	require_login: bool
	# EN: Assign annotated value to sites.
	# JP: sites に型付きの値を代入する。
	sites: list[str]
	# EN: Assign annotated value to eval.
	# JP: eval に型付きの値を代入する。
	eval: dict[str, Any]
	# EN: Assign annotated value to intent_template_id.
	# JP: intent_template_id に型付きの値を代入する。
	intent_template_id: int | str


# EN: Define class `WebArenaStep`.
# JP: クラス `WebArenaStep` を定義する。
class WebArenaStep(TypedDict):
	# EN: Assign annotated value to step.
	# JP: step に型付きの値を代入する。
	step: int
	# EN: Assign annotated value to content.
	# JP: content に型付きの値を代入する。
	content: str


# EN: Define class `WebArenaTaskResult`.
# JP: クラス `WebArenaTaskResult` を定義する。
class WebArenaTaskResult(TypedDict):
	# EN: Assign annotated value to task_id.
	# JP: task_id に型付きの値を代入する。
	task_id: int | str | None
	# EN: Assign annotated value to success.
	# JP: success に型付きの値を代入する。
	success: bool
	# EN: Assign annotated value to summary.
	# JP: summary に型付きの値を代入する。
	summary: str | None
	# EN: Assign annotated value to steps.
	# JP: steps に型付きの値を代入する。
	steps: list[WebArenaStep]
	# EN: Assign annotated value to evaluation.
	# JP: evaluation に型付きの値を代入する。
	evaluation: str

# JP: ローカルで利用可能な環境のみ許可
# EN: Only these environments are provisioned locally
SUPPORTED_SITES = {'shopping', 'shopping_admin', 'reddit', 'gitlab'}

# JP: タスク一覧を読み込み、サポート対象に絞る
# EN: Load tasks from JSON and filter to supported environments
TASKS_FILE = os.path.join(os.path.dirname(__file__), 'tasks_data/test.json')


# EN: Define function `_load_tasks`.
# JP: 関数 `_load_tasks` を定義する。
def _load_tasks() -> tuple[list[WebArenaTask], list[WebArenaTask]]:
	# JP: tasks_data/test.json を読み込み、対応サイトのみ抽出
	# EN: Load tasks_data/test.json and keep only supported-site tasks
	try:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with open(TASKS_FILE, encoding='utf-8') as f:
			# EN: Assign value to all_tasks.
			# JP: all_tasks に値を代入する。
			all_tasks = cast(list[WebArenaTask], json.load(f))
	except Exception:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('Could not load WebArena tasks from %s', TASKS_FILE)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [], []

	# EN: Define function `_is_supported`.
	# JP: 関数 `_is_supported` を定義する。
	def _is_supported(task: WebArenaTask) -> bool:
		# EN: Assign value to sites.
		# JP: sites に値を代入する。
		sites = task.get('sites', []) or []
		# Keep tasks that only reference environments we actually have
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return bool(sites) and all(site in SUPPORTED_SITES for site in sites)

	# EN: Assign value to supported_tasks.
	# JP: supported_tasks に値を代入する。
	supported_tasks = [t for t in all_tasks if _is_supported(t)]

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if len(supported_tasks) != len(all_tasks):
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info(
			'WebArena tasks filtered: %s supported of %s total (allowed sites: %s)',
			len(supported_tasks),
			len(all_tasks),
			','.join(sorted(SUPPORTED_SITES)),
		)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return all_tasks, supported_tasks


# EN: Assign value to target variable.
# JP: target variable に値を代入する。
ALL_WEBARENA_TASKS, WEBARENA_TASKS = _load_tasks()

# Optional external reset hooks
# EN: Assign value to RESET_COMMAND.
# JP: RESET_COMMAND に値を代入する。
RESET_COMMAND = os.getenv(
	'WEBARENA_RESET_COMMAND'
)  # e.g., "docker compose -f bin/webarena/docker-compose.webarena.yml restart shopping shopping_admin gitlab forum"

# Set a sensible default for RESET_COMMAND if not provided and file exists
# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if not RESET_COMMAND and not os.getenv('WEBARENA_RESET_URL'):
	# EN: Assign value to _default_compose_path.
	# JP: _default_compose_path に値を代入する。
	_default_compose_path = os.path.join(os.getcwd(), 'bin/webarena/docker-compose.webarena.yml')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if os.path.exists(_default_compose_path):
		# EN: Assign value to RESET_COMMAND.
		# JP: RESET_COMMAND に値を代入する。
		RESET_COMMAND = f'docker compose -f {_default_compose_path} restart shopping shopping_admin gitlab forum'
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info(f'Configured default WebArena reset command: {RESET_COMMAND}')

# EN: Assign value to RESET_URL.
# JP: RESET_URL に値を代入する。
RESET_URL = os.getenv('WEBARENA_RESET_URL')  # e.g., "http://localhost:7000/reset"


# EN: Define function `_build_default_env_urls`.
# JP: 関数 `_build_default_env_urls` を定義する。
def _build_default_env_urls() -> dict[str, str]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	When the app runs inside Docker (/.dockerenv present), the agent and the
	browser containers share the same user-defined network (`multi_agent_network`).
	In that case the WebArena backends are reachable via their service names
	(shopping, shopping_admin, gitlab, forum) rather than localhost:*.

	When running the app directly on the host machine, we still want to keep
	the existing localhost-based defaults so the UI works without Docker.
	"""
	# JP: Docker 内外で到達可能な URL を切り替える
	# EN: Switch defaults based on whether we are inside Docker
	in_container = os.path.exists('/.dockerenv') or os.environ.get('CONTAINERIZED') == '1'

	# EN: Assign value to container_defaults.
	# JP: container_defaults に値を代入する。
	container_defaults = {
		'shopping': 'http://shopping:80',
		'shopping_admin': 'http://shopping_admin:80',
		'gitlab': 'http://gitlab:8023',
		'reddit': 'http://forum:80',
		'wikipedia': 'http://wikipedia:80',
	}

	# EN: Assign value to host_defaults.
	# JP: host_defaults に値を代入する。
	host_defaults = {
		'shopping': 'http://localhost:7770',
		'shopping_admin': 'http://localhost:7780',
		'gitlab': 'http://localhost:8023',
		'reddit': 'http://localhost:9999',
		'wikipedia': 'http://wikipedia:80',
	}

	# EN: Assign value to defaults.
	# JP: defaults に値を代入する。
	defaults = container_defaults if in_container else host_defaults

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return {
		'shopping': os.getenv('WEBARENA_SHOPPING_URL', defaults['shopping']),
		'shopping_admin': os.getenv('WEBARENA_SHOPPING_ADMIN_URL', defaults['shopping_admin']),
		'gitlab': os.getenv('WEBARENA_GITLAB_URL', defaults['gitlab']),
		'reddit': os.getenv('WEBARENA_REDDIT_URL', defaults['reddit']),
		'wikipedia': os.getenv('WEBARENA_WIKIPEDIA_URL', defaults['wikipedia']),
	}


# JP: Docker/ホストを自動判定した既定の環境URL
# EN: Default env URLs auto-selected for host vs container
DEFAULT_ENV_URLS = _build_default_env_urls()


# EN: Define function `index`.
# JP: 関数 `index` を定義する。
@router.get('/webarena')
def index(request: Request) -> Response:
	# JP: WebArena UI を返す
	# EN: Serve the WebArena UI
	return templates.TemplateResponse(
		'webarena.html',
		{
			'request': request,
			'browser_url': _BROWSER_URL,
			'env_urls': DEFAULT_ENV_URLS,
			'supported_sites': sorted(SUPPORTED_SITES),
		},
	)


# EN: Define function `get_tasks`.
# JP: 関数 `get_tasks` を定義する。
@router.get('/webarena/tasks')
def get_tasks(page: int = 1, per_page: int = 50, site: str | None = None) -> JSONResponse:
	# JP: ページングされたタスク一覧を返す
	# EN: Return a paginated list of tasks
	site_filter = site

	# EN: Assign value to tasks.
	# JP: tasks に値を代入する。
	tasks = WEBARENA_TASKS
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if site_filter and site_filter in SUPPORTED_SITES:
		# User request: Only show tasks that are exclusively for this site.
		# Multi-site tasks should only appear in "ALL".
		# EN: Assign value to tasks.
		# JP: tasks に値を代入する。
		tasks = [t for t in tasks if t.get('sites') and len(t['sites']) == 1 and site_filter in t['sites']]

	# EN: Assign value to start.
	# JP: start に値を代入する。
	start = (page - 1) * per_page
	# EN: Assign value to end.
	# JP: end に値を代入する。
	end = start + per_page
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return JSONResponse({'tasks': tasks[start:end], 'total': len(tasks), 'page': page, 'per_page': per_page})


# EN: Define function `_resolve_start_url`.
# JP: 関数 `_resolve_start_url` を定義する。
def _resolve_start_url(task: WebArenaTask, env_urls_override: Mapping[str, str] | None = None) -> str:
	# JP: タスク内のプレースホルダを実URLに置換
	# EN: Replace placeholders in task start_url with actual URLs
	start_url = task.get('start_url', '')
	# EN: Assign value to env_urls.
	# JP: env_urls に値を代入する。
	env_urls = DEFAULT_ENV_URLS.copy()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if env_urls_override:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		env_urls.update(env_urls_override)

	# EN: Assign value to replacements.
	# JP: replacements に値を代入する。
	replacements = {
		'__SHOPPING__': env_urls.get('shopping'),
		'__SHOPPING_ADMIN__': env_urls.get('shopping_admin'),
		'__GITLAB__': env_urls.get('gitlab'),
		'__REDDIT__': env_urls.get('reddit'),
		'__WIKIPEDIA__': env_urls.get('wikipedia', 'https://en.wikipedia.org/wiki'),
	}

	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for placeholder, base_url in replacements.items():
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if base_url and placeholder in start_url:
			# EN: Assign value to start_url.
			# JP: start_url に値を代入する。
			start_url = start_url.replace(placeholder, base_url)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return start_url


# EN: Define function `_reset_state`.
# JP: 関数 `_reset_state` を定義する。
def _reset_state(
	controller: BrowserAgentController,
	sites: Sequence[str],
	start_url: str | None = None,
) -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Best-effort reset for WebArena between tasks.
	- Always reset the browser controller session (clears cookies/storage).
	- Optionally call external reset hook via command or HTTP endpoint for backend state.
	"""
	# JP: タスク間の状態をできる限りリセットする
	# EN: Best-effort reset between tasks
	# 1) Reset browser session
	try:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		controller.reset()
		# Apply the next start page (task-specific when provided) so warmup/cleanup
		# happens on the correct environment.
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if start_url:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			controller.set_start_page(start_url)
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			controller.set_start_page(None)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		controller.ensure_start_page_ready()
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with suppress(Exception):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			controller.close_additional_tabs(start_url)
	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('Browser reset failed: %s', e)

	# 2) External reset hook (if configured)
	# EN: Assign value to sites_csv.
	# JP: sites_csv に値を代入する。
	sites_csv = ','.join(sites or [])

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if RESET_URL:
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to data.
			# JP: data に値を代入する。
			data = json.dumps({'sites': sites or []}).encode('utf-8')
			# EN: Assign value to req.
			# JP: req に値を代入する。
			req = urllib.request.Request(RESET_URL, data=data, headers={'Content-Type': 'application/json'}, method='POST')
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with urllib.request.urlopen(req, timeout=180) as resp:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('Reset URL responded with status %s', resp.getcode())
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning('External reset via URL failed: %s', e)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif RESET_COMMAND:
		# EN: Assign value to cmd.
		# JP: cmd に値を代入する。
		cmd = RESET_COMMAND.format(sites=sites_csv)
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			subprocess.run(cmd, shell=True, check=True, timeout=300)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info('Executed reset command: %s', cmd)
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning('External reset command failed: %s', e)
	else:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if sites:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning('No WEBARENA_RESET_COMMAND/URL configured. Only browser session was reset for sites: %s', sites_csv)
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning('No WEBARENA_RESET_COMMAND/URL configured. Only browser session was reset.')


# JP: WebArena のログイン情報を system prompt に追加
# EN: Inject WebArena credentials into the system prompt
WEBARENA_CREDENTIALS_PROMPT = f"""
### WebArena Environment Credentials
For tasks in the WebArena environment, use the following credentials if required:
- Shopping (Magento): Email "{os.getenv('WEBARENA_MAGENTO_EMAIL', 'emma.lopez@gmail.com')}", Password "{os.getenv('WEBARENA_MAGENTO_PASSWORD', 'Password.123')}"
- Shopping Admin: Username "{os.getenv('WEBARENA_ADMIN_USERNAME', 'admin')}", Password "{os.getenv('WEBARENA_ADMIN_PASSWORD', 'admin1234')}"
- GitLab: Username "{os.getenv('WEBARENA_GITLAB_USERNAME', 'root')}", Password "{os.getenv('WEBARENA_GITLAB_PASSWORD', '5iveL!fe')}"
- Reddit (PostMill): Username "{os.getenv('WEBARENA_REDDIT_USERNAME', 'user1')}", Password "{os.getenv('WEBARENA_REDDIT_PASSWORD', 'password')}"
"""


# EN: Define function `_run_single_task`.
# JP: 関数 `_run_single_task` を定義する。
def _run_single_task(
	task: WebArenaTask,
	controller: BrowserAgentController,
	env_urls_override: Mapping[str, str] | None = None,
	start_url_override: str | None = None,
) -> WebArenaTaskResult:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Execute one WebArena task with the shared controller and return the result payload.
	"""
	# JP: タスク1件を実行し、結果のサマリを作成
	# EN: Execute a single task and build a result payload
	intent = task.get('intent', '')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not intent:
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError('Task is missing intent.')

	# EN: Assign value to start_url.
	# JP: start_url に値を代入する。
	start_url = _resolve_start_url(task, env_urls_override)

	# EN: Assign value to full_prompt.
	# JP: full_prompt に値を代入する。
	full_prompt = intent
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if start_url:
		# EN: Assign value to full_prompt.
		# JP: full_prompt に値を代入する。
		full_prompt = f'Navigate to {start_url} first. Then, {intent}'

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if task.get('require_login'):
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		full_prompt += ' (Note: This task may require logging in. If credentials are unknown, fail gracefully.)'

	# EN: Assign value to start_url_for_reset.
	# JP: start_url_for_reset に値を代入する。
	start_url_for_reset = start_url_override or start_url
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	_reset_state(controller, task.get('sites') or [], start_url_for_reset)

	# EN: Assign value to result.
	# JP: result に値を代入する。
	result = controller.run(
		full_prompt,
		additional_system_message=WEBARENA_CREDENTIALS_PROMPT,
		max_steps=_WEBARENA_MAX_STEPS,
	)
	# EN: Assign value to history.
	# JP: history に値を代入する。
	history = result.history

	# EN: Assign value to evaluation_msg.
	# JP: evaluation_msg に値を代入する。
	evaluation_msg = _evaluate_result(history, task, controller)
	# EN: Assign value to success.
	# JP: success に値を代入する。
	success = history.is_successful()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if 'Failure' in evaluation_msg:
		# EN: Assign value to success.
		# JP: success に値を代入する。
		success = False
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif success is None or success is False:
		# 評価で失敗が出ていなくても、エージェントの自己申告が未設定/失敗なら失敗扱い
		# EN: Assign value to success.
		# JP: success に値を代入する。
		success = False

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return {
		'task_id': task.get('task_id'),
		'success': success,
		'summary': history.final_result(),
		'steps': [{'step': n, 'content': c} for n, c in _format_history_messages(history)],
		'evaluation': evaluation_msg,
	}


# EN: Define function `_compute_aggregate_metrics`.
# JP: 関数 `_compute_aggregate_metrics` を定義する。
def _compute_aggregate_metrics(
	results: Sequence[WebArenaTaskResult],
	selected_tasks: Sequence[WebArenaTask],
	max_steps: int,
) -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Compute extended aggregate statistics for a WebArena batch run."""

	# JP: 成功率やステップ統計などの集計指標を計算
	# EN: Compute aggregate metrics (success rate, step stats, etc.)
	if not results:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {}

	# EN: Assign value to total.
	# JP: total に値を代入する。
	total = len(results)
	# EN: Assign value to success_flags.
	# JP: success_flags に値を代入する。
	success_flags = [bool(r.get('success')) for r in results]
	# EN: Assign value to success_count.
	# JP: success_count に値を代入する。
	success_count = sum(success_flags)
	# EN: Assign value to sr.
	# JP: sr に値を代入する。
	sr = success_count / total if total else 0.0

	# 95% CI for success rate (normal approximation, clamped to [0,1])
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if total:
		# EN: Assign value to se.
		# JP: se に値を代入する。
		se = math.sqrt(sr * (1 - sr) / total)
		# EN: Assign value to margin.
		# JP: margin に値を代入する。
		margin = 1.96 * se
		# EN: Assign value to ci_lower.
		# JP: ci_lower に値を代入する。
		ci_lower = max(0.0, sr - margin)
		# EN: Assign value to ci_upper.
		# JP: ci_upper に値を代入する。
		ci_upper = min(1.0, sr + margin)
	else:
		# EN: Assign value to ci_lower, ci_upper.
		# JP: ci_lower, ci_upper に値を代入する。
		ci_lower = ci_upper = 0.0

	# Template-macro SR (average of per-template success rates)
	# EN: Assign annotated value to template_results.
	# JP: template_results に型付きの値を代入する。
	template_results: dict[str | int, list[bool]] = {}
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for task, result in zip(selected_tasks, results):
		# EN: Assign value to template_id.
		# JP: template_id に値を代入する。
		template_id = task.get('intent_template_id')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if template_id is None:
			# EN: Continue to the next loop iteration.
			# JP: ループの次の反復に進む。
			continue
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		template_results.setdefault(template_id, []).append(bool(result.get('success')))

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if template_results:
		# EN: Assign value to template_rates.
		# JP: template_rates に値を代入する。
		template_rates = [sum(flags) / len(flags) for flags in template_results.values() if flags]
		# EN: Assign value to template_macro_sr.
		# JP: template_macro_sr に値を代入する。
		template_macro_sr = sum(template_rates) / len(template_rates) if template_rates else 0.0
	else:
		# EN: Assign value to template_macro_sr.
		# JP: template_macro_sr に値を代入する。
		template_macro_sr = 0.0

	# Step statistics
	# EN: Assign value to step_counts_success.
	# JP: step_counts_success に値を代入する。
	step_counts_success = [len(r.get('steps') or []) for r in results if r.get('success')]
	# EN: Assign value to step_counts_overall.
	# JP: step_counts_overall に値を代入する。
	step_counts_overall = [len(r.get('steps') or []) if r.get('success') else max_steps for r in results]

	# EN: Define function `_safe_mean`.
	# JP: 関数 `_safe_mean` を定義する。
	def _safe_mean(values: list[int]) -> float:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return statistics.mean(values) if values else 0.0

	# EN: Define function `_safe_median`.
	# JP: 関数 `_safe_median` を定義する。
	def _safe_median(values: list[int]) -> float:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return float(statistics.median(values)) if values else 0.0

	# EN: Define function `_p90`.
	# JP: 関数 `_p90` を定義する。
	def _p90(values: list[int]) -> float:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not values:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 0.0
		# EN: Assign value to sorted_vals.
		# JP: sorted_vals に値を代入する。
		sorted_vals = sorted(values)
		# EN: Assign value to idx.
		# JP: idx に値を代入する。
		idx = max(0, min(len(sorted_vals) - 1, math.ceil(0.9 * len(sorted_vals)) - 1))
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return float(sorted_vals[idx])

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return {
		'success_rate': round(sr * 100, 2),
		'success_rate_ci_95': {'lower': round(ci_lower * 100, 2), 'upper': round(ci_upper * 100, 2)},
		'template_macro_sr': round(template_macro_sr * 100, 2),
		'average_steps_success_only': round(_safe_mean(step_counts_success), 2),
		'average_steps_overall_with_failures_as_max': round(_safe_mean(step_counts_overall), 2),
		'median_steps_success_only': round(_safe_median(step_counts_success), 2),
		'p90_steps_success_only': round(_p90(step_counts_success), 2),
		'max_steps': max_steps,
	}


# EN: Define function `_apply_start_page_override`.
# JP: 関数 `_apply_start_page_override` を定義する。
def _apply_start_page_override(
	selected_site: str | None,
	env_urls_override: Mapping[str, str] | None = None,
) -> str | None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	When the WebArena UI is used with an environment filter, start the agent on that site's base URL.
	This affects only the WebArena flow (root / is unchanged).
	"""
	# JP: サイトフィルタ時は対象サイトのURLを開始ページにする
	# EN: Use the selected site's base URL as the start page when filtering
	if not selected_site or selected_site not in SUPPORTED_SITES:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Assign value to env_urls.
	# JP: env_urls に値を代入する。
	env_urls = DEFAULT_ENV_URLS.copy()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if env_urls_override:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		env_urls.update(env_urls_override)

	# EN: Assign value to start_url.
	# JP: start_url に値を代入する。
	start_url = env_urls.get(selected_site)
	# EN: Assign value to normalized.
	# JP: normalized に値を代入する。
	normalized = _normalize_start_url(start_url) if start_url else None
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return normalized


# EN: Define function `_evaluate_result`.
# JP: 関数 `_evaluate_result` を定義する。
def _evaluate_result(
	history: AgentHistoryList,
	task: WebArenaTask | None,
	controller: BrowserAgentController,
) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Evaluation logic based on WebArena 'eval' fields.
	"""
	# JP: タスクに紐づく評価条件で成功/失敗を判定
	# EN: Evaluate success based on task-specific criteria
	if not task:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'Custom task - no automated evaluation'

	# EN: Define function `_normalize_text`.
	# JP: 関数 `_normalize_text` を定義する。
	def _normalize_text(text: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Lowercase, remove punctuation, collapse whitespace for robust matching."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not text:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ''
		# EN: Assign value to translator.
		# JP: translator に値を代入する。
		translator = str.maketrans('', '', string.punctuation)
		# EN: Assign value to no_punct.
		# JP: no_punct に値を代入する。
		no_punct = text.translate(translator)
		# EN: Assign value to collapsed.
		# JP: collapsed に値を代入する。
		collapsed = ' '.join(no_punct.lower().split())
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return collapsed

	# EN: Define function `_similarity`.
	# JP: 関数 `_similarity` を定義する。
	def _similarity(a: str, b: str) -> float:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return SequenceMatcher(None, a, b).ratio()

	# EN: Assign value to final_result.
	# JP: final_result に値を代入する。
	final_result = history.final_result() or ''
	# EN: Assign value to normalized_output.
	# JP: normalized_output に値を代入する。
	normalized_output = _normalize_text(final_result)
	# EN: Assign value to eval_config.
	# JP: eval_config に値を代入する。
	eval_config = task.get('eval', {})
	# EN: Assign value to eval_types.
	# JP: eval_types に値を代入する。
	eval_types = eval_config.get('eval_types', [])
	# EN: Assign value to reference_answers.
	# JP: reference_answers に値を代入する。
	reference_answers = eval_config.get('reference_answers', {})

	# EN: Assign value to results.
	# JP: results に値を代入する。
	results = []

	# EN: Define function `_ensure_page_ready`.
	# JP: 関数 `_ensure_page_ready` を定義する。
	def _ensure_page_ready() -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Wait briefly for document readiness to reduce false negatives."""
		# JP: 読み込み完了待ちで誤判定を減らす
		# EN: Wait for readiness to reduce false negatives
		for _ in range(3):
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to ready.
				# JP: ready に値を代入する。
				ready = controller.evaluate_in_browser('document.readyState')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if ready == 'complete':
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return True
			except Exception:
				# EN: Exit the current loop.
				# JP: 現在のループを終了する。
				break
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

	# EN: Define function `_url_matches`.
	# JP: 関数 `_url_matches` を定義する。
	def _url_matches(reference_url: str, current_url: str | None, ignore_query: bool = True) -> bool:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not reference_url or not current_url:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False
		# EN: Assign value to ref.
		# JP: ref に値を代入する。
		ref = urlparse(reference_url)
		# EN: Assign value to cur.
		# JP: cur に値を代入する。
		cur = urlparse(current_url)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if ignore_query:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return (ref.scheme, ref.netloc, ref.path.rstrip('/')) == (cur.scheme, cur.netloc, cur.path.rstrip('/'))
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return (ref.scheme, ref.netloc, ref.path, ref.query) == (cur.scheme, cur.netloc, cur.path, cur.query)

	# 1. String Match
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if 'string_match' in eval_types:
		# EN: Assign value to exact_match.
		# JP: exact_match に値を代入する。
		exact_match = reference_answers.get('exact_match')
		# EN: Assign value to must_include.
		# JP: must_include に値を代入する。
		must_include = reference_answers.get('must_include')
		# EN: Assign value to fuzzy_match.
		# JP: fuzzy_match に値を代入する。
		fuzzy_match = reference_answers.get('fuzzy_match')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if exact_match:
			# EN: Assign value to normalized_expected.
			# JP: normalized_expected に値を代入する。
			normalized_expected = _normalize_text(exact_match)
			# EN: Assign value to similarity.
			# JP: similarity に値を代入する。
			similarity = _similarity(normalized_output, normalized_expected)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if normalized_output == normalized_expected or similarity >= 0.9:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				results.append(f'Success: Exact/near-exact match (similarity {similarity:.2f}).')
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				results.append(f"Failure: Expected near match to '{exact_match}' (similarity {similarity:.2f}).")

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if must_include:
			# EN: Assign value to missing.
			# JP: missing に値を代入する。
			missing = []
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for phrase in must_include:
				# EN: Assign value to norm_phrase.
				# JP: norm_phrase に値を代入する。
				norm_phrase = _normalize_text(phrase)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if norm_phrase not in normalized_output and _similarity(norm_phrase, normalized_output) < 0.7:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					missing.append(phrase)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not missing:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				results.append('Success: All required phrases found.')
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				results.append(f'Failure: Missing phrases: {", ".join(missing)}')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if fuzzy_match:
			# Basic implementation: check if any fuzzy match string is present
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(fuzzy_match, list):
				# EN: Assign value to similarities.
				# JP: similarities に値を代入する。
				similarities = []
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for phrase in fuzzy_match:
					# EN: Assign value to norm_phrase.
					# JP: norm_phrase に値を代入する。
					norm_phrase = _normalize_text(phrase)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					similarities.append(_similarity(norm_phrase, normalized_output))
				# EN: Assign value to max_sim.
				# JP: max_sim に値を代入する。
				max_sim = max(similarities) if similarities else 0.0
				# EN: Assign value to found.
				# JP: found に値を代入する。
				found = max_sim >= 0.8
				# EN: Assign value to match_str.
				# JP: match_str に値を代入する。
				match_str = ', '.join(fuzzy_match)
			else:
				# EN: Assign value to norm_phrase.
				# JP: norm_phrase に値を代入する。
				norm_phrase = _normalize_text(fuzzy_match)
				# EN: Assign value to max_sim.
				# JP: max_sim に値を代入する。
				max_sim = _similarity(norm_phrase, normalized_output)
				# EN: Assign value to found.
				# JP: found に値を代入する。
				found = max_sim >= 0.8
				# EN: Assign value to match_str.
				# JP: match_str に値を代入する。
				match_str = fuzzy_match

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if found:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				results.append(f'Success: Fuzzy match found (max similarity {max_sim:.2f}).')
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				results.append(f'Failure: No fuzzy match found for {match_str}')

	# 2. URL Match
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if 'url_match' in eval_types:
		# EN: Assign value to reference_url.
		# JP: reference_url に値を代入する。
		reference_url = eval_config.get('reference_url')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if reference_url:
			# EN: Assign value to url_found.
			# JP: url_found に値を代入する。
			url_found = False
			# EN: Assign value to current_url.
			# JP: current_url に値を代入する。
			current_url = None

			# Try to get the actual current URL from the browser
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				_ensure_page_ready()
				# EN: Assign value to current_url.
				# JP: current_url に値を代入する。
				current_url = controller.evaluate_in_browser('window.location.href')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if _url_matches(reference_url, current_url):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					results.append(f"Success: Current URL matches reference '{reference_url}'")
					# EN: Assign value to url_found.
					# JP: url_found に値を代入する。
					url_found = True
			except Exception as e:
				# Log but don't fail yet - try text fallback
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.warning(f'Could not verify browser URL directly: {e}')

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not url_found:
				# Fallback to checking text output if browser check fails or doesn't match
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if reference_url in final_result:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					results.append('Success: Reference URL found in output text.')
				else:
					# EN: Assign value to msg.
					# JP: msg に値を代入する。
					msg = f"Failure: URL '{reference_url}' not found"
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if current_url:
						# EN: Update variable with augmented assignment.
						# JP: 複合代入で変数を更新する。
						msg += f' in current location ({current_url})'
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					msg += ' or output.'
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					results.append(msg)

	# 3. Program HTML (DOM Check)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if 'program_html' in eval_types:
		# EN: Assign value to program_html.
		# JP: program_html に値を代入する。
		program_html = eval_config.get('program_html', [])
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for check in program_html:
			# We assume 'url' key might specify a page, but usually it checks the current page 'last'
			# EN: Assign value to locator_js.
			# JP: locator_js に値を代入する。
			locator_js = check.get('locator')  # This is JS code to execute
			# EN: Assign value to required_contents.
			# JP: required_contents に値を代入する。
			required_contents = check.get('required_contents', {})

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if locator_js:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					_ensure_page_ready()
					# WebArena locators often use document.querySelector... which returns an element or string.
					# We need to execute this JS in the browser.
					# The locator string might be like "document.querySelector(...).outerText"

					# We wrap it to ensure it returns a value we can capture
					# EN: Assign value to js_code.
					# JP: js_code に値を代入する。
					js_code = f'(() => {{ return {locator_js}; }})()'

					# EN: Assign value to execution_result.
					# JP: execution_result に値を代入する。
					execution_result = controller.evaluate_in_browser(js_code)
					# EN: Assign value to execution_result_str.
					# JP: execution_result_str に値を代入する。
					execution_result_str = str(execution_result) if execution_result is not None else ''

					# Check against required contents
					# EN: Assign value to exact_match.
					# JP: exact_match に値を代入する。
					exact_match = required_contents.get('exact_match')
					# EN: Assign value to must_include.
					# JP: must_include に値を代入する。
					must_include = required_contents.get('must_include')

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if exact_match:
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if execution_result_str.strip() == exact_match.strip():
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							results.append('Success (DOM): Exact match for locator.')
						else:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							results.append(f"Failure (DOM): Expected '{exact_match}', got '{execution_result_str}'")

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if must_include:
						# EN: Assign value to missing.
						# JP: missing に値を代入する。
						missing = [phrase for phrase in must_include if phrase.lower() not in execution_result_str.lower()]
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if not missing:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							results.append('Success (DOM): Required content found in locator result.')
						else:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							results.append(f'Failure (DOM): Missing content in DOM: {", ".join(missing)}')

				except Exception as e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					results.append(f"Failure (DOM): Error executing locator '{locator_js}': {e}")
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				results.append('Failure (DOM): program_html check missing locator')

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not results:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'No automated evaluation criteria met or supported.'

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return '\n'.join(results)


# EN: Define async function `run_task`.
# JP: 非同期関数 `run_task` を定義する。
@router.post('/webarena/run')
async def run_task(request: Request) -> JSONResponse:
	# JP: 単体タスクの実行エンドポイント
	# EN: Endpoint to run a single task
	data = cast(dict[str, Any], await read_json_payload(request))
	# EN: Assign value to task_id.
	# JP: task_id に値を代入する。
	task_id = data.get('task_id')
	# EN: Assign value to custom_task.
	# JP: custom_task に値を代入する。
	custom_task = cast(dict[str, Any] | None, data.get('custom_task'))
	# EN: Assign value to env_urls_override.
	# JP: env_urls_override に値を代入する。
	env_urls_override = cast(Mapping[str, str] | None, data.get('env_urls'))
	# EN: Assign value to selected_site.
	# JP: selected_site に値を代入する。
	selected_site = data.get('selected_site')

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Import here to avoid circular dependency
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from fastapi_app.services.agent_runtime import get_agent_controller
		# EN: Assign value to controller.
		# JP: controller に値を代入する。
		controller = get_agent_controller()

		# EN: Assign value to intent.
		# JP: intent に値を代入する。
		intent = ''
		# EN: Assign annotated value to current_task.
		# JP: current_task に型付きの値を代入する。
		current_task: WebArenaTask | None = None

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if task_id is not None:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to t_id.
				# JP: t_id に値を代入する。
				t_id = int(task_id)
				# EN: Assign value to current_task.
				# JP: current_task に値を代入する。
				current_task = next((t for t in WEBARENA_TASKS if t.get('task_id') == t_id), None)
			except ValueError:
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if current_task:
				# EN: Assign value to intent.
				# JP: intent に値を代入する。
				intent = current_task['intent']
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif custom_task:
			# EN: Assign value to intent.
			# JP: intent に値を代入する。
			intent = custom_task.get('intent')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not intent:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return JSONResponse({'error': '有効なタスクではありません。'}, status_code=400)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if controller.is_running():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return JSONResponse({'error': 'エージェントは既に実行中です。'}, status_code=409)

		# EN: Assign value to start_override.
		# JP: start_override に値を代入する。
		start_override = _apply_start_page_override(selected_site, env_urls_override)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if custom_task:
			# Execute ad-hoc task without filtering
			# EN: Assign value to temp_task.
			# JP: temp_task に値を代入する。
			temp_task = {
				'task_id': 'custom',
				'intent': custom_task.get('intent'),
				'start_url': custom_task.get('start_url'),
				'require_login': False,
			}
			# EN: Assign value to payload.
			# JP: payload に値を代入する。
			payload = _run_single_task(temp_task, controller, env_urls_override, start_override)
		else:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not current_task:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return JSONResponse({'error': '有効なタスクではありません。'}, status_code=400)
			# EN: Assign value to payload.
			# JP: payload に値を代入する。
			payload = _run_single_task(current_task, controller, env_urls_override, start_override)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse(payload)

	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.exception('WebArena evaluation failed')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': str(e)}, status_code=500)


# EN: Define async function `run_batch`.
# JP: 非同期関数 `run_batch` を定義する。
@router.post('/webarena/run_batch')
async def run_batch(request: Request) -> JSONResponse:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Run a batch of supported WebArena tasks sequentially (no manual prompt input).
	"""
	# JP: タスクを順番に実行して集計結果を返す
	# EN: Run tasks sequentially and return aggregate results
	data = cast(dict[str, Any], await read_json_payload(request))
	# EN: Assign value to env_urls_override.
	# JP: env_urls_override に値を代入する。
	env_urls_override = cast(Mapping[str, str] | None, data.get('env_urls'))
	# EN: Assign value to selected_site.
	# JP: selected_site に値を代入する。
	selected_site = data.get('selected_site')
	# EN: Assign value to task_ids.
	# JP: task_ids に値を代入する。
	task_ids = data.get('task_ids')

	# If caller didn't provide explicit IDs, run all supported tasks
	# EN: Assign annotated value to selected_tasks.
	# JP: selected_tasks に型付きの値を代入する。
	selected_tasks: list[WebArenaTask] = WEBARENA_TASKS
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if task_ids:
		# EN: Assign value to allowed.
		# JP: allowed に値を代入する。
		allowed = {int(t) for t in task_ids if str(t).isdigit()}
		# EN: Assign value to selected_tasks.
		# JP: selected_tasks に値を代入する。
		selected_tasks = [t for t in WEBARENA_TASKS if t.get('task_id') in allowed]
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif selected_site and selected_site in SUPPORTED_SITES:
		# Apply strict filtering: only tasks exclusive to this site
		# EN: Assign value to selected_tasks.
		# JP: selected_tasks に値を代入する。
		selected_tasks = [t for t in WEBARENA_TASKS if t.get('sites') and len(t['sites']) == 1 and selected_site in t['sites']]

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not selected_tasks:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': '実行可能なタスクがありません。'}, status_code=400)

	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from fastapi_app.services.agent_runtime import get_agent_controller

	# EN: Assign value to controller.
	# JP: controller に値を代入する。
	controller = get_agent_controller()

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if controller.is_running():
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': 'エージェントは既に実行中です。'}, status_code=409)

	# EN: Assign value to start_override.
	# JP: start_override に値を代入する。
	start_override = _apply_start_page_override(selected_site, env_urls_override)

	# EN: Assign annotated value to results.
	# JP: results に型付きの値を代入する。
	results: list[WebArenaTaskResult] = []
	# EN: Assign value to success_count.
	# JP: success_count に値を代入する。
	success_count = 0

	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for task in selected_tasks:
		# JP: タスク単位で失敗してもバッチは継続
		# EN: Continue batch even if a single task fails
		try:
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = _run_single_task(task, controller, env_urls_override, start_override)
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			success_count += 1 if result.get('success') else 0
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			results.append(result)
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			results.append(
				{
					'task_id': task.get('task_id'),
					'success': False,
					'summary': f'Error: {e}',
					'steps': [],
					'evaluation': 'Batch runner caught an exception.',
				}
			)

	# EN: Assign value to total.
	# JP: total に値を代入する。
	total = len(selected_tasks)
	# EN: Assign value to score.
	# JP: score に値を代入する。
	score = round((success_count / total) * 100, 2)

	# EN: Assign value to metrics.
	# JP: metrics に値を代入する。
	metrics = _compute_aggregate_metrics(results, selected_tasks, _WEBARENA_MAX_STEPS)

	# EN: Assign value to response_data.
	# JP: response_data に値を代入する。
	response_data = {
		'total_tasks': total,
		'success_count': success_count,
		'score': score,
		'aggregate_metrics': metrics,
		'results': results,
	}

	# Save results to disk
	# JP: 集計結果をローカルに保存
	# EN: Persist batch results to disk
	try:
		# EN: Assign value to output_dir.
		# JP: output_dir に値を代入する。
		output_dir = 'webarena_data'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.path.exists(output_dir):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			os.makedirs(output_dir)

		# EN: Assign value to output_file.
		# JP: output_file に値を代入する。
		output_file = os.path.join(output_dir, 'results.json')
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with open(output_file, 'w', encoding='utf-8') as f:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			json.dump({**response_data, 'timestamp': datetime.datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info('Saved batch results to %s', output_file)
	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.error('Failed to save batch results to file: %s', e)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return JSONResponse(response_data)


# EN: Define async function `save_results`.
# JP: 非同期関数 `save_results` を定義する。
@router.post('/webarena/save_results')
async def save_results(request: Request) -> JSONResponse:
	# JP: UI から送信された結果を保存・再計算する
	# EN: Save UI-submitted results and recompute metrics
	data = cast(dict[str, Any], await read_json_payload(request))
	# EN: Assign value to results.
	# JP: results に値を代入する。
	results = cast(list[WebArenaTaskResult], data.get('results', []))

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not results:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': 'No results provided'}, status_code=400)

	# Reconstruct selected_tasks from result IDs for metric calculation
	# JP: task_id から元タスクを復元して集計に利用
	# EN: Rebuild task list from task_id for aggregation
	task_map = {t['task_id']: t for t in WEBARENA_TASKS}
	# EN: Assign value to ordered_tasks.
	# JP: ordered_tasks に値を代入する。
	ordered_tasks = []
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for r in results:
		# EN: Assign value to tid.
		# JP: tid に値を代入する。
		tid = r.get('task_id')
		# If custom task or unknown, might be None, handle gracefully
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		ordered_tasks.append(task_map.get(tid, {}))

	# EN: Assign value to metrics.
	# JP: metrics に値を代入する。
	metrics = _compute_aggregate_metrics(results, ordered_tasks, _WEBARENA_MAX_STEPS)

	# EN: Assign value to success_count.
	# JP: success_count に値を代入する。
	success_count = sum(1 for r in results if r.get('success'))
	# EN: Assign value to total.
	# JP: total に値を代入する。
	total = len(results)
	# EN: Assign value to score.
	# JP: score に値を代入する。
	score = round((success_count / total) * 100, 2) if total > 0 else 0.0

	# EN: Assign value to response_data.
	# JP: response_data に値を代入する。
	response_data = {
		'total_tasks': total,
		'success_count': success_count,
		'score': score,
		'aggregate_metrics': metrics,
		'results': results,
	}

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to output_dir.
		# JP: output_dir に値を代入する。
		output_dir = 'webarena_data'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.path.exists(output_dir):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			os.makedirs(output_dir)

		# EN: Assign value to output_file.
		# JP: output_file に値を代入する。
		output_file = os.path.join(output_dir, 'results.json')
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with open(output_file, 'w', encoding='utf-8') as f:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			json.dump({**response_data, 'timestamp': datetime.datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info('Saved batch results to %s', output_file)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'success': True, 'path': output_file})
	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.error('Failed to save batch results to file: %s', e)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': str(e)}, status_code=500)
