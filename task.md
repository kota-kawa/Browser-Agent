# Current Task Context

## 今回やること・目的 (Goal/Objective)
<!-- 何のために何をするのか簡潔に記述 -->
- [ ] フロントエンドを React(TypeScript) に完全移行し、既存 UI/機能/挙動を一切変えずに型安全化と開発基盤を整備する。

## やること (Must)
<!-- 具体的なタスクリスト -->
- [ ] 現行エントリ3本 (`index`/`webarena`/`agent_result`) を全て `.tsx` 化し、TypeScript でビルドできるようにする。
- [ ] Vite 設定の入力を `.tsx` に更新し、出力が `flask_app/static/dist/{index,webarena,agent_result}.js` のままになることを保証する。
- [ ] `tsconfig.json` と `vite-env.d.ts` を追加し、`strict` 系オプションを有効化する。
- [ ] `window.__INDEX_APP_PROPS__`, `__WEBARENA_APP_PROPS__`, `__AGENT_RESULT_APP_PROPS__` の型定義を用意する。
- [ ] `fetch` 先 API 応答の型定義を作成し、`response.ok` 判定や必要フィールドの存在チェックを維持する。
- [ ] 既存の DOM 操作/ResizeObserver/SSE 再接続/Thinking 表示などの挙動を TypeScript で再現し、回帰を起こさない。
- [ ] `npm run build` で `flask_app/static/dist` が生成されること、`npm run typecheck` が通ることを前提化する (必要なら script 追加)。
- [ ] `flask_app/static/js` の旧アセットが未使用であることを確認し、不要なら削除または参照を完全に廃止する。
- [ ] README/運用メモに TypeScript 移行後のビルド/開発手順を追記する (必要な場合のみ)。

## やらないこと (Non-goals)
<!-- 今回のスコープ外のこと -->
- [ ] UI/UX の大幅なリデザイン、CSS の作り直し。
- [ ] バックエンド API の仕様変更や新規 API 追加。
- [ ] 既存の日本語文言やログ仕様の変更 (必要な型付け以外)。
- [ ] 既存の挙動変更 (バグ修正・UX 改善含む) は一切行わない。

## 受け入れ基準 (Acceptance Criteria)
<!-- 完了とみなす条件 -->
- [ ] `flask_app/frontend` が TypeScript でビルド可能で、`npm run build` 後に `flask_app/static/dist/index.js` などが生成される。
- [ ] `npm run typecheck` (または `tsc --noEmit`) がエラーなしで完了する。
- [ ] `/`, `/webarena`, `/agent_result` で従来どおりの表示と主要操作 (SSE 更新・チャット送信・一時停止/再開・リセット・WebArena 実行/バッチ実行) が動作する。
- [ ] 既存の挙動が一切変わっていないこと (UI/UX・レスポンス・タイミング・状態遷移を含む)。
- [ ] DOMPurify + marked によるサニタイズ済み Markdown 描画が維持される。
- [ ] コンソールに TypeScript 起因のランタイムエラーが出ない (通常操作範囲)。
- [ ] 旧 `static/js/*.js` が参照されていない (削除/未使用が明確)。

## 影響範囲 (Impact/Scope)
<!-- 変更するファイルや注意すべき既存機能 -->
- **触るファイル**:
  - `flask_app/frontend/src/*`
  - `flask_app/frontend/vite.config.js`
  - `flask_app/frontend/package.json`
  - `flask_app/frontend/tsconfig.json`
  - `flask_app/frontend/src/vite-env.d.ts` など型定義ファイル
  - `flask_app/templates/*.html` (必要な場合のみ)
  - `flask_app/static/dist/*` (ビルド生成物)
  - `flask_app/static/js/*` (不要化または削除の場合)
- **壊しちゃいけない挙動**:
  - SSE ストリームの接続/再接続とステータス表示
  - チャット履歴の取得/表示/スクロール制御
  - モデル選択・Vision 設定・WebArena タスク実行のフロー
  - ブラウザ iframe の高さ同期やレスポンシブ表示
