// JP: HTML テンプレートから注入される初期Propsの型定義
// EN: Type definitions for initial props injected by templates
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
