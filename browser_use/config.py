"""Configuration system for browser-use with automatic migration support."""

import json
import logging
import os
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import Any
from uuid import uuid4

import psutil
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


# EN: Define function `is_running_in_docker`.
# JP: 関数 `is_running_in_docker` を定義する。
@cache
def is_running_in_docker() -> bool:
	"""Detect if we are running in a docker container, for the purpose of optimizing chrome launch flags (dev shm usage, gpu settings, etc.)"""
	try:
		if Path('/.dockerenv').exists() or 'docker' in Path('/proc/1/cgroup').read_text().lower():
			return True
	except Exception:
		pass

	try:
		# if init proc (PID 1) looks like uvicorn/python/uv/etc. then we're in Docker
		# if init proc (PID 1) looks like bash/systemd/init/etc. then we're probably NOT in Docker
		init_cmd = ' '.join(psutil.Process(1).cmdline())
		if ('py' in init_cmd) or ('uv' in init_cmd) or ('app' in init_cmd):
			return True
	except Exception:
		pass

	try:
		# if less than 10 total running procs, then we're almost certainly in a container
		if len(psutil.pids()) < 10:
			return True
	except Exception:
		pass

	return False


# EN: Define class `OldConfig`.
# JP: クラス `OldConfig` を定義する。
class OldConfig:
	"""Original lazy-loading configuration class for environment variables."""

	# Cache for directory creation tracking
	_dirs_created = False

	# EN: Define function `BROWSER_USE_LOGGING_LEVEL`.
	# JP: 関数 `BROWSER_USE_LOGGING_LEVEL` を定義する。
	@property
	def BROWSER_USE_LOGGING_LEVEL(self) -> str:
		return os.getenv('BROWSER_USE_LOGGING_LEVEL', 'info').lower()

	# EN: Define function `ANONYMIZED_TELEMETRY`.
	# JP: 関数 `ANONYMIZED_TELEMETRY` を定義する。
	@property
	def ANONYMIZED_TELEMETRY(self) -> bool:
		return os.getenv('ANONYMIZED_TELEMETRY', 'true').lower()[:1] in 'ty1'

	# EN: Define function `BROWSER_USE_CLOUD_SYNC`.
	# JP: 関数 `BROWSER_USE_CLOUD_SYNC` を定義する。
	@property
	def BROWSER_USE_CLOUD_SYNC(self) -> bool:
		return os.getenv('BROWSER_USE_CLOUD_SYNC', str(self.ANONYMIZED_TELEMETRY)).lower()[:1] in 'ty1'

	# EN: Define function `BROWSER_USE_CLOUD_API_URL`.
	# JP: 関数 `BROWSER_USE_CLOUD_API_URL` を定義する。
	@property
	def BROWSER_USE_CLOUD_API_URL(self) -> str:
		url = os.getenv('BROWSER_USE_CLOUD_API_URL', 'https://api.browser-use.com')
		assert '://' in url, 'BROWSER_USE_CLOUD_API_URL must be a valid URL'
		return url

	# EN: Define function `BROWSER_USE_CLOUD_UI_URL`.
	# JP: 関数 `BROWSER_USE_CLOUD_UI_URL` を定義する。
	@property
	def BROWSER_USE_CLOUD_UI_URL(self) -> str:
		url = os.getenv('BROWSER_USE_CLOUD_UI_URL', '')
		# Allow empty string as default, only validate if set
		if url and '://' not in url:
			raise AssertionError('BROWSER_USE_CLOUD_UI_URL must be a valid URL if set')
		return url

	# Path configuration
	# EN: Define function `XDG_CACHE_HOME`.
	# JP: 関数 `XDG_CACHE_HOME` を定義する。
	@property
	def XDG_CACHE_HOME(self) -> Path:
		return Path(os.getenv('XDG_CACHE_HOME', '~/.cache')).expanduser().resolve()

	# EN: Define function `XDG_CONFIG_HOME`.
	# JP: 関数 `XDG_CONFIG_HOME` を定義する。
	@property
	def XDG_CONFIG_HOME(self) -> Path:
		return Path(os.getenv('XDG_CONFIG_HOME', '~/.config')).expanduser().resolve()

	# EN: Define function `BROWSER_USE_CONFIG_DIR`.
	# JP: 関数 `BROWSER_USE_CONFIG_DIR` を定義する。
	@property
	def BROWSER_USE_CONFIG_DIR(self) -> Path:
		path = Path(os.getenv('BROWSER_USE_CONFIG_DIR', str(self.XDG_CONFIG_HOME / 'browseruse'))).expanduser().resolve()
		self._ensure_dirs()
		return path

	# EN: Define function `BROWSER_USE_CONFIG_FILE`.
	# JP: 関数 `BROWSER_USE_CONFIG_FILE` を定義する。
	@property
	def BROWSER_USE_CONFIG_FILE(self) -> Path:
		return self.BROWSER_USE_CONFIG_DIR / 'config.json'

	# EN: Define function `BROWSER_USE_PROFILES_DIR`.
	# JP: 関数 `BROWSER_USE_PROFILES_DIR` を定義する。
	@property
	def BROWSER_USE_PROFILES_DIR(self) -> Path:
		path = self.BROWSER_USE_CONFIG_DIR / 'profiles'
		self._ensure_dirs()
		return path

	# EN: Define function `BROWSER_USE_DEFAULT_USER_DATA_DIR`.
	# JP: 関数 `BROWSER_USE_DEFAULT_USER_DATA_DIR` を定義する。
	@property
	def BROWSER_USE_DEFAULT_USER_DATA_DIR(self) -> Path:
		return self.BROWSER_USE_PROFILES_DIR / 'default'

	# EN: Define function `BROWSER_USE_EXTENSIONS_DIR`.
	# JP: 関数 `BROWSER_USE_EXTENSIONS_DIR` を定義する。
	@property
	def BROWSER_USE_EXTENSIONS_DIR(self) -> Path:
		path = self.BROWSER_USE_CONFIG_DIR / 'extensions'
		self._ensure_dirs()
		return path

	# EN: Define function `_ensure_dirs`.
	# JP: 関数 `_ensure_dirs` を定義する。
	def _ensure_dirs(self) -> None:
		"""Create directories if they don't exist (only once)"""
		if not self._dirs_created:
			config_dir = (
				Path(os.getenv('BROWSER_USE_CONFIG_DIR', str(self.XDG_CONFIG_HOME / 'browseruse'))).expanduser().resolve()
			)
			config_dir.mkdir(parents=True, exist_ok=True)
			(config_dir / 'profiles').mkdir(parents=True, exist_ok=True)
			(config_dir / 'extensions').mkdir(parents=True, exist_ok=True)
			self._dirs_created = True

	# LLM API key configuration
	# EN: Define function `OPENAI_API_KEY`.
	# JP: 関数 `OPENAI_API_KEY` を定義する。
	@property
	def OPENAI_API_KEY(self) -> str:
		return os.getenv('OPENAI_API_KEY', '')

	# EN: Define function `ANTHROPIC_API_KEY`.
	# JP: 関数 `ANTHROPIC_API_KEY` を定義する。
	@property
	def ANTHROPIC_API_KEY(self) -> str:
		return os.getenv('ANTHROPIC_API_KEY', '')

	# EN: Define function `GOOGLE_API_KEY`.
	# JP: 関数 `GOOGLE_API_KEY` を定義する。
	@property
	def GOOGLE_API_KEY(self) -> str:
		return os.getenv('GOOGLE_API_KEY', '')

	# EN: Define function `DEEPSEEK_API_KEY`.
	# JP: 関数 `DEEPSEEK_API_KEY` を定義する。
	@property
	def DEEPSEEK_API_KEY(self) -> str:
		return os.getenv('DEEPSEEK_API_KEY', '')

	# EN: Define function `GROK_API_KEY`.
	# JP: 関数 `GROK_API_KEY` を定義する。
	@property
	def GROK_API_KEY(self) -> str:
		return os.getenv('GROK_API_KEY', '')

	# EN: Define function `NOVITA_API_KEY`.
	# JP: 関数 `NOVITA_API_KEY` を定義する。
	@property
	def NOVITA_API_KEY(self) -> str:
		return os.getenv('NOVITA_API_KEY', '')

	# EN: Define function `AZURE_OPENAI_ENDPOINT`.
	# JP: 関数 `AZURE_OPENAI_ENDPOINT` を定義する。
	@property
	def AZURE_OPENAI_ENDPOINT(self) -> str:
		return os.getenv('AZURE_OPENAI_ENDPOINT', '')

	# EN: Define function `AZURE_OPENAI_KEY`.
	# JP: 関数 `AZURE_OPENAI_KEY` を定義する。
	@property
	def AZURE_OPENAI_KEY(self) -> str:
		return os.getenv('AZURE_OPENAI_KEY', '')

	# EN: Define function `SKIP_LLM_API_KEY_VERIFICATION`.
	# JP: 関数 `SKIP_LLM_API_KEY_VERIFICATION` を定義する。
	@property
	def SKIP_LLM_API_KEY_VERIFICATION(self) -> bool:
		return os.getenv('SKIP_LLM_API_KEY_VERIFICATION', 'false').lower()[:1] in 'ty1'

	# EN: Define function `DEFAULT_LLM`.
	# JP: 関数 `DEFAULT_LLM` を定義する。
	@property
	def DEFAULT_LLM(self) -> str:
		return os.getenv('DEFAULT_LLM', 'groq_openai/gpt-oss-20b')

	# Runtime hints
	# EN: Define function `IN_DOCKER`.
	# JP: 関数 `IN_DOCKER` を定義する。
	@property
	def IN_DOCKER(self) -> bool:
		return os.getenv('IN_DOCKER', 'false').lower()[:1] in 'ty1' or is_running_in_docker()

	# EN: Define function `IS_IN_EVALS`.
	# JP: 関数 `IS_IN_EVALS` を定義する。
	@property
	def IS_IN_EVALS(self) -> bool:
		return os.getenv('IS_IN_EVALS', 'false').lower()[:1] in 'ty1'

	# EN: Define function `WIN_FONT_DIR`.
	# JP: 関数 `WIN_FONT_DIR` を定義する。
	@property
	def WIN_FONT_DIR(self) -> str:
		return os.getenv('WIN_FONT_DIR', 'C:\\Windows\\Fonts')


