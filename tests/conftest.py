import sys
import types
import os

try:
    import psutil  # noqa: F401
except ModuleNotFoundError:
    stub = types.ModuleType("psutil")
    # minimal attributes used by browser_use.config
    stub.virtual_memory = lambda: types.SimpleNamespace(total=0)
    stub.cpu_count = lambda: 1
    sys.modules["psutil"] = stub

try:
    import bubus  # noqa: F401
except ModuleNotFoundError:
    bus_stub = types.ModuleType("bubus")
    service_stub = types.ModuleType("bubus.service")

    # EN: Define class `_EventBus`.
    # JP: クラス `_EventBus` を定義する。
    class _EventBus:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            pass

        # EN: Define function `publish`.
        # JP: 関数 `publish` を定義する。
        def publish(self, *args, **kwargs):
            return None

    # EN: Define function `_noop`.
    # JP: 関数 `_noop` を定義する。
    def _noop(*args, **kwargs):
        return None

    # EN: Define class `_BaseEvent`.
    # JP: クラス `_BaseEvent` を定義する。
    class _BaseEvent:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            pass

    bus_stub.EventBus = _EventBus
    bus_stub.BaseEvent = _BaseEvent
    service_stub.get_handler_id = _noop
    service_stub.get_handler_name = _noop
    service_stub.logger = types.SimpleNamespace(info=_noop, warning=_noop, error=_noop)

    sys.modules["bubus"] = bus_stub
    sys.modules["bubus.service"] = service_stub

try:
    import uuid_extensions  # noqa: F401
except ModuleNotFoundError:
    uuid_stub = types.ModuleType("uuid_extensions")
    uuid_stub.uuid7str = lambda: "00000000-0000-7000-0000-000000000000"
    sys.modules["uuid_extensions"] = uuid_stub

try:
    import cdp_use  # noqa: F401
except ModuleNotFoundError:
    cdp_stub = types.ModuleType("cdp_use")
    cdp_cdp_stub = types.ModuleType("cdp_use.cdp")
    cdp_target_stub = types.ModuleType("cdp_use.cdp.target")

    # EN: Define class `_TargetID`.
    # JP: クラス `_TargetID` を定義する。
    class _TargetID(str):
        pass

    cdp_target_stub.TargetID = _TargetID

    sys.modules["cdp_use"] = cdp_stub
    sys.modules["cdp_use.cdp"] = cdp_cdp_stub
    sys.modules["cdp_use.cdp.target"] = cdp_target_stub


