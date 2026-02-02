/// <reference types="vite/client" />

import type { AgentResultAppProps, IndexAppProps, WebArenaAppProps } from './types/app';

declare global {
  interface Window {
    __INDEX_APP_PROPS__?: IndexAppProps;
    __AGENT_RESULT_APP_PROPS__?: AgentResultAppProps;
    __WEBARENA_APP_PROPS__?: WebArenaAppProps;
  }
}

export {};
