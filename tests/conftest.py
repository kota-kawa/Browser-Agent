# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import sys
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import types
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os

# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
    # EN: Import required modules.
    # JP: 必要なモジュールをインポートする。
    import psutil  # noqa: F401
except ModuleNotFoundError:
    # EN: Assign value to stub.
    # JP: stub に値を代入する。
    stub = types.ModuleType("psutil")
    # minimal attributes used by browser_use.config
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    stub.virtual_memory = lambda: types.SimpleNamespace(total=0)
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    stub.cpu_count = lambda: 1
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["psutil"] = stub

# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
    # EN: Import required modules.
    # JP: 必要なモジュールをインポートする。
    import bubus  # noqa: F401
except ModuleNotFoundError:
    # EN: Assign value to bus_stub.
    # JP: bus_stub に値を代入する。
    bus_stub = types.ModuleType("bubus")
    # EN: Assign value to service_stub.
    # JP: service_stub に値を代入する。
    service_stub = types.ModuleType("bubus.service")

    # EN: Define class `_EventBus`.
    # JP: クラス `_EventBus` を定義する。
    class _EventBus:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            # EN: Keep a placeholder statement.
            # JP: プレースホルダー文を維持する。
            pass

        # EN: Define function `publish`.
        # JP: 関数 `publish` を定義する。
        def publish(self, *args, **kwargs):
            # EN: Return a value from the function.
            # JP: 関数から値を返す。
            return None

    # EN: Define function `_noop`.
    # JP: 関数 `_noop` を定義する。
    def _noop(*args, **kwargs):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return None

    # EN: Define class `_BaseEvent`.
    # JP: クラス `_BaseEvent` を定義する。
    class _BaseEvent:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            # EN: Keep a placeholder statement.
            # JP: プレースホルダー文を維持する。
            pass

    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    bus_stub.EventBus = _EventBus
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    bus_stub.BaseEvent = _BaseEvent
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    service_stub.get_handler_id = _noop
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    service_stub.get_handler_name = _noop
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    service_stub.logger = types.SimpleNamespace(info=_noop, warning=_noop, error=_noop)

    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["bubus"] = bus_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["bubus.service"] = service_stub

# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
    # EN: Import required modules.
    # JP: 必要なモジュールをインポートする。
    import uuid_extensions  # noqa: F401
except ModuleNotFoundError:
    # EN: Assign value to uuid_stub.
    # JP: uuid_stub に値を代入する。
    uuid_stub = types.ModuleType("uuid_extensions")
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    uuid_stub.uuid7str = lambda: "00000000-0000-7000-0000-000000000000"
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["uuid_extensions"] = uuid_stub

# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
    # EN: Import required modules.
    # JP: 必要なモジュールをインポートする。
    import cdp_use  # noqa: F401
except ModuleNotFoundError:
    # EN: Assign value to cdp_stub.
    # JP: cdp_stub に値を代入する。
    cdp_stub = types.ModuleType("cdp_use")
    # EN: Assign value to cdp_cdp_stub.
    # JP: cdp_cdp_stub に値を代入する。
    cdp_cdp_stub = types.ModuleType("cdp_use.cdp")
    # EN: Assign value to cdp_target_stub.
    # JP: cdp_target_stub に値を代入する。
    cdp_target_stub = types.ModuleType("cdp_use.cdp.target")

    # EN: Define class `_TargetID`.
    # JP: クラス `_TargetID` を定義する。
    class _TargetID(str):
        # EN: Keep a placeholder statement.
        # JP: プレースホルダー文を維持する。
        pass

    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    cdp_target_stub.TargetID = _TargetID

    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["cdp_use"] = cdp_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["cdp_use.cdp"] = cdp_cdp_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["cdp_use.cdp.target"] = cdp_target_stub


