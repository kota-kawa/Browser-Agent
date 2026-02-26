// JP: エージェント結果画面のエントリポイント
// EN: Entry point for the agent result screen
import React, { useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import type { AgentResultAppProps } from './types/app';

const initialData: Partial<AgentResultAppProps> = window.__AGENT_RESULT_APP_PROPS__ || {};
const browserUrl = initialData.browserUrl || '';

// JP: ブラウザ iframe の高さをツールバー分だけ調整する
// EN: Resize iframe to account for toolbar height
const App = () => {
  useEffect(() => {
    const browserIframe = document.querySelector<HTMLIFrameElement>('.browser-pane iframe');
    if (!browserIframe) {
      return undefined;
    }
    const shell = document.querySelector<HTMLDivElement>('.browser-shell');
    /**
     * EN: Declare variable `toolbar`.
     * JP: 変数 `toolbar` を宣言する。
     */
    const toolbar = shell ? shell.querySelector<HTMLDivElement>('.browser-toolbar') : null;

    /**
     * EN: Declare callable constant `syncIframeHeight`.
     * JP: 呼び出し可能な定数 `syncIframeHeight` を宣言する。
     */
    const syncIframeHeight = () => {
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (!shell) {
        /**
         * EN: Return a value from this scope.
         * JP: このスコープから値を返す。
         */
        return;
      }
      /**
       * EN: Declare variable `toolbarHeight`.
       * JP: 変数 `toolbarHeight` を宣言する。
       */
      const toolbarHeight = toolbar ? toolbar.offsetHeight : 0;
      /**
       * EN: Declare variable `nextHeight`.
       * JP: 変数 `nextHeight` を宣言する。
       */
      const nextHeight = Math.max(shell.clientHeight - toolbarHeight, 0);
      browserIframe.style.height = `${nextHeight}px`;
    };

    let resizeObserver: ResizeObserver | null = null;
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (shell) {
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(syncIframeHeight);
        resizeObserver.observe(shell);
      } else {
        window.addEventListener('resize', syncIframeHeight);
      }
    }

    syncIframeHeight();

    /**
     * EN: Return a value from this scope.
     * JP: このスコープから値を返す。
     */
    return () => {
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (resizeObserver) {
        resizeObserver.disconnect();
      } else {
        window.removeEventListener('resize', syncIframeHeight);
      }
    };
  }, []);

  /**
   * EN: Return a value from this scope.
   * JP: このスコープから値を返す。
   */
  return (
    <main className="full-screen-layout">
      <section className="browser-pane" aria-label="ブラウザ画面">
        <div className="browser-shell">
          <div className="browser-toolbar" role="presentation">
            <div className="browser-toolbar-dots" aria-hidden="true">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div className="browser-toolbar-title">リモートブラウザ</div>
            <div className="browser-toolbar-url" title={browserUrl}>
              {browserUrl}
            </div>
          </div>
          <iframe src={browserUrl} title="コンテナ内ブラウザ"></iframe>
        </div>
      </section>
    </main>
  );
};

/**
 * EN: Declare variable `root`.
 * JP: 変数 `root` を宣言する。
 */
const root = document.getElementById('root');
/**
 * EN: Branch logic based on a condition.
 * JP: 条件に応じて処理を分岐する。
 */
if (root) {
  createRoot(root).render(<App />);
}
