# JP: UI で選択可能な LLM モデル一覧
# EN: List of LLM models available for selection in the UI
SUPPORTED_MODELS = [
	# JP: Groq 系モデル
	# EN: Groq-backed models
	{'provider': 'groq', 'model': 'openai/gpt-oss-20b', 'label': 'GPT-OSS 20B (Groq)'},
	{'provider': 'groq', 'model': 'llama-3.3-70b-versatile', 'label': 'Llama 3.3 70B (Groq)'},
	{'provider': 'groq', 'model': 'llama-3.1-8b-instant', 'label': 'Llama 3.1 8B (Groq)'},
	{'provider': 'groq', 'model': 'qwen/qwen3-32b', 'label': 'Qwen3 32B (Groq)'},
	# JP: OpenAI 系モデル
	# EN: OpenAI-backed models
	{'provider': 'openai', 'model': 'gpt-5.1', 'label': 'GPT-5.1'},
	# JP: Gemini (Google) 系モデル
	# EN: Gemini (Google) models
	{'provider': 'gemini', 'model': 'gemini-3-pro-preview', 'label': 'Gemini 3 Pro Preview'},
	# JP: Claude (Anthropic) 系モデル
	# EN: Claude (Anthropic) models
	{'provider': 'claude', 'model': 'claude-haiku-4-5', 'label': 'Claude Haiku 4.5'},
	{'provider': 'claude', 'model': 'claude-opus-4-5', 'label': 'Claude Opus 4.5'},
]