# EN: Define function `_install_browser_use_stubs`.
# JP: 関数 `_install_browser_use_stubs` を定義する。
def _install_browser_use_stubs():
    # EN: Assign value to browser_use_stub.
    # JP: browser_use_stub に値を代入する。
    browser_use_stub = types.ModuleType("browser_use")
    # EN: Assign value to agent_stub.
    # JP: agent_stub に値を代入する。
    agent_stub = types.ModuleType("browser_use.agent")
    # EN: Assign value to agent_views_stub.
    # JP: agent_views_stub に値を代入する。
    agent_views_stub = types.ModuleType("browser_use.agent.views")
    # EN: Assign value to browser_stub.
    # JP: browser_stub に値を代入する。
    browser_stub = types.ModuleType("browser_use.browser")
    # EN: Assign value to browser_views_stub.
    # JP: browser_views_stub に値を代入する。
    browser_views_stub = types.ModuleType("browser_use.browser.views")
    # EN: Assign value to browser_events_stub.
    # JP: browser_events_stub に値を代入する。
    browser_events_stub = types.ModuleType("browser_use.browser.events")
    # EN: Assign value to browser_profile_stub.
    # JP: browser_profile_stub に値を代入する。
    browser_profile_stub = types.ModuleType("browser_use.browser.profile")
    # EN: Assign value to model_selection_stub.
    # JP: model_selection_stub に値を代入する。
    model_selection_stub = types.ModuleType("browser_use.model_selection")
    # EN: Assign value to llm_stub.
    # JP: llm_stub に値を代入する。
    llm_stub = types.ModuleType("browser_use.llm")
    # EN: Assign value to llm_base_stub.
    # JP: llm_base_stub に値を代入する。
    llm_base_stub = types.ModuleType("browser_use.llm.base")
    # EN: Assign value to llm_exceptions_stub.
    # JP: llm_exceptions_stub に値を代入する。
    llm_exceptions_stub = types.ModuleType("browser_use.llm.exceptions")
    # EN: Assign value to llm_messages_stub.
    # JP: llm_messages_stub に値を代入する。
    llm_messages_stub = types.ModuleType("browser_use.llm.messages")
    # EN: Assign value to llm_openai_stub.
    # JP: llm_openai_stub に値を代入する。
    llm_openai_stub = types.ModuleType("browser_use.llm.openai.chat")
    # EN: Assign value to llm_google_stub.
    # JP: llm_google_stub に値を代入する。
    llm_google_stub = types.ModuleType("browser_use.llm.google.chat")
    # EN: Assign value to llm_anthropic_stub.
    # JP: llm_anthropic_stub に値を代入する。
    llm_anthropic_stub = types.ModuleType("browser_use.llm.anthropic.chat")
    # EN: Assign value to llm_groq_stub.
    # JP: llm_groq_stub に値を代入する。
    llm_groq_stub = types.ModuleType("browser_use.llm.groq.chat")
    # EN: Assign value to env_loader_stub.
    # JP: env_loader_stub に値を代入する。
    env_loader_stub = types.ModuleType("browser_use.env_loader")

    # EN: Define class `_Agent`.
    # JP: クラス `_Agent` を定義する。
    class _Agent:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            # EN: Keep a placeholder statement.
            # JP: プレースホルダー文を維持する。
            pass

    # EN: Define class `_BrowserProfile`.
    # JP: クラス `_BrowserProfile` を定義する。
    class _BrowserProfile:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            # EN: Keep a placeholder statement.
            # JP: プレースホルダー文を維持する。
            pass

    # EN: Define class `_BrowserSession`.
    # JP: クラス `_BrowserSession` を定義する。
    class _BrowserSession:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            # EN: Keep a placeholder statement.
            # JP: プレースホルダー文を維持する。
            pass

    # EN: Define class `_Tools`.
    # JP: クラス `_Tools` を定義する。
    class _Tools:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            # EN: Keep a placeholder statement.
            # JP: プレースホルダー文を維持する。
            pass

    # EN: Define class `_ActionResult`.
    # JP: クラス `_ActionResult` を定義する。
    class _ActionResult:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            # EN: Keep a placeholder statement.
            # JP: プレースホルダー文を維持する。
            pass

    # EN: Define class `_AgentHistoryList`.
    # JP: クラス `_AgentHistoryList` を定義する。
    class _AgentHistoryList:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            # EN: Assign value to target variable.
            # JP: target variable に値を代入する。
            self.history = []

        # EN: Define function `load_from_file`.
        # JP: 関数 `load_from_file` を定義する。
        @classmethod
        def load_from_file(cls, *args, **kwargs):
            # EN: Return a value from the function.
            # JP: 関数から値を返す。
            return cls()

    # EN: Define class `_AgentOutput`.
    # JP: クラス `_AgentOutput` を定義する。
    class _AgentOutput:
        # EN: Keep a placeholder statement.
        # JP: プレースホルダー文を維持する。
        pass

    # EN: Define class `_BrowserStateSummary`.
    # JP: クラス `_BrowserStateSummary` を定義する。
    class _BrowserStateSummary:
        # EN: Keep a placeholder statement.
        # JP: プレースホルダー文を維持する。
        pass

    # EN: Define class `_BrowserStateHistory`.
    # JP: クラス `_BrowserStateHistory` を定義する。
    class _BrowserStateHistory:
        # EN: Keep a placeholder statement.
        # JP: プレースホルダー文を維持する。
        pass

    # EN: Define class `_TabClosedEvent`.
    # JP: クラス `_TabClosedEvent` を定義する。
    class _TabClosedEvent:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            # EN: Keep a placeholder statement.
            # JP: プレースホルダー文を維持する。
            pass

    # EN: Define class `_ViewportSize`.
    # JP: クラス `_ViewportSize` を定義する。
    class _ViewportSize:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            # EN: Assign value to target variable.
            # JP: target variable に値を代入する。
            self.width = kwargs.get("width", 0)
            # EN: Assign value to target variable.
            # JP: target variable に値を代入する。
            self.height = kwargs.get("height", 0)

    # EN: Define class `_Message`.
    # JP: クラス `_Message` を定義する。
    class _Message:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, content=None):
            # EN: Assign value to target variable.
            # JP: target variable に値を代入する。
            self.content = content

    # EN: Define class `_BaseChatModel`.
    # JP: クラス `_BaseChatModel` を定義する。
    class _BaseChatModel:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            # EN: Keep a placeholder statement.
            # JP: プレースホルダー文を維持する。
            pass

    # EN: Define class `_ChatOpenAI`.
    # JP: クラス `_ChatOpenAI` を定義する。
    class _ChatOpenAI(_BaseChatModel):
        # EN: Keep a placeholder statement.
        # JP: プレースホルダー文を維持する。
        pass

    # EN: Define class `_ChatGoogle`.
    # JP: クラス `_ChatGoogle` を定義する。
    class _ChatGoogle(_BaseChatModel):
        # EN: Keep a placeholder statement.
        # JP: プレースホルダー文を維持する。
        pass

    # EN: Define class `_ChatAnthropic`.
    # JP: クラス `_ChatAnthropic` を定義する。
    class _ChatAnthropic(_BaseChatModel):
        # EN: Keep a placeholder statement.
        # JP: プレースホルダー文を維持する。
        pass

    # EN: Define class `_ChatGroq`.
    # JP: クラス `_ChatGroq` を定義する。
    class _ChatGroq(_BaseChatModel):
        # EN: Keep a placeholder statement.
        # JP: プレースホルダー文を維持する。
        pass

    # EN: Define function `_apply_model_selection`.
    # JP: 関数 `_apply_model_selection` を定義する。
    def _apply_model_selection(*_args, **_kwargs):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return ("openai", "dummy", "")

    # EN: Define function `_load_selection`.
    # JP: 関数 `_load_selection` を定義する。
    def _load_selection(*_args, **_kwargs):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return {"provider": "openai", "model": "dummy", "base_url": ""}

    # EN: Define function `_update_override`.
    # JP: 関数 `_update_override` を定義する。
    def _update_override(selection_override=None):
        # EN: Branch logic based on a condition.
        # JP: 条件に応じて処理を分岐する。
        if isinstance(selection_override, dict):
            # EN: Return a value from the function.
            # JP: 関数から値を返す。
            return {
                "provider": selection_override.get("provider", "openai"),
                "model": selection_override.get("model", "dummy"),
                "base_url": selection_override.get("base_url", ""),
            }
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return {"provider": "openai", "model": "dummy", "base_url": ""}

    # EN: Define function `_load_secrets_env`.
    # JP: 関数 `_load_secrets_env` を定義する。
    def _load_secrets_env(*_args, **_kwargs):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return None

    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    browser_use_stub.Agent = _Agent
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    browser_use_stub.BrowserProfile = _BrowserProfile
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    browser_use_stub.BrowserSession = _BrowserSession
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    browser_use_stub.Tools = _Tools

    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    agent_views_stub.ActionResult = _ActionResult
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    agent_views_stub.AgentHistoryList = _AgentHistoryList
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    agent_views_stub.AgentOutput = _AgentOutput

    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    browser_views_stub.BrowserStateSummary = _BrowserStateSummary
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    browser_views_stub.BrowserStateHistory = _BrowserStateHistory
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    browser_events_stub.TabClosedEvent = _TabClosedEvent
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    browser_profile_stub.ViewportSize = _ViewportSize

    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    model_selection_stub.apply_model_selection = _apply_model_selection
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    model_selection_stub.update_override = _update_override
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    model_selection_stub._load_selection = _load_selection
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    model_selection_stub.PROVIDER_DEFAULTS = {
        "openai": {"api_key_env": "OPENAI_API_KEY"},
        "gemini": {"api_key_env": "GEMINI_API_KEY"},
        "claude": {"api_key_env": "ANTHROPIC_API_KEY"},
        "groq": {"api_key_env": "GROQ_API_KEY"},
    }

    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    llm_base_stub.BaseChatModel = _BaseChatModel
    # EN: Define class `_ModelProviderError`.
    # JP: クラス `_ModelProviderError` を定義する。
    class _ModelProviderError(Exception):
        # EN: Keep a placeholder statement.
        # JP: プレースホルダー文を維持する。
        pass

    # EN: Define class `_ModelRateLimitError`.
    # JP: クラス `_ModelRateLimitError` を定義する。
    class _ModelRateLimitError(Exception):
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, message=None, model=None):
            # EN: Evaluate an expression.
            # JP: 式を評価する。
            super().__init__(message)
            # EN: Assign value to target variable.
            # JP: target variable に値を代入する。
            self.model = model

    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    llm_exceptions_stub.ModelProviderError = _ModelProviderError
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    llm_exceptions_stub.ModelRateLimitError = _ModelRateLimitError
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    llm_messages_stub.SystemMessage = _Message
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    llm_messages_stub.UserMessage = _Message
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    llm_openai_stub.ChatOpenAI = _ChatOpenAI
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    llm_google_stub.ChatGoogle = _ChatGoogle
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    llm_anthropic_stub.ChatAnthropic = _ChatAnthropic
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    llm_groq_stub.ChatGroq = _ChatGroq
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    env_loader_stub.load_secrets_env = _load_secrets_env

    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use"] = browser_use_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.agent"] = agent_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.agent.views"] = agent_views_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.browser"] = browser_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.browser.views"] = browser_views_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.browser.events"] = browser_events_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.browser.profile"] = browser_profile_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.model_selection"] = model_selection_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.llm"] = llm_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.llm.base"] = llm_base_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.llm.exceptions"] = llm_exceptions_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.llm.messages"] = llm_messages_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.llm.openai.chat"] = llm_openai_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.llm.google.chat"] = llm_google_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.llm.anthropic.chat"] = llm_anthropic_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.llm.groq.chat"] = llm_groq_stub
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    sys.modules["browser_use.env_loader"] = env_loader_stub


# Force stubs for browser_use to avoid heavy optional deps during tests.
# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if os.environ.get("BROWSER_USE_TEST_STUBS", "1") == "1":
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    _install_browser_use_stubs()
