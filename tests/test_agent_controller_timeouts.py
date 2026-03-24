import fastapi_app.services.agent_controller as controller_mod


# EN: Define function `test_resolve_step_timeout_uses_default_when_env_missing`.
# JP: 関数 `test_resolve_step_timeout_uses_default_when_env_missing` を定義する。
def test_resolve_step_timeout_uses_default_when_env_missing(monkeypatch):
    monkeypatch.delenv("BROWSER_USE_STEP_TIMEOUT", raising=False)
    monkeypatch.setattr(controller_mod, "_AGENT_STEP_TIMEOUT_SECONDS", 77)
    assert controller_mod.BrowserAgentController._resolve_step_timeout() == 77


# EN: Define function `test_resolve_step_timeout_respects_valid_env`.
# JP: 関数 `test_resolve_step_timeout_respects_valid_env` を定義する。
def test_resolve_step_timeout_respects_valid_env(monkeypatch):
    monkeypatch.setenv("BROWSER_USE_STEP_TIMEOUT", "30")
    monkeypatch.setattr(controller_mod, "_AGENT_STEP_TIMEOUT_SECONDS", 77)
    assert controller_mod.BrowserAgentController._resolve_step_timeout() == 30


# EN: Define function `test_resolve_run_timeout_uses_default_when_invalid`.
# JP: 関数 `test_resolve_run_timeout_uses_default_when_invalid` を定義する。
def test_resolve_run_timeout_uses_default_when_invalid(monkeypatch):
    monkeypatch.setenv("BROWSER_USE_RUN_TIMEOUT", "invalid")
    monkeypatch.setattr(controller_mod, "_AGENT_RUN_TIMEOUT_SECONDS", 555)
    assert controller_mod.BrowserAgentController._resolve_run_timeout() == 555
