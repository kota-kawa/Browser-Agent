# Project Specifications & Guidelines

## 全体ルール (General Rules)
<!-- プロジェクト全体で遵守すべき原則 -->
- [ ] React 18 + Vite を維持し、フロントエンドは TypeScript に統一する (新規 JS/JSX 禁止)。
- [ ] `strict` 系コンパイラ設定を有効化し、`any`/`@ts-ignore` は原則禁止 (例外は理由コメント必須)。
- [ ] 既存の画面構成/文言/データフロー/UX を保持し、機能回帰を起こさない。
- [ ] 既存の動作は一切変更しない (挙動・タイミング・状態遷移・レスポンス内容・副作用を含む)。
- [ ] 既存の CSS (`flask_app/static/css/base.css` + ページ別 CSS) をそのまま利用し、JS 側でスタイルを作り直さない。
- [ ] API は現行エンドポイントを前提とし、フロント側から仕様変更を要求しない。
- [ ] ビルド成果物は `flask_app/static/dist` に固定し、テンプレート参照名は `index.js` / `webarena.js` / `agent_result.js` を維持する。

## コーディング規約 (Coding Conventions)
<!-- 言語ごとのスタイルガイド、フォーマッター設定など -->
- **Python**:
  - 変更対象外。ただしテンプレートの script 参照が変わる場合は同期する。
- **JavaScript/React**:
  - TypeScript を使用し、関数コンポーネント + Hooks を基本とする。
  - `.tsx` は JSX を含むファイルのみ、純粋なロジックは `.ts` に分離する。
  - `useEffect`/`useLayoutEffect`/`useMemo`/`useCallback` の依存配列を必ず正しく記述する。
  - DOM 操作が必要な箇所は `useRef` と型注釈で安全化し、`null` を考慮する。
  - `fetch` は `response.ok` 判定 + 例外処理を徹底し、JSON 形状が崩れた場合はフォールバックを用意する。
  - SSE(EventSource) の再接続/ステータス更新ロジックは現行挙動を維持する。
  - Markdown 描画は `marked` + `dompurify` を継続し、`dangerouslySetInnerHTML` はこの用途に限定する。

## TypeScript 設定 (tsconfig)
- `target`: `ES2020` 以上
- `module`: `ESNext`
- `moduleResolution`: `Bundler`
- `jsx`: `react-jsx`
- `strict`: `true`
- `noImplicitAny`: `true`
- `noUncheckedIndexedAccess`: `true`
- `exactOptionalPropertyTypes`: `true`
- `noFallthroughCasesInSwitch`: `true`
- `types`: `["vite/client"]`
- `include`: `src/**/*` と型定義ファイル
- `noEmit`: `true` (型チェック専用。ビルドは Vite が担当)

## 命名規則 (Naming Conventions)
<!-- 変数、関数、クラス、ファイル名の命名ルール -->
- **Variables/Functions**: `camelCase`
- **Classes/Types/Interfaces**: `PascalCase` (例: `ChatMessage`, `ModelOption`, `VisionState`)
- **Components**: `PascalCase`
- **Hooks**: `useXxx`
- **Files**:
  - エントリ: `index.tsx`, `webarena.tsx`, `agent_result.tsx`
  - コンポーネント: `PascalCase.tsx`
  - 型定義/ユーティリティ: `*.ts` (例: `types.ts`, `api.ts`)
- **Constants**: `UPPER_SNAKE_CASE` (例: `MIN_THINKING_MS`)

## ディレクトリ構成方針 (Directory Structure Policy)
<!-- ファイルの配置ルール、モジュール分割の方針 -->
- `flask_app/frontend/src/`
  - ルートにエントリ `index.tsx`, `webarena.tsx`, `agent_result.tsx` を配置する。
  - 共通部品は `components/`、共通ロジックは `lib/`、型定義は `types/` に集約する。
  - グローバル型拡張は `src/types/global.d.ts` もしくは `src/vite-env.d.ts` に配置する。
- `flask_app/static/css/base.css` とページ別 CSS は引き続きテンプレートで読み込み、Vite 側で CSS をバンドルしない (必要があれば別途検討)。

## Vite ビルド方針
- `build.outDir`: `../static/dist`
- `rollupOptions.input`: `index.tsx`, `webarena.tsx`, `agent_result.tsx`
- `entryFileNames`: `[name].js` を維持し、テンプレート参照を変更しない。

