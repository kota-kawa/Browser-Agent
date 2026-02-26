# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Configuration system for browser-use with automatic migration support."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from datetime import datetime
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from functools import cache
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from uuid import uuid4

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import psutil
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, ConfigDict, Field
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic_settings import BaseSettings, SettingsConfigDict

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# EN: Define function `is_running_in_docker`.
# JP: 関数 `is_running_in_docker` を定義する。
@cache
def is_running_in_docker() -> bool:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Detect if we are running in a docker container, for the purpose of optimizing chrome launch flags (dev shm usage, gpu settings, etc.)"""
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if Path('/.dockerenv').exists() or 'docker' in Path('/proc/1/cgroup').read_text().lower():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True
	except Exception:
		# EN: Keep a placeholder statement.
		# JP: プレースホルダー文を維持する。
		pass

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# if init proc (PID 1) looks like uvicorn/python/uv/etc. then we're in Docker
		# if init proc (PID 1) looks like bash/systemd/init/etc. then we're probably NOT in Docker
		# EN: Assign value to init_cmd.
		# JP: init_cmd に値を代入する。
		init_cmd = ' '.join(psutil.Process(1).cmdline())
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if ('py' in init_cmd) or ('uv' in init_cmd) or ('app' in init_cmd):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True
	except Exception:
		# EN: Keep a placeholder statement.
		# JP: プレースホルダー文を維持する。
		pass

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# if less than 10 total running procs, then we're almost certainly in a container
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if len(psutil.pids()) < 10:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True
	except Exception:
		# EN: Keep a placeholder statement.
		# JP: プレースホルダー文を維持する。
		pass

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return False


# EN: Define class `OldConfig`.
# JP: クラス `OldConfig` を定義する。
class OldConfig:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Original lazy-loading configuration class for environment variables."""

	# Cache for directory creation tracking
	# EN: Assign value to _dirs_created.
	# JP: _dirs_created に値を代入する。
	_dirs_created = False

	# EN: Define function `BROWSER_USE_LOGGING_LEVEL`.
	# JP: 関数 `BROWSER_USE_LOGGING_LEVEL` を定義する。
	@property
	def BROWSER_USE_LOGGING_LEVEL(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('BROWSER_USE_LOGGING_LEVEL', 'info').lower()

	# EN: Define function `ANONYMIZED_TELEMETRY`.
	# JP: 関数 `ANONYMIZED_TELEMETRY` を定義する。
	@property
	def ANONYMIZED_TELEMETRY(self) -> bool:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('ANONYMIZED_TELEMETRY', 'true').lower()[:1] in 'ty1'

	# EN: Define function `BROWSER_USE_CLOUD_SYNC`.
	# JP: 関数 `BROWSER_USE_CLOUD_SYNC` を定義する。
	@property
	def BROWSER_USE_CLOUD_SYNC(self) -> bool:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('BROWSER_USE_CLOUD_SYNC', str(self.ANONYMIZED_TELEMETRY)).lower()[:1] in 'ty1'

	# EN: Define function `BROWSER_USE_CLOUD_API_URL`.
	# JP: 関数 `BROWSER_USE_CLOUD_API_URL` を定義する。
	@property
	def BROWSER_USE_CLOUD_API_URL(self) -> str:
		# EN: Assign value to url.
		# JP: url に値を代入する。
		url = os.getenv('BROWSER_USE_CLOUD_API_URL', 'https://api.browser-use.com')
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert '://' in url, 'BROWSER_USE_CLOUD_API_URL must be a valid URL'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return url

	# EN: Define function `BROWSER_USE_CLOUD_UI_URL`.
	# JP: 関数 `BROWSER_USE_CLOUD_UI_URL` を定義する。
	@property
	def BROWSER_USE_CLOUD_UI_URL(self) -> str:
		# EN: Assign value to url.
		# JP: url に値を代入する。
		url = os.getenv('BROWSER_USE_CLOUD_UI_URL', '')
		# Allow empty string as default, only validate if set
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if url and '://' not in url:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AssertionError('BROWSER_USE_CLOUD_UI_URL must be a valid URL if set')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return url

	# Path configuration
	# EN: Define function `XDG_CACHE_HOME`.
	# JP: 関数 `XDG_CACHE_HOME` を定義する。
	@property
	def XDG_CACHE_HOME(self) -> Path:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return Path(os.getenv('XDG_CACHE_HOME', '~/.cache')).expanduser().resolve()

	# EN: Define function `XDG_CONFIG_HOME`.
	# JP: 関数 `XDG_CONFIG_HOME` を定義する。
	@property
	def XDG_CONFIG_HOME(self) -> Path:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return Path(os.getenv('XDG_CONFIG_HOME', '~/.config')).expanduser().resolve()

	# EN: Define function `BROWSER_USE_CONFIG_DIR`.
	# JP: 関数 `BROWSER_USE_CONFIG_DIR` を定義する。
	@property
	def BROWSER_USE_CONFIG_DIR(self) -> Path:
		# EN: Assign value to path.
		# JP: path に値を代入する。
		path = Path(os.getenv('BROWSER_USE_CONFIG_DIR', str(self.XDG_CONFIG_HOME / 'browseruse'))).expanduser().resolve()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._ensure_dirs()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return path

	# EN: Define function `BROWSER_USE_CONFIG_FILE`.
	# JP: 関数 `BROWSER_USE_CONFIG_FILE` を定義する。
	@property
	def BROWSER_USE_CONFIG_FILE(self) -> Path:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.BROWSER_USE_CONFIG_DIR / 'config.json'

	# EN: Define function `BROWSER_USE_PROFILES_DIR`.
	# JP: 関数 `BROWSER_USE_PROFILES_DIR` を定義する。
	@property
	def BROWSER_USE_PROFILES_DIR(self) -> Path:
		# EN: Assign value to path.
		# JP: path に値を代入する。
		path = self.BROWSER_USE_CONFIG_DIR / 'profiles'
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._ensure_dirs()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return path

	# EN: Define function `BROWSER_USE_DEFAULT_USER_DATA_DIR`.
	# JP: 関数 `BROWSER_USE_DEFAULT_USER_DATA_DIR` を定義する。
	@property
	def BROWSER_USE_DEFAULT_USER_DATA_DIR(self) -> Path:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.BROWSER_USE_PROFILES_DIR / 'default'

	# EN: Define function `BROWSER_USE_EXTENSIONS_DIR`.
	# JP: 関数 `BROWSER_USE_EXTENSIONS_DIR` を定義する。
	@property
	def BROWSER_USE_EXTENSIONS_DIR(self) -> Path:
		# EN: Assign value to path.
		# JP: path に値を代入する。
		path = self.BROWSER_USE_CONFIG_DIR / 'extensions'
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._ensure_dirs()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return path

	# EN: Define function `_ensure_dirs`.
	# JP: 関数 `_ensure_dirs` を定義する。
	def _ensure_dirs(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Create directories if they don't exist (only once)"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._dirs_created:
			# EN: Assign value to config_dir.
			# JP: config_dir に値を代入する。
			config_dir = (
				Path(os.getenv('BROWSER_USE_CONFIG_DIR', str(self.XDG_CONFIG_HOME / 'browseruse'))).expanduser().resolve()
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			config_dir.mkdir(parents=True, exist_ok=True)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			(config_dir / 'profiles').mkdir(parents=True, exist_ok=True)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			(config_dir / 'extensions').mkdir(parents=True, exist_ok=True)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._dirs_created = True

	# LLM API key configuration
	# EN: Define function `OPENAI_API_KEY`.
	# JP: 関数 `OPENAI_API_KEY` を定義する。
	@property
	def OPENAI_API_KEY(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('OPENAI_API_KEY', '')

	# EN: Define function `ANTHROPIC_API_KEY`.
	# JP: 関数 `ANTHROPIC_API_KEY` を定義する。
	@property
	def ANTHROPIC_API_KEY(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('ANTHROPIC_API_KEY', '')

	# EN: Define function `GOOGLE_API_KEY`.
	# JP: 関数 `GOOGLE_API_KEY` を定義する。
	@property
	def GOOGLE_API_KEY(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('GOOGLE_API_KEY', '')

	# EN: Define function `DEEPSEEK_API_KEY`.
	# JP: 関数 `DEEPSEEK_API_KEY` を定義する。
	@property
	def DEEPSEEK_API_KEY(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('DEEPSEEK_API_KEY', '')

	# EN: Define function `GROK_API_KEY`.
	# JP: 関数 `GROK_API_KEY` を定義する。
	@property
	def GROK_API_KEY(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('GROK_API_KEY', '')

	# EN: Define function `NOVITA_API_KEY`.
	# JP: 関数 `NOVITA_API_KEY` を定義する。
	@property
	def NOVITA_API_KEY(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('NOVITA_API_KEY', '')

	# EN: Define function `AZURE_OPENAI_ENDPOINT`.
	# JP: 関数 `AZURE_OPENAI_ENDPOINT` を定義する。
	@property
	def AZURE_OPENAI_ENDPOINT(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('AZURE_OPENAI_ENDPOINT', '')

	# EN: Define function `AZURE_OPENAI_KEY`.
	# JP: 関数 `AZURE_OPENAI_KEY` を定義する。
	@property
	def AZURE_OPENAI_KEY(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('AZURE_OPENAI_KEY', '')

	# EN: Define function `SKIP_LLM_API_KEY_VERIFICATION`.
	# JP: 関数 `SKIP_LLM_API_KEY_VERIFICATION` を定義する。
	@property
	def SKIP_LLM_API_KEY_VERIFICATION(self) -> bool:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('SKIP_LLM_API_KEY_VERIFICATION', 'false').lower()[:1] in 'ty1'

	# EN: Define function `DEFAULT_LLM`.
	# JP: 関数 `DEFAULT_LLM` を定義する。
	@property
	def DEFAULT_LLM(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('DEFAULT_LLM', 'groq_openai/gpt-oss-20b')

	# Runtime hints
	# EN: Define function `IN_DOCKER`.
	# JP: 関数 `IN_DOCKER` を定義する。
	@property
	def IN_DOCKER(self) -> bool:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('IN_DOCKER', 'false').lower()[:1] in 'ty1' or is_running_in_docker()

	# EN: Define function `IS_IN_EVALS`.
	# JP: 関数 `IS_IN_EVALS` を定義する。
	@property
	def IS_IN_EVALS(self) -> bool:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('IS_IN_EVALS', 'false').lower()[:1] in 'ty1'

	# EN: Define function `WIN_FONT_DIR`.
	# JP: 関数 `WIN_FONT_DIR` を定義する。
	@property
	def WIN_FONT_DIR(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return os.getenv('WIN_FONT_DIR', 'C:\\Windows\\Fonts')


# EN: Define class `FlatEnvConfig`.
# JP: クラス `FlatEnvConfig` を定義する。
class FlatEnvConfig(BaseSettings):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""All environment variables in a flat namespace."""

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = SettingsConfigDict(
		env_file=('secrets.env', '.env'),
		env_file_encoding='utf-8',
		case_sensitive=True,
		extra='allow',
	)

	# Logging and telemetry
	# EN: Assign annotated value to BROWSER_USE_LOGGING_LEVEL.
	# JP: BROWSER_USE_LOGGING_LEVEL に型付きの値を代入する。
	BROWSER_USE_LOGGING_LEVEL: str = Field(default='info')
	# EN: Assign annotated value to CDP_LOGGING_LEVEL.
	# JP: CDP_LOGGING_LEVEL に型付きの値を代入する。
	CDP_LOGGING_LEVEL: str = Field(default='WARNING')
	# EN: Assign annotated value to BROWSER_USE_DEBUG_LOG_FILE.
	# JP: BROWSER_USE_DEBUG_LOG_FILE に型付きの値を代入する。
	BROWSER_USE_DEBUG_LOG_FILE: str | None = Field(default=None)
	# EN: Assign annotated value to BROWSER_USE_INFO_LOG_FILE.
	# JP: BROWSER_USE_INFO_LOG_FILE に型付きの値を代入する。
	BROWSER_USE_INFO_LOG_FILE: str | None = Field(default=None)
	# EN: Assign annotated value to ANONYMIZED_TELEMETRY.
	# JP: ANONYMIZED_TELEMETRY に型付きの値を代入する。
	ANONYMIZED_TELEMETRY: bool = Field(default=True)
	# EN: Assign annotated value to BROWSER_USE_CLOUD_SYNC.
	# JP: BROWSER_USE_CLOUD_SYNC に型付きの値を代入する。
	BROWSER_USE_CLOUD_SYNC: bool | None = Field(default=None)
	# EN: Assign annotated value to BROWSER_USE_CLOUD_API_URL.
	# JP: BROWSER_USE_CLOUD_API_URL に型付きの値を代入する。
	BROWSER_USE_CLOUD_API_URL: str = Field(default='https://api.browser-use.com')
	# EN: Assign annotated value to BROWSER_USE_CLOUD_UI_URL.
	# JP: BROWSER_USE_CLOUD_UI_URL に型付きの値を代入する。
	BROWSER_USE_CLOUD_UI_URL: str = Field(default='')

	# Path configuration
	# EN: Assign annotated value to XDG_CACHE_HOME.
	# JP: XDG_CACHE_HOME に型付きの値を代入する。
	XDG_CACHE_HOME: str = Field(default='~/.cache')
	# EN: Assign annotated value to XDG_CONFIG_HOME.
	# JP: XDG_CONFIG_HOME に型付きの値を代入する。
	XDG_CONFIG_HOME: str = Field(default='~/.config')
	# EN: Assign annotated value to BROWSER_USE_CONFIG_DIR.
	# JP: BROWSER_USE_CONFIG_DIR に型付きの値を代入する。
	BROWSER_USE_CONFIG_DIR: str | None = Field(default=None)

	# LLM API keys
	# EN: Assign annotated value to OPENAI_API_KEY.
	# JP: OPENAI_API_KEY に型付きの値を代入する。
	OPENAI_API_KEY: str = Field(default='')
	# EN: Assign annotated value to ANTHROPIC_API_KEY.
	# JP: ANTHROPIC_API_KEY に型付きの値を代入する。
	ANTHROPIC_API_KEY: str = Field(default='')
	# EN: Assign annotated value to GOOGLE_API_KEY.
	# JP: GOOGLE_API_KEY に型付きの値を代入する。
	GOOGLE_API_KEY: str = Field(default='')
	# EN: Assign annotated value to DEEPSEEK_API_KEY.
	# JP: DEEPSEEK_API_KEY に型付きの値を代入する。
	DEEPSEEK_API_KEY: str = Field(default='')
	# EN: Assign annotated value to GROK_API_KEY.
	# JP: GROK_API_KEY に型付きの値を代入する。
	GROK_API_KEY: str = Field(default='')
	# EN: Assign annotated value to NOVITA_API_KEY.
	# JP: NOVITA_API_KEY に型付きの値を代入する。
	NOVITA_API_KEY: str = Field(default='')
	# EN: Assign annotated value to AZURE_OPENAI_ENDPOINT.
	# JP: AZURE_OPENAI_ENDPOINT に型付きの値を代入する。
	AZURE_OPENAI_ENDPOINT: str = Field(default='')
	# EN: Assign annotated value to AZURE_OPENAI_KEY.
	# JP: AZURE_OPENAI_KEY に型付きの値を代入する。
	AZURE_OPENAI_KEY: str = Field(default='')
	# EN: Assign annotated value to SKIP_LLM_API_KEY_VERIFICATION.
	# JP: SKIP_LLM_API_KEY_VERIFICATION に型付きの値を代入する。
	SKIP_LLM_API_KEY_VERIFICATION: bool = Field(default=False)
	# EN: Assign annotated value to DEFAULT_LLM.
	# JP: DEFAULT_LLM に型付きの値を代入する。
	DEFAULT_LLM: str = Field(default='groq_openai/gpt-oss-20b')

	# Runtime hints
	# EN: Assign annotated value to IN_DOCKER.
	# JP: IN_DOCKER に型付きの値を代入する。
	IN_DOCKER: bool | None = Field(default=None)
	# EN: Assign annotated value to IS_IN_EVALS.
	# JP: IS_IN_EVALS に型付きの値を代入する。
	IS_IN_EVALS: bool = Field(default=False)
	# EN: Assign annotated value to WIN_FONT_DIR.
	# JP: WIN_FONT_DIR に型付きの値を代入する。
	WIN_FONT_DIR: str = Field(default='C:\\Windows\\Fonts')

	# MCP-specific env vars
	# EN: Assign annotated value to BROWSER_USE_CONFIG_PATH.
	# JP: BROWSER_USE_CONFIG_PATH に型付きの値を代入する。
	BROWSER_USE_CONFIG_PATH: str | None = Field(default=None)
	# EN: Assign annotated value to BROWSER_USE_HEADLESS.
	# JP: BROWSER_USE_HEADLESS に型付きの値を代入する。
	BROWSER_USE_HEADLESS: bool | None = Field(default=None)
	# EN: Assign annotated value to BROWSER_USE_ALLOWED_DOMAINS.
	# JP: BROWSER_USE_ALLOWED_DOMAINS に型付きの値を代入する。
	BROWSER_USE_ALLOWED_DOMAINS: str | None = Field(default=None)
	# EN: Assign annotated value to BROWSER_USE_LLM_MODEL.
	# JP: BROWSER_USE_LLM_MODEL に型付きの値を代入する。
	BROWSER_USE_LLM_MODEL: str | None = Field(default=None)

	# Proxy env vars
	# EN: Assign annotated value to BROWSER_USE_PROXY_URL.
	# JP: BROWSER_USE_PROXY_URL に型付きの値を代入する。
	BROWSER_USE_PROXY_URL: str | None = Field(default=None)
	# EN: Assign annotated value to BROWSER_USE_NO_PROXY.
	# JP: BROWSER_USE_NO_PROXY に型付きの値を代入する。
	BROWSER_USE_NO_PROXY: str | None = Field(default=None)
	# EN: Assign annotated value to BROWSER_USE_PROXY_USERNAME.
	# JP: BROWSER_USE_PROXY_USERNAME に型付きの値を代入する。
	BROWSER_USE_PROXY_USERNAME: str | None = Field(default=None)
	# EN: Assign annotated value to BROWSER_USE_PROXY_PASSWORD.
	# JP: BROWSER_USE_PROXY_PASSWORD に型付きの値を代入する。
	BROWSER_USE_PROXY_PASSWORD: str | None = Field(default=None)


# EN: Define class `DBStyleEntry`.
# JP: クラス `DBStyleEntry` を定義する。
class DBStyleEntry(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Database-style entry with UUID and metadata."""

	# EN: Assign annotated value to id.
	# JP: id に型付きの値を代入する。
	id: str = Field(default_factory=lambda: str(uuid4()))
	# EN: Assign annotated value to default.
	# JP: default に型付きの値を代入する。
	default: bool = Field(default=False)
	# EN: Assign annotated value to created_at.
	# JP: created_at に型付きの値を代入する。
	created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# EN: Define class `BrowserProfileEntry`.
# JP: クラス `BrowserProfileEntry` を定義する。
class BrowserProfileEntry(DBStyleEntry):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Browser profile configuration entry - accepts any BrowserProfile fields."""

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(extra='allow')

	# Common browser profile fields for reference
	# EN: Assign annotated value to headless.
	# JP: headless に型付きの値を代入する。
	headless: bool | None = None
	# EN: Assign annotated value to user_data_dir.
	# JP: user_data_dir に型付きの値を代入する。
	user_data_dir: str | None = None
	# EN: Assign annotated value to allowed_domains.
	# JP: allowed_domains に型付きの値を代入する。
	allowed_domains: list[str] | None = None
	# EN: Assign annotated value to downloads_path.
	# JP: downloads_path に型付きの値を代入する。
	downloads_path: str | None = None


# EN: Define class `LLMEntry`.
# JP: クラス `LLMEntry` を定義する。
class LLMEntry(DBStyleEntry):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""LLM configuration entry."""

	# EN: Assign annotated value to api_key.
	# JP: api_key に型付きの値を代入する。
	api_key: str | None = None
	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str | None = None
	# EN: Assign annotated value to temperature.
	# JP: temperature に型付きの値を代入する。
	temperature: float | None = None
	# EN: Assign annotated value to max_tokens.
	# JP: max_tokens に型付きの値を代入する。
	max_tokens: int | None = None


# EN: Define class `AgentEntry`.
# JP: クラス `AgentEntry` を定義する。
class AgentEntry(DBStyleEntry):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Agent configuration entry."""

	# EN: Assign annotated value to max_steps.
	# JP: max_steps に型付きの値を代入する。
	max_steps: int | None = None
	# EN: Assign annotated value to use_vision.
	# JP: use_vision に型付きの値を代入する。
	use_vision: bool | None = None
	# EN: Assign annotated value to system_prompt.
	# JP: system_prompt に型付きの値を代入する。
	system_prompt: str | None = None


# EN: Define class `DBStyleConfigJSON`.
# JP: クラス `DBStyleConfigJSON` を定義する。
class DBStyleConfigJSON(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""New database-style configuration format."""

	# EN: Assign annotated value to browser_profile.
	# JP: browser_profile に型付きの値を代入する。
	browser_profile: dict[str, BrowserProfileEntry] = Field(default_factory=dict)
	# EN: Assign annotated value to llm.
	# JP: llm に型付きの値を代入する。
	llm: dict[str, LLMEntry] = Field(default_factory=dict)
	# EN: Assign annotated value to agent.
	# JP: agent に型付きの値を代入する。
	agent: dict[str, AgentEntry] = Field(default_factory=dict)


# EN: Define function `create_default_config`.
# JP: 関数 `create_default_config` を定義する。
def create_default_config() -> DBStyleConfigJSON:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Create a fresh default configuration."""
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.debug('Creating fresh default config.json')

	# EN: Assign value to new_config.
	# JP: new_config に値を代入する。
	new_config = DBStyleConfigJSON()

	# Generate default IDs
	# EN: Assign value to profile_id.
	# JP: profile_id に値を代入する。
	profile_id = str(uuid4())
	# EN: Assign value to llm_id.
	# JP: llm_id に値を代入する。
	llm_id = str(uuid4())
	# EN: Assign value to agent_id.
	# JP: agent_id に値を代入する。
	agent_id = str(uuid4())

	# Create default browser profile entry
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	new_config.browser_profile[profile_id] = BrowserProfileEntry(id=profile_id, default=True, headless=False, user_data_dir=None)

	# Create default LLM entry
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	new_config.llm[llm_id] = LLMEntry(
		id=llm_id,
		default=True,
		model='openai/gpt-oss-20b',
		api_key='your-groq-api-key-here',
	)

	# Create default agent entry
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	new_config.agent[agent_id] = AgentEntry(id=agent_id, default=True)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return new_config


# EN: Define function `load_and_migrate_config`.
# JP: 関数 `load_and_migrate_config` を定義する。
def load_and_migrate_config(config_path: Path) -> DBStyleConfigJSON:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Load config.json or create fresh one if old format detected."""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not config_path.exists():
		# Create fresh config with defaults
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		config_path.parent.mkdir(parents=True, exist_ok=True)
		# EN: Assign value to new_config.
		# JP: new_config に値を代入する。
		new_config = create_default_config()
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with open(config_path, 'w') as f:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			json.dump(new_config.model_dump(), f, indent=2)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return new_config

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with open(config_path) as f:
			# EN: Assign value to data.
			# JP: data に値を代入する。
			data = json.load(f)

		# Check if it's already in DB-style format
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if all(key in data for key in ['browser_profile', 'llm', 'agent']) and all(
			isinstance(data.get(key, {}), dict) for key in ['browser_profile', 'llm', 'agent']
		):
			# Check if the values are DB-style entries (have UUIDs as keys)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if data.get('browser_profile') and all(isinstance(v, dict) and 'id' in v for v in data['browser_profile'].values()):
				# Already in new format
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return DBStyleConfigJSON(**data)

		# Old format detected - delete it and create fresh config
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'Old config format detected at {config_path}, creating fresh config')
		# EN: Assign value to new_config.
		# JP: new_config に値を代入する。
		new_config = create_default_config()

		# Overwrite with new config
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with open(config_path, 'w') as f:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			json.dump(new_config.model_dump(), f, indent=2)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'Created fresh config.json at {config_path}')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return new_config

	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.error(f'Failed to load config from {config_path}: {e}, creating fresh config')
		# On any error, create fresh config
		# EN: Assign value to new_config.
		# JP: new_config に値を代入する。
		new_config = create_default_config()
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with open(config_path, 'w') as f:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				json.dump(new_config.model_dump(), f, indent=2)
		except Exception as write_error:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'Failed to write fresh config: {write_error}')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return new_config


# EN: Define class `Config`.
# JP: クラス `Config` を定義する。
class Config:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Backward-compatible configuration class that merges all config sources.

	Re-reads environment variables on every access to maintain compatibility.
	"""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self):
		# Cache for directory creation tracking only
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._dirs_created = False

	# EN: Define function `__getattr__`.
	# JP: 関数 `__getattr__` を定義する。
	def __getattr__(self, name: str) -> Any:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Dynamically proxy all attributes to fresh instances.

		This ensures env vars are re-read on every access.
		"""
		# Special handling for internal attributes
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if name.startswith('_'):
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

		# Create fresh instances on every access
		# EN: Assign value to old_config.
		# JP: old_config に値を代入する。
		old_config = OldConfig()

		# Always use old config for all attributes (it handles env vars with proper transformations)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(old_config, name):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return getattr(old_config, name)

		# For new MCP-specific attributes not in old config
		# EN: Assign value to env_config.
		# JP: env_config に値を代入する。
		env_config = FlatEnvConfig()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(env_config, name):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return getattr(env_config, name)

		# Handle special methods
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if name == 'get_default_profile':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return lambda: self._get_default_profile()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif name == 'get_default_llm':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return lambda: self._get_default_llm()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif name == 'get_default_agent':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return lambda: self._get_default_agent()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif name == 'load_config':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return lambda: self._load_config()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif name == '_ensure_dirs':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return lambda: old_config._ensure_dirs()

		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

	# EN: Define function `_get_config_path`.
	# JP: 関数 `_get_config_path` を定義する。
	def _get_config_path(self) -> Path:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get config path from fresh env config."""
		# EN: Assign value to env_config.
		# JP: env_config に値を代入する。
		env_config = FlatEnvConfig()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if env_config.BROWSER_USE_CONFIG_PATH:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return Path(env_config.BROWSER_USE_CONFIG_PATH).expanduser()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif env_config.BROWSER_USE_CONFIG_DIR:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return Path(env_config.BROWSER_USE_CONFIG_DIR).expanduser() / 'config.json'
		else:
			# EN: Assign value to xdg_config.
			# JP: xdg_config に値を代入する。
			xdg_config = Path(env_config.XDG_CONFIG_HOME).expanduser()
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return xdg_config / 'browseruse' / 'config.json'

	# EN: Define function `_get_db_config`.
	# JP: 関数 `_get_db_config` を定義する。
	def _get_db_config(self) -> DBStyleConfigJSON:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Load and migrate config.json."""
		# EN: Assign value to config_path.
		# JP: config_path に値を代入する。
		config_path = self._get_config_path()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return load_and_migrate_config(config_path)

	# EN: Define function `_get_default_profile`.
	# JP: 関数 `_get_default_profile` を定義する。
	def _get_default_profile(self) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the default browser profile configuration."""
		# EN: Assign value to db_config.
		# JP: db_config に値を代入する。
		db_config = self._get_db_config()
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for profile in db_config.browser_profile.values():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if profile.default:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return profile.model_dump(exclude_none=True)

		# Return first profile if no default
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if db_config.browser_profile:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return next(iter(db_config.browser_profile.values())).model_dump(exclude_none=True)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {}

	# EN: Define function `_get_default_llm`.
	# JP: 関数 `_get_default_llm` を定義する。
	def _get_default_llm(self) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the default LLM configuration."""
		# EN: Assign value to db_config.
		# JP: db_config に値を代入する。
		db_config = self._get_db_config()
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for llm in db_config.llm.values():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if llm.default:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return llm.model_dump(exclude_none=True)

		# Return first LLM if no default
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if db_config.llm:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return next(iter(db_config.llm.values())).model_dump(exclude_none=True)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {}

	# EN: Define function `_get_default_agent`.
	# JP: 関数 `_get_default_agent` を定義する。
	def _get_default_agent(self) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the default agent configuration."""
		# EN: Assign value to db_config.
		# JP: db_config に値を代入する。
		db_config = self._get_db_config()
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for agent in db_config.agent.values():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if agent.default:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return agent.model_dump(exclude_none=True)

		# Return first agent if no default
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if db_config.agent:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return next(iter(db_config.agent.values())).model_dump(exclude_none=True)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {}

	# EN: Define function `_load_config`.
	# JP: 関数 `_load_config` を定義する。
	def _load_config(self) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Load configuration with env var overrides for MCP components."""
		# EN: Assign value to config.
		# JP: config に値を代入する。
		config = {
			'browser_profile': self._get_default_profile(),
			'llm': self._get_default_llm(),
			'agent': self._get_default_agent(),
		}

		# Fresh env config for overrides
		# EN: Assign value to env_config.
		# JP: env_config に値を代入する。
		env_config = FlatEnvConfig()

		# Apply MCP-specific env var overrides
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if env_config.BROWSER_USE_HEADLESS is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			config['browser_profile']['headless'] = env_config.BROWSER_USE_HEADLESS

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if env_config.BROWSER_USE_ALLOWED_DOMAINS:
			# EN: Assign value to domains.
			# JP: domains に値を代入する。
			domains = [d.strip() for d in env_config.BROWSER_USE_ALLOWED_DOMAINS.split(',') if d.strip()]
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			config['browser_profile']['allowed_domains'] = domains

		# Proxy settings (Chromium) -> consolidated `proxy` dict
		# EN: Assign annotated value to proxy_dict.
		# JP: proxy_dict に型付きの値を代入する。
		proxy_dict: dict[str, Any] = {}
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if env_config.BROWSER_USE_PROXY_URL:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			proxy_dict['server'] = env_config.BROWSER_USE_PROXY_URL
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if env_config.BROWSER_USE_NO_PROXY:
			# store bypass as comma-separated string to match Chrome flag
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			proxy_dict['bypass'] = ','.join([d.strip() for d in env_config.BROWSER_USE_NO_PROXY.split(',') if d.strip()])
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if env_config.BROWSER_USE_PROXY_USERNAME:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			proxy_dict['username'] = env_config.BROWSER_USE_PROXY_USERNAME
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if env_config.BROWSER_USE_PROXY_PASSWORD:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			proxy_dict['password'] = env_config.BROWSER_USE_PROXY_PASSWORD
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if proxy_dict:
			# ensure section exists
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			config.setdefault('browser_profile', {})
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			config['browser_profile']['proxy'] = proxy_dict

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if env_config.OPENAI_API_KEY:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			config['llm']['api_key'] = env_config.OPENAI_API_KEY

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if env_config.BROWSER_USE_LLM_MODEL:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			config['llm']['model'] = env_config.BROWSER_USE_LLM_MODEL

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return config


# Create singleton instance
# EN: Assign value to CONFIG.
# JP: CONFIG に値を代入する。
CONFIG = Config()


# Helper functions for MCP components
# EN: Define function `load_browser_use_config`.
# JP: 関数 `load_browser_use_config` を定義する。
def load_browser_use_config() -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Load browser-use configuration for MCP components."""
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return CONFIG.load_config()


# EN: Define function `get_default_profile`.
# JP: 関数 `get_default_profile` を定義する。
def get_default_profile(config: dict[str, Any]) -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Get default browser profile from config dict."""
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return config.get('browser_profile', {})


# EN: Define function `get_default_llm`.
# JP: 関数 `get_default_llm` を定義する。
def get_default_llm(config: dict[str, Any]) -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Get default LLM config from config dict."""
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return config.get('llm', {})