# EN: Define function `_install_browser_use_stubs`.
# JP: 関数 `_install_browser_use_stubs` を定義する。
def _install_browser_use_stubs():
    browser_use_stub = types.ModuleType("browser_use")
    agent_stub = types.ModuleType("browser_use.agent")
    agent_views_stub = types.ModuleType("browser_use.agent.views")
    browser_stub = types.ModuleType("browser_use.browser")
    browser_views_stub = types.ModuleType("browser_use.browser.views")
    browser_events_stub = types.ModuleType("browser_use.browser.events")
    browser_profile_stub = types.ModuleType("browser_use.browser.profile")
    model_selection_stub = types.ModuleType("browser_use.model_selection")
    llm_stub = types.ModuleType("browser_use.llm")
    llm_base_stub = types.ModuleType("browser_use.llm.base")
    llm_exceptions_stub = types.ModuleType("browser_use.llm.exceptions")
    llm_messages_stub = types.ModuleType("browser_use.llm.messages")
    llm_openai_stub = types.ModuleType("browser_use.llm.openai.chat")
    llm_google_stub = types.ModuleType("browser_use.llm.google.chat")
    llm_anthropic_stub = types.ModuleType("browser_use.llm.anthropic.chat")
    llm_groq_stub = types.ModuleType("browser_use.llm.groq.chat")
    env_loader_stub = types.ModuleType("browser_use.env_loader")

    # EN: Define class `_Agent`.
    # JP: クラス `_Agent` を定義する。
    class _Agent:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            pass

    # EN: Define class `_BrowserProfile`.
    # JP: クラス `_BrowserProfile` を定義する。
    class _BrowserProfile:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            pass

    # EN: Define class `_BrowserSession`.
    # JP: クラス `_BrowserSession` を定義する。
    class _BrowserSession:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            pass

    # EN: Define class `_Tools`.
    # JP: クラス `_Tools` を定義する。
    class _Tools:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            pass

    # EN: Define class `_ActionResult`.
    # JP: クラス `_ActionResult` を定義する。
    class _ActionResult:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            pass

    # EN: Define class `_AgentHistoryList`.
    # JP: クラス `_AgentHistoryList` を定義する。
    class _AgentHistoryList:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            self.history = []

        # EN: Define function `load_from_file`.
        # JP: 関数 `load_from_file` を定義する。
        @classmethod
        def load_from_file(cls, *args, **kwargs):
            return cls()

    # EN: Define class `_AgentOutput`.
    # JP: クラス `_AgentOutput` を定義する。
    class _AgentOutput:
        pass

    # EN: Define class `_BrowserStateSummary`.
    # JP: クラス `_BrowserStateSummary` を定義する。
    class _BrowserStateSummary:
        pass

    # EN: Define class `_BrowserStateHistory`.
    # JP: クラス `_BrowserStateHistory` を定義する。
    class _BrowserStateHistory:
        pass

    # EN: Define class `_TabClosedEvent`.
    # JP: クラス `_TabClosedEvent` を定義する。
    class _TabClosedEvent:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            pass

    # EN: Define class `_ViewportSize`.
    # JP: クラス `_ViewportSize` を定義する。
    class _ViewportSize:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            self.width = kwargs.get("width", 0)
            self.height = kwargs.get("height", 0)

    # EN: Define class `_Message`.
    # JP: クラス `_Message` を定義する。
    class _Message:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, content=None):
            self.content = content

    # EN: Define class `_BaseChatModel`.
    # JP: クラス `_BaseChatModel` を定義する。
    class _BaseChatModel:
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, *args, **kwargs):
            pass

    # EN: Define class `_ChatOpenAI`.
    # JP: クラス `_ChatOpenAI` を定義する。
    class _ChatOpenAI(_BaseChatModel):
        pass

    # EN: Define class `_ChatGoogle`.
    # JP: クラス `_ChatGoogle` を定義する。
    class _ChatGoogle(_BaseChatModel):
        pass

    # EN: Define class `_ChatAnthropic`.
    # JP: クラス `_ChatAnthropic` を定義する。
    class _ChatAnthropic(_BaseChatModel):
        pass

    # EN: Define class `_ChatGroq`.
    # JP: クラス `_ChatGroq` を定義する。
    class _ChatGroq(_BaseChatModel):
        pass

    # EN: Define function `_apply_model_selection`.
    # JP: 関数 `_apply_model_selection` を定義する。
    def _apply_model_selection(*_args, **_kwargs):
        return ("openai", "dummy", "")

    # EN: Define function `_load_selection`.
    # JP: 関数 `_load_selection` を定義する。
    def _load_selection(*_args, **_kwargs):
        return {"provider": "openai", "model": "dummy", "base_url": ""}

    # EN: Define function `_update_override`.
    # JP: 関数 `_update_override` を定義する。
    def _update_override(selection_override=None):
        if isinstance(selection_override, dict):
            return {
                "provider": selection_override.get("provider", "openai"),
                "model": selection_override.get("model", "dummy"),
                "base_url": selection_override.get("base_url", ""),
            }
        return {"provider": "openai", "model": "dummy", "base_url": ""}

    # EN: Define function `_load_secrets_env`.
    # JP: 関数 `_load_secrets_env` を定義する。
    def _load_secrets_env(*_args, **_kwargs):
        return None

    browser_use_stub.Agent = _Agent
    browser_use_stub.BrowserProfile = _BrowserProfile
    browser_use_stub.BrowserSession = _BrowserSession
    browser_use_stub.Tools = _Tools

    agent_views_stub.ActionResult = _ActionResult
    agent_views_stub.AgentHistoryList = _AgentHistoryList
    agent_views_stub.AgentOutput = _AgentOutput

    browser_views_stub.BrowserStateSummary = _BrowserStateSummary
    browser_views_stub.BrowserStateHistory = _BrowserStateHistory
    browser_events_stub.TabClosedEvent = _TabClosedEvent
    browser_profile_stub.ViewportSize = _ViewportSize

    model_selection_stub.apply_model_selection = _apply_model_selection
    model_selection_stub.update_override = _update_override
    model_selection_stub._load_selection = _load_selection
    model_selection_stub.PROVIDER_DEFAULTS = {
        "openai": {"api_key_env": "OPENAI_API_KEY"},
        "gemini": {"api_key_env": "GEMINI_API_KEY"},
        "claude": {"api_key_env": "ANTHROPIC_API_KEY"},
        "groq": {"api_key_env": "GROQ_API_KEY"},
    }

    llm_base_stub.BaseChatModel = _BaseChatModel
    # EN: Define class `_ModelProviderError`.
    # JP: クラス `_ModelProviderError` を定義する。
    class _ModelProviderError(Exception):
        pass

    # EN: Define class `_ModelRateLimitError`.
    # JP: クラス `_ModelRateLimitError` を定義する。
    class _ModelRateLimitError(Exception):
        # EN: Define function `__init__`.
        # JP: 関数 `__init__` を定義する。
        def __init__(self, message=None, model=None):
            super().__init__(message)
            self.model = model

    llm_exceptions_stub.ModelProviderError = _ModelProviderError
    llm_exceptions_stub.ModelRateLimitError = _ModelRateLimitError
    llm_messages_stub.SystemMessage = _Message
    llm_messages_stub.UserMessage = _Message
    llm_openai_stub.ChatOpenAI = _ChatOpenAI
    llm_google_stub.ChatGoogle = _ChatGoogle
    llm_anthropic_stub.ChatAnthropic = _ChatAnthropic
    llm_groq_stub.ChatGroq = _ChatGroq
    env_loader_stub.load_secrets_env = _load_secrets_env

    sys.modules["browser_use"] = browser_use_stub
    sys.modules["browser_use.agent"] = agent_stub
    sys.modules["browser_use.agent.views"] = agent_views_stub
    sys.modules["browser_use.browser"] = browser_stub
    sys.modules["browser_use.browser.views"] = browser_views_stub
    sys.modules["browser_use.browser.events"] = browser_events_stub
    sys.modules["browser_use.browser.profile"] = browser_profile_stub
    sys.modules["browser_use.model_selection"] = model_selection_stub
    sys.modules["browser_use.llm"] = llm_stub
    sys.modules["browser_use.llm.base"] = llm_base_stub
    sys.modules["browser_use.llm.exceptions"] = llm_exceptions_stub
    sys.modules["browser_use.llm.messages"] = llm_messages_stub
    sys.modules["browser_use.llm.openai.chat"] = llm_openai_stub
    sys.modules["browser_use.llm.google.chat"] = llm_google_stub
    sys.modules["browser_use.llm.anthropic.chat"] = llm_anthropic_stub
    sys.modules["browser_use.llm.groq.chat"] = llm_groq_stub
    sys.modules["browser_use.env_loader"] = env_loader_stub


# Force stubs for browser_use to avoid heavy optional deps during tests.
if os.environ.get("BROWSER_USE_TEST_STUBS", "1") == "1":
    _install_browser_use_stubs()