## エラーハンドリング方針 (Error Handling Policy)
<!-- 例外処理、ログ出力、ユーザーへのフィードバック方法 -->
- API レスポンス:
  - `response.ok` で成否判断し、失敗時は UI ステータス/エラーメッセージを表示する。
  - JSON の期待形が崩れた場合は空配列/デフォルト値にフォールバックする。
- SSE:
  - `onerror` で接続状態を `disconnected` にし、再接続タイマーでリトライする。
- ユーザー操作:
  - `isSending`/`isRunning` などのフラグで多重送信を防止する。

## テスト方針 (Testing Policy)
<!-- テストの種類、カバレッジ目標、使用ツール -->
- **Unit Tests**: 今回の移行では追加しない (将来的に共通ロジックへ導入候補)。
- **Type Check**:
  - `tsc --noEmit` を必須とする。
- **Build Smoke**:
  - `npm run build` が成功し、`flask_app/static/dist` に必要なエントリファイルが生成されること。
- **Manual**:
  - `/` で SSE 更新、チャット送信、停止/再開/リセットが動作すること。
  - `/webarena` でモデル選択・Vision 切替・タスク実行/バッチ実行が動作すること。
  - `/agent_result` で iframe 表示と高さ同期が動作すること。

## グローバルプロパティ (Window Props)
- `window.__INDEX_APP_PROPS__`: `{ browserUrl: string }`
- `window.__AGENT_RESULT_APP_PROPS__`: `{ browserUrl: string }`
- `window.__WEBARENA_APP_PROPS__`: `{ browserUrl: string, envUrls: { shopping: string, shopping_admin: string, gitlab: string, reddit: string }, supportedSites: string[] }`

## フロントエンド型定義 (Type Contracts)
- **ChatMessage**: `{ id: number, role: 'user' | 'assistant' | 'system', content: string, timestamp: string }`
- **SSEEvent**:
  - `type: 'message' | 'update' | 'reset' | 'status' | 'model'`
  - `payload`:
    - `message/update`: `ChatMessage`
    - `status`: `{ agent_running?: boolean, run_summary?: string }`
    - `model`: `{ provider: string, model: string, label?: string, base_url?: string }`
- **ModelsResponse**: `{ models: ModelOption[], current: ModelSelection }`
- **ModelOption**: `{ provider: string, model: string, label?: string, base_url?: string }`
- **ModelSelection**: `{ provider: string, model: string, base_url?: string }`
- **VisionState**: `{ user_enabled: boolean, model_supported: boolean, effective: boolean, provider: string, model: string }`
- **ChatResponse (POST /api/chat)**:
  - 成功: `{ messages: ChatMessage[], run_summary?: string, queued?: boolean, agent_running?: boolean }`
  - 失敗: `{ error: string }`
- **ResetResponse**: `{ messages: ChatMessage[] }` または `{ error: string }`
- **Pause/Resume Response**: `{ status: 'paused' | 'resumed' }` または `{ error: string }`
- **WebArenaTask**: `{ task_id: number, intent: string, start_url?: string, sites?: string[], require_login?: boolean }`
- **WebArenaRunResponse**:
  - 成功: `{ task_id: number | 'custom', success: boolean, summary: string, steps: { step: number, content: string }[], evaluation: string }`
  - 失敗: `{ error: string }`
- **WebArenaBatchResponse**:
  - `{ total_tasks: number, success_count: number, score: number, aggregate_metrics: AggregateMetrics, results: WebArenaRunResponse[] }`
- **AggregateMetrics**:
  - `{ success_rate: number, success_rate_ci_95: { lower: number, upper: number }, template_macro_sr: number, average_steps_success_only: number, average_steps_overall_with_failures_as_max: number, median_steps_success_only: number, p90_steps_success_only: number, max_steps: number }`

## 対象 API 一覧 (Frontend Contracts)
- `/api/stream` (SSE)
- `/api/history`
- `/api/chat`
- `/api/reset`
- `/api/pause`
- `/api/resume`
- `/api/models`
- `/model_settings`
- `/api/vision`
- `/webarena/tasks`
- `/webarena/run`
- `/webarena/run_batch`
- `/webarena/save_results`