# EN: Define class `FlatEnvConfig`.
# JP: クラス `FlatEnvConfig` を定義する。
class FlatEnvConfig(BaseSettings):
	"""All environment variables in a flat namespace."""

	model_config = SettingsConfigDict(
		env_file=('secrets.env', '.env'),
		env_file_encoding='utf-8',
		case_sensitive=True,
		extra='allow',
	)

	# Logging and telemetry
	BROWSER_USE_LOGGING_LEVEL: str = Field(default='info')
	CDP_LOGGING_LEVEL: str = Field(default='WARNING')
	BROWSER_USE_DEBUG_LOG_FILE: str | None = Field(default=None)
	BROWSER_USE_INFO_LOG_FILE: str | None = Field(default=None)
	ANONYMIZED_TELEMETRY: bool = Field(default=True)
	BROWSER_USE_CLOUD_SYNC: bool | None = Field(default=None)
	BROWSER_USE_CLOUD_API_URL: str = Field(default='https://api.browser-use.com')
	BROWSER_USE_CLOUD_UI_URL: str = Field(default='')

	# Path configuration
	XDG_CACHE_HOME: str = Field(default='~/.cache')
	XDG_CONFIG_HOME: str = Field(default='~/.config')
	BROWSER_USE_CONFIG_DIR: str | None = Field(default=None)

	# LLM API keys
	OPENAI_API_KEY: str = Field(default='')
	ANTHROPIC_API_KEY: str = Field(default='')
	GOOGLE_API_KEY: str = Field(default='')
	DEEPSEEK_API_KEY: str = Field(default='')
	GROK_API_KEY: str = Field(default='')
	NOVITA_API_KEY: str = Field(default='')
	AZURE_OPENAI_ENDPOINT: str = Field(default='')
	AZURE_OPENAI_KEY: str = Field(default='')
	SKIP_LLM_API_KEY_VERIFICATION: bool = Field(default=False)
	DEFAULT_LLM: str = Field(default='groq_openai/gpt-oss-20b')

	# Runtime hints
	IN_DOCKER: bool | None = Field(default=None)
	IS_IN_EVALS: bool = Field(default=False)
	WIN_FONT_DIR: str = Field(default='C:\\Windows\\Fonts')

	# MCP-specific env vars
	BROWSER_USE_CONFIG_PATH: str | None = Field(default=None)
	BROWSER_USE_HEADLESS: bool | None = Field(default=None)
	BROWSER_USE_ALLOWED_DOMAINS: str | None = Field(default=None)
	BROWSER_USE_LLM_MODEL: str | None = Field(default=None)

	# Proxy env vars
	BROWSER_USE_PROXY_URL: str | None = Field(default=None)
	BROWSER_USE_NO_PROXY: str | None = Field(default=None)
	BROWSER_USE_PROXY_USERNAME: str | None = Field(default=None)
	BROWSER_USE_PROXY_PASSWORD: str | None = Field(default=None)


