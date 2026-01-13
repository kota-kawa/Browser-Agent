# Browser-Agent

日本語 | [English](README.en.md)

<p align="center">
  <img src="static/Browser-Agent-Icon.png" width="800" alt="Browser-Agent Icon">
</p>

最新のLLMを活用したFastAPIベースのWebインターフェース付きブラウザ自動化エージェントです。自然言語でブラウザを操作でき、実行状況をリアルタイムで可視化し、WebArenaのようなベンチマークも実行できます。

## 🚀 概要

`Browser-Agent` は `browser_use` ライブラリと堅牢なFastAPIバックエンドを統合し、次の機能を提供します。
- **自然言語操作**: 「東京行きの最安フライトを探して」や「アカウントにログインしてメッセージを確認して」といった指示でブラウザを操作します。
- **リアルタイム可視化**: noVNCストリームでエージェントの動作を見ながら、UI上でステップごとのログを確認できます。
- **マルチLLM対応**: Gemini、OpenAI、Anthropic、DeepSeek などに対応しています。
- **WebArenaベンチマーク**: 標準的なブラウザ自動化ベンチマークを実行・評価するツールを内蔵しています。

## ✨ 主な機能

- **Webインターフェース**: エージェントの操作、ブラウザ画面の確認、実行ログの監視を行える、クリーンでレスポンシブなUI。
- **ライブストリーミング**: Server-Sent Events (SSE) とVNCでリアルタイムにフィードバック。
- **Scratchpad**: タスク中に抽出したデータ（価格、名前、レビューなど）を構造化して保存する専用メモリ。
- **Docker対応**: Docker Composeによる簡単なデプロイに対応。
- **拡張可能なアーキテクチャ**: コアエージェント（`browser_use`）、APIサービス（`flask_app`）、UIを分離したモジュール設計。

## 🛠️ インストール

### 前提条件
- **Python 3.11+**
- **Docker & Docker Compose**（フルスタック推奨）
- **uv**（ローカルPython管理に推奨）
- **Google Chrome**（Dockerなしでローカル実行する場合）

### 1. リポジトリをクローン
```bash
git clone https://github.com/kota-kawa/Browser-Agent.git
cd browser-agent
```

### 2. 環境設定
サンプルのシークレットファイルをコピーしてAPIキーを設定します。
```bash
cp secrets.env.example secrets.env
```
`secrets.env` を編集し、LLMプロバイダのキー（例: `GOOGLE_API_KEY`, `OPENAI_API_KEY`）を追加してください。

### 3. Dockerで実行（推奨）
FastAPIアプリ、Chromeインスタンス、VNCサーバーが起動します。
```bash
docker-compose up --build
```
UIのアクセス先: http://localhost:5005

### 4. ローカルで実行
Dockerなしで実行する場合:

**依存関係のインストール:**
```bash
# uv を使用（推奨）
./bin/setup.sh

# または pip
pip install -r flask_app/requirements.txt
```

**アプリの起動:**
リモートデバッグを有効にしたChromeを起動するか、`BROWSER_USE_CDP_URL` にリモートCDPエンドポイントを指定してください。
```bash
uv run uvicorn flask_app.app:app --host 0.0.0.0 --port 5005
```

## 📖 使い方

### Web UI
1. ブラウザで http://localhost:5005 を開きます。
2. チャットボックスに指示を入力します（例: "amazon.comに行って良いメカニカルキーボードを探して"）。
3. エージェントがタスクを実行します。左側にブラウザ画面、右側にログとチャットが表示されます。

### WebArena ベンチマーク
UIの「WebArena」タブから、またはAPIを使って標準ベンチマークタスクを実行・評価できます。

### API エンドポイント
- `POST /api/chat`: エージェントにタスクを送信します。
- `GET /api/stream`: ログ用イベントストリームに接続します。
- `POST /webarena/run`: WebArenaの特定タスクを実行します。

## 📂 プロジェクト構成

```
/
├── browser_use/       # コアエージェントロジック、DOM操作、ツール
├── flask_app/         # FastAPI Webサーバー、APIルート、UIテンプレート
│   ├── core/          # 設定と環境構築
│   ├── services/      # ビジネスロジック（Agent Controller, History）
│   ├── routes/        # APIエンドポイント
│   └── templates/     # HTMLフロントエンド
├── docker-compose.yml # コンテナオーケストレーション
└── secrets.env        # APIキーと設定
```

## 🧪 開発

### テスト実行
```bash
./bin/test.sh
```

### Lint
```bash
./bin/lint.sh
```

## 📄 ライセンス

詳細は [LICENSE.md](LICENSE.md) を参照してください。
