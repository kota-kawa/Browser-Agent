/// <reference types="vite/client" />

// JP: テンプレートから注入されるグローバル変数の型定義
// EN: Global typings for template-injected variables
import type { AgentResultAppProps, IndexAppProps, WebArenaAppProps } from './types/app';

declare global {
  interface Window {
    __INDEX_APP_PROPS__?: IndexAppProps;
    __AGENT_RESULT_APP_PROPS__?: AgentResultAppProps;
    __WEBARENA_APP_PROPS__?: WebArenaAppProps;
  }
}

export {};