# EN: Define class `DBStyleEntry`.
# JP: クラス `DBStyleEntry` を定義する。
class DBStyleEntry(BaseModel):
	"""Database-style entry with UUID and metadata."""

	id: str = Field(default_factory=lambda: str(uuid4()))
	default: bool = Field(default=False)
	created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# EN: Define class `BrowserProfileEntry`.
# JP: クラス `BrowserProfileEntry` を定義する。
class BrowserProfileEntry(DBStyleEntry):
	"""Browser profile configuration entry - accepts any BrowserProfile fields."""

	model_config = ConfigDict(extra='allow')

	# Common browser profile fields for reference
	headless: bool | None = None
	user_data_dir: str | None = None
	allowed_domains: list[str] | None = None
	downloads_path: str | None = None


# EN: Define class `LLMEntry`.
# JP: クラス `LLMEntry` を定義する。
class LLMEntry(DBStyleEntry):
	"""LLM configuration entry."""

	api_key: str | None = None
	model: str | None = None
	temperature: float | None = None
	max_tokens: int | None = None


# EN: Define class `AgentEntry`.
# JP: クラス `AgentEntry` を定義する。
class AgentEntry(DBStyleEntry):
	"""Agent configuration entry."""

	max_steps: int | None = None
	use_vision: bool | None = None
	system_prompt: str | None = None


