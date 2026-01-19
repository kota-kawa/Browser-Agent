import React, { useEffect } from 'react';
import { createRoot } from 'react-dom/client';

const initialData = window.__AGENT_RESULT_APP_PROPS__ || {};
const browserUrl = initialData.browserUrl || '';

const App = () => {
  useEffect(() => {
    const browserIframe = document.querySelector('.browser-pane iframe');
    if (!browserIframe) {
      return undefined;
    }
    const shell = document.querySelector('.browser-shell');
    const toolbar = shell ? shell.querySelector('.browser-toolbar') : null;

    const syncIframeHeight = () => {
      if (!shell) {
        return;
      }
      const toolbarHeight = toolbar ? toolbar.offsetHeight : 0;
      const nextHeight = Math.max(shell.clientHeight - toolbarHeight, 0);
      browserIframe.style.height = `${nextHeight}px`;
    };

    let resizeObserver;
    if (shell) {
      if (typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(syncIframeHeight);
        resizeObserver.observe(shell);
      } else {
        window.addEventListener('resize', syncIframeHeight);
      }
    }

    syncIframeHeight();

    return () => {
      if (resizeObserver) {
        resizeObserver.disconnect();
      } else {
        window.removeEventListener('resize', syncIframeHeight);
      }
    };
  }, []);

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

const root = document.getElementById('root');
if (root) {
  createRoot(root).render(<App />);
}
