# Agent Playbook

## 目的と全体像
- このリポジトリは `browser_use` のフルソースと、FastAPI ベースのブラウザ操作エージェント UI/API (`flask_app/`) を同梱します。
- 主要な変更点は `flask_app/services/agent_controller.py` の `BrowserAgentController` と `flask_app/routes/` の HTTP エンドポイント群です。Gemini ベースの LLM、Chrome DevTools (CDP) セッション、EventBus を常駐させ、SSE で UI に進捗を配信します。
- `IMPLEMENTATION_SUMMARY.md` は本ファイルに統合されました。最新の仕様はこのファイルを参照してください。

## ディレクトリ構成の要点
- `browser_use/` : OSS 本体。`agent/`, `controller/`, `browser/`, `llm/`, `tokens/`, `tools/`, `telemetry/`, `mcp/` などに機能が分類されています。
  - `browser_use/agent/scratchpad.py`: エージェントが構造化データを一時保存するための「メモ帳」機能。
- `flask_app/` : Web サーバー、SSE、静的 UI、Docker `Dockerfile.flask`、`requirements.txt` を含むアプリ本体 (FastAPI)。
  - `core/` (設定/環境), `services/` (実行ロジック), `routes/` (HTTP), `prompts/` (system prompt) に分割。
  - `webarena/`: WebArena ベンチマーク実行環境とルート定義。
  - `templates/index.html` + `static/css/style.css` が UI。
- `docs/` : Mintlify 互換ドキュメント。プレビューは `cd docs && npx mintlify dev` を使用。
- `examples/` : サンプル集。
- `docker/` とトップレベル `Dockerfile*` : Chrome/VNC コンテナと FastAPI コンテナのビルド設定。
- `bin/` : `setup.sh`, `test.sh`, `lint.sh`。`uv` ベースの開発環境を前提。
- `flask_app/prompts/system_prompt_browser_agent.md` : FastAPI アプリが読み込むカスタム system prompt。

## Runtime/Controller の仕組み
- `BrowserAgentController` (`flask_app/services/agent_controller.py`)
  - CDP URL を検出 (`_resolve_cdp_url`) し、`BrowserSession` を常駐させるスレッド＋イベントループを持ちます。
  - `ChatGoogle` (Gemini) を生成し、`Agent` を初期化。
  - `enqueue_follow_up`, `pause`, `resume`, `reset` など状態管理 API を公開。
  - EventBus (`bubus.EventBus`) + SSE で UI にステップ別ログを配信。
- CDP/ブラウザ
  - `BROWSER_USE_CDP_URL` 明示指定推奨。
  - `EMBED_BROWSER_URL` を `noVNC` に向け、iframe に表示。
  - **CDP Session Strategy**: WebArena バッチ実行時の安定性向上のため、デフォルトで Chrome インスタンスごとの共有ソケットを使用。専用ソケット (`BROWSER_USE_DEDICATED_SOCKET_PER_TARGET=true`) はオプション。

## 主要機能と実装詳細

### 1. WebArena Automation
ローカル環境で WebArena ベンチマーク (Shopping, Shopping Admin, Reddit, GitLab) を実行・評価する機能です。
- **Batch Runner**: `/webarena/run_batch` エンドポイントにより、フィルタリングされたタスクを順次実行します。UI 上では "表示中タスクを順番に実行" ボタンでトリガーされます。
- **Environment**: 未使用の MAP URL フィールドを削除し、実在する環境のみをサポート。
- **Safety**: 各タスク実行前にブラウザセッションをリセットし、前のタスクのタブを閉じてから新規タブで開始します (`ensure_start_page_ready`)。
- **Vision**: WebArena 実行時はスクリーンショット解析 (Vision) が強制的に有効化されます。
- **Step Limit**: WebArena タスクは `WEBARENA_AGENT_MAX_STEPS` (デフォルト 20) で制限されます。

### 2. Scratchpad (外部メモ機能)
エージェントの Context Window (短期記憶) だけに頼らず、収集した構造化データを一時保存する「メモ帳」領域です。
- **Purpose**: 「店名・価格・評価」のようなデータを構造化して保持し、タスク終了時にまとめて回答生成に使用することで、情報の取りこぼしを防ぎます。
- **Integration**: `AgentState` に `scratchpad` オブジェクトが含まれます。
- **Tools**:
  - `scratchpad_add`: 新規エントリ追加
  - `scratchpad_update`: 既存エントリ更新 (マージ可能)
  - `scratchpad_remove`: エントリ削除
  - `scratchpad_get`: 情報取得 (サマリー生成)
  - `scratchpad_clear`: 全削除

## HTTP API とフロントエンド
- `GET /` : noVNC iframe + チャット UI。
- `GET /api/stream` : SSE (Server-Sent Events) でログやステータスを配信。
- `POST /api/chat` : UI からの通常実行。`skip_conversation_review=true` で分析スキップ可能。
- `POST /api/agent-relay` : 他エージェント用。アイドル時は即時実行、稼働中はキューイング。
- `GET /webarena/tasks` : WebArena タスク一覧取得。
- `POST /webarena/run` : WebArena 単体タスク実行。
- `POST /webarena/run_batch` : WebArena バッチ実行。

## LLM・プロンプト関連
- `flask_app/prompts/system_prompt_browser_agent.md`
  - `{max_actions}`, `{current_datetime}` プレースホルダ対応。
  - `<scratchpad>` セクションでメモ帳機能の使用法を定義。
  - `read_file` アクションの禁止や、日本語応答の強制が含まれています。
- `flask_app/prompts/system_prompt.py`: システムプロンプト構築ロジック。タイムゾーンを考慮した日時を注入します。

## ビルド・実行・検証
- **セットアップ**: `./bin/setup.sh` (uv venv + 依存インストール)。
- **起動**:
  - 直接: `uv run uvicorn flask_app.app:app --host 0.0.0.0 --port 5005` (別途 Chrome 必要)
  - Docker: `docker compose up --build`
- **テスト**:
  - `./bin/test.sh`
- **Lint**: `./bin/lint.sh`

## ドキュメント・サンプル
- `docs/`: API/実装メモ。

## セキュリティ & 設定
- `secrets.env` に API キーを設定 (コミット禁止)。
- `BROWSER_USE_LOGGING_LEVEL` でログレベル制御。
- LLM 応答の JSON パースは `flask_app/services/conversation_review.py` で堅牢に行われ、Markdown ブロック除去などに対応しています。

## Critical Instruction / 重要指示
どれだけ時間とコストをかけてもよいので、確実に目標が達成されるようにしてほしい。