# EN: Define class `DBStyleConfigJSON`.
# JP: クラス `DBStyleConfigJSON` を定義する。
class DBStyleConfigJSON(BaseModel):
	"""New database-style configuration format."""

	browser_profile: dict[str, BrowserProfileEntry] = Field(default_factory=dict)
	llm: dict[str, LLMEntry] = Field(default_factory=dict)
	agent: dict[str, AgentEntry] = Field(default_factory=dict)


# EN: Define function `create_default_config`.
# JP: 関数 `create_default_config` を定義する。
def create_default_config() -> DBStyleConfigJSON:
	"""Create a fresh default configuration."""
	logger.debug('Creating fresh default config.json')

	new_config = DBStyleConfigJSON()

	# Generate default IDs
	profile_id = str(uuid4())
	llm_id = str(uuid4())
	agent_id = str(uuid4())

	# Create default browser profile entry
	new_config.browser_profile[profile_id] = BrowserProfileEntry(id=profile_id, default=True, headless=False, user_data_dir=None)

	# Create default LLM entry
	new_config.llm[llm_id] = LLMEntry(
		id=llm_id,
		default=True,
		model='openai/gpt-oss-20b',
		api_key='your-groq-api-key-here',
	)

	# Create default agent entry
	new_config.agent[agent_id] = AgentEntry(id=agent_id, default=True)

	return new_config


