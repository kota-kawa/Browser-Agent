import type { EnvUrls } from './api';

export interface IndexAppProps {
  browserUrl: string;
}

export interface AgentResultAppProps {
  browserUrl: string;
}

export interface WebArenaAppProps {
  browserUrl: string;
  envUrls: EnvUrls;
  supportedSites: string[];
}