# EN: Define function `load_and_migrate_config`.
# JP: 関数 `load_and_migrate_config` を定義する。
def load_and_migrate_config(config_path: Path) -> DBStyleConfigJSON:
	"""Load config.json or create fresh one if old format detected."""
	if not config_path.exists():
		# Create fresh config with defaults
		config_path.parent.mkdir(parents=True, exist_ok=True)
		new_config = create_default_config()
		with open(config_path, 'w') as f:
			json.dump(new_config.model_dump(), f, indent=2)
		return new_config

	try:
		with open(config_path) as f:
			data = json.load(f)

		# Check if it's already in DB-style format
		if all(key in data for key in ['browser_profile', 'llm', 'agent']) and all(
			isinstance(data.get(key, {}), dict) for key in ['browser_profile', 'llm', 'agent']
		):
			# Check if the values are DB-style entries (have UUIDs as keys)
			if data.get('browser_profile') and all(isinstance(v, dict) and 'id' in v for v in data['browser_profile'].values()):
				# Already in new format
				return DBStyleConfigJSON(**data)

		# Old format detected - delete it and create fresh config
		logger.debug(f'Old config format detected at {config_path}, creating fresh config')
		new_config = create_default_config()

		# Overwrite with new config
		with open(config_path, 'w') as f:
			json.dump(new_config.model_dump(), f, indent=2)

		logger.debug(f'Created fresh config.json at {config_path}')
		return new_config

	except Exception as e:
		logger.error(f'Failed to load config from {config_path}: {e}, creating fresh config')
		# On any error, create fresh config
		new_config = create_default_config()
		try:
			with open(config_path, 'w') as f:
				json.dump(new_config.model_dump(), f, indent=2)
		except Exception as write_error:
			logger.error(f'Failed to write fresh config: {write_error}')
		return new_config


# EN: Define class `Config`.
# JP: クラス `Config` を定義する。
class Config:
	"""Backward-compatible configuration class that merges all config sources.

	Re-reads environment variables on every access to maintain compatibility.
	"""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self):
		# Cache for directory creation tracking only
		self._dirs_created = False

	# EN: Define function `__getattr__`.
	# JP: 関数 `__getattr__` を定義する。
	def __getattr__(self, name: str) -> Any:
		"""Dynamically proxy all attributes to fresh instances.

		This ensures env vars are re-read on every access.
		"""
		# Special handling for internal attributes
		if name.startswith('_'):
			raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

		# Create fresh instances on every access
		old_config = OldConfig()

		# Always use old config for all attributes (it handles env vars with proper transformations)
		if hasattr(old_config, name):
			return getattr(old_config, name)

		# For new MCP-specific attributes not in old config
		env_config = FlatEnvConfig()
		if hasattr(env_config, name):
			return getattr(env_config, name)

		# Handle special methods
		if name == 'get_default_profile':
			return lambda: self._get_default_profile()
		elif name == 'get_default_llm':
			return lambda: self._get_default_llm()
		elif name == 'get_default_agent':
			return lambda: self._get_default_agent()
		elif name == 'load_config':
			return lambda: self._load_config()
		elif name == '_ensure_dirs':
			return lambda: old_config._ensure_dirs()

		raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

	# EN: Define function `_get_config_path`.
	# JP: 関数 `_get_config_path` を定義する。
	def _get_config_path(self) -> Path:
		"""Get config path from fresh env config."""
		env_config = FlatEnvConfig()
		if env_config.BROWSER_USE_CONFIG_PATH:
			return Path(env_config.BROWSER_USE_CONFIG_PATH).expanduser()
		elif env_config.BROWSER_USE_CONFIG_DIR:
			return Path(env_config.BROWSER_USE_CONFIG_DIR).expanduser() / 'config.json'
		else:
			xdg_config = Path(env_config.XDG_CONFIG_HOME).expanduser()
			return xdg_config / 'browseruse' / 'config.json'

	# EN: Define function `_get_db_config`.
	# JP: 関数 `_get_db_config` を定義する。
	def _get_db_config(self) -> DBStyleConfigJSON:
		"""Load and migrate config.json."""
		config_path = self._get_config_path()
		return load_and_migrate_config(config_path)

	# EN: Define function `_get_default_profile`.
	# JP: 関数 `_get_default_profile` を定義する。
	def _get_default_profile(self) -> dict[str, Any]:
		"""Get the default browser profile configuration."""
		db_config = self._get_db_config()
		for profile in db_config.browser_profile.values():
			if profile.default:
				return profile.model_dump(exclude_none=True)

		# Return first profile if no default
		if db_config.browser_profile:
			return next(iter(db_config.browser_profile.values())).model_dump(exclude_none=True)

		return {}

	# EN: Define function `_get_default_llm`.
	# JP: 関数 `_get_default_llm` を定義する。
	def _get_default_llm(self) -> dict[str, Any]:
		"""Get the default LLM configuration."""
		db_config = self._get_db_config()
		for llm in db_config.llm.values():
			if llm.default:
				return llm.model_dump(exclude_none=True)

		# Return first LLM if no default
		if db_config.llm:
			return next(iter(db_config.llm.values())).model_dump(exclude_none=True)

		return {}

	# EN: Define function `_get_default_agent`.
	# JP: 関数 `_get_default_agent` を定義する。
	def _get_default_agent(self) -> dict[str, Any]:
		"""Get the default agent configuration."""
		db_config = self._get_db_config()
		for agent in db_config.agent.values():
			if agent.default:
				return agent.model_dump(exclude_none=True)

		# Return first agent if no default
		if db_config.agent:
			return next(iter(db_config.agent.values())).model_dump(exclude_none=True)

		return {}

	# EN: Define function `_load_config`.
	# JP: 関数 `_load_config` を定義する。
	def _load_config(self) -> dict[str, Any]:
		"""Load configuration with env var overrides for MCP components."""
		config = {
			'browser_profile': self._get_default_profile(),
			'llm': self._get_default_llm(),
			'agent': self._get_default_agent(),
		}

		# Fresh env config for overrides
		env_config = FlatEnvConfig()

		# Apply MCP-specific env var overrides
		if env_config.BROWSER_USE_HEADLESS is not None:
			config['browser_profile']['headless'] = env_config.BROWSER_USE_HEADLESS

		if env_config.BROWSER_USE_ALLOWED_DOMAINS:
			domains = [d.strip() for d in env_config.BROWSER_USE_ALLOWED_DOMAINS.split(',') if d.strip()]
			config['browser_profile']['allowed_domains'] = domains

		# Proxy settings (Chromium) -> consolidated `proxy` dict
		proxy_dict: dict[str, Any] = {}
		if env_config.BROWSER_USE_PROXY_URL:
			proxy_dict['server'] = env_config.BROWSER_USE_PROXY_URL
		if env_config.BROWSER_USE_NO_PROXY:
			# store bypass as comma-separated string to match Chrome flag
			proxy_dict['bypass'] = ','.join([d.strip() for d in env_config.BROWSER_USE_NO_PROXY.split(',') if d.strip()])
		if env_config.BROWSER_USE_PROXY_USERNAME:
			proxy_dict['username'] = env_config.BROWSER_USE_PROXY_USERNAME
		if env_config.BROWSER_USE_PROXY_PASSWORD:
			proxy_dict['password'] = env_config.BROWSER_USE_PROXY_PASSWORD
		if proxy_dict:
			# ensure section exists
			config.setdefault('browser_profile', {})
			config['browser_profile']['proxy'] = proxy_dict

		if env_config.OPENAI_API_KEY:
			config['llm']['api_key'] = env_config.OPENAI_API_KEY

		if env_config.BROWSER_USE_LLM_MODEL:
			config['llm']['model'] = env_config.BROWSER_USE_LLM_MODEL

		return config


# Create singleton instance
CONFIG = Config()


# Helper functions for MCP components
# EN: Define function `load_browser_use_config`.
# JP: 関数 `load_browser_use_config` を定義する。
def load_browser_use_config() -> dict[str, Any]:
	"""Load browser-use configuration for MCP components."""
	return CONFIG.load_config()


# EN: Define function `get_default_profile`.
# JP: 関数 `get_default_profile` を定義する。
def get_default_profile(config: dict[str, Any]) -> dict[str, Any]:
	"""Get default browser profile from config dict."""
	return config.get('browser_profile', {})


# EN: Define function `get_default_llm`.
# JP: 関数 `get_default_llm` を定義する。
def get_default_llm(config: dict[str, Any]) -> dict[str, Any]:
	"""Get default LLM config from config dict."""
	return config.get('llm', {})
