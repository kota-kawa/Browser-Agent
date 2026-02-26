// JP: フロントエンドで使うAPIレスポンス型
// EN: API response types used by the frontend
export type ChatRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: number;
  role: ChatRole;
  content: string;
  timestamp: string;
}

/**
 * EN: Define interface `ModelOption`.
 * JP: インターフェース `ModelOption` を定義する。
 */
export interface ModelOption {
  provider: string;
  model: string;
  label?: string;
  base_url?: string;
}

/**
 * EN: Define interface `ModelSelection`.
 * JP: インターフェース `ModelSelection` を定義する。
 */
export interface ModelSelection {
  provider: string;
  model: string;
  base_url?: string;
  label?: string;
}

/**
 * EN: Define interface `ModelsResponse`.
 * JP: インターフェース `ModelsResponse` を定義する。
 */
export interface ModelsResponse {
  models: ModelOption[];
  current: ModelSelection;
}

/**
 * EN: Define interface `VisionState`.
 * JP: インターフェース `VisionState` を定義する。
 */
export interface VisionState {
  user_enabled: boolean;
  model_supported: boolean;
  effective: boolean;
  provider: string;
  model: string;
}

/**
 * EN: Define interface `UserProfileResponse`.
 * JP: インターフェース `UserProfileResponse` を定義する。
 */
export interface UserProfileResponse {
  text: string;
}

/**
 * EN: Define interface `StatusPayload`.
 * JP: インターフェース `StatusPayload` を定義する。
 */
export interface StatusPayload {
  agent_running?: boolean;
  run_summary?: string;
}

/**
 * EN: Define type alias `SSEEvent`.
 * JP: 型エイリアス `SSEEvent` を定義する。
 */
export type SSEEvent =
  | { type: 'message'; payload: ChatMessage }
  | { type: 'update'; payload: ChatMessage }
  | { type: 'reset' }
  | { type: 'status'; payload: StatusPayload }
  | { type: 'model'; payload: ModelOption };

/**
 * EN: Define interface `ChatResponse`.
 * JP: インターフェース `ChatResponse` を定義する。
 */
export interface ChatResponse {
  messages?: ChatMessage[];
  run_summary?: string;
  queued?: boolean;
  agent_running?: boolean;
  error?: string;
}

/**
 * EN: Define interface `ResetResponse`.
 * JP: インターフェース `ResetResponse` を定義する。
 */
export interface ResetResponse {
  messages?: ChatMessage[];
  error?: string;
}

/**
 * EN: Define interface `PauseResumeResponse`.
 * JP: インターフェース `PauseResumeResponse` を定義する。
 */
export interface PauseResumeResponse {
  status?: 'paused' | 'resumed';
  error?: string;
}

/**
 * EN: Define interface `EnvUrls`.
 * JP: インターフェース `EnvUrls` を定義する。
 */
export interface EnvUrls {
  shopping: string;
  shopping_admin: string;
  gitlab: string;
  reddit: string;
}

/**
 * EN: Define interface `WebArenaTask`.
 * JP: インターフェース `WebArenaTask` を定義する。
 */
export interface WebArenaTask {
  task_id: number;
  intent: string;
  start_url?: string;
  sites?: string[];
  require_login?: boolean;
}

/**
 * EN: Define interface `WebArenaTasksResponse`.
 * JP: インターフェース `WebArenaTasksResponse` を定義する。
 */
export interface WebArenaTasksResponse {
  tasks: WebArenaTask[];
  total?: number;
  page?: number;
  per_page?: number;
}

/**
 * EN: Define interface `WebArenaStep`.
 * JP: インターフェース `WebArenaStep` を定義する。
 */
export interface WebArenaStep {
  step: number;
  content: string;
}

/**
 * EN: Define type alias `WebArenaTaskId`.
 * JP: 型エイリアス `WebArenaTaskId` を定義する。
 */
export type WebArenaTaskId = number | 'custom';

/**
 * EN: Define interface `WebArenaRunResult`.
 * JP: インターフェース `WebArenaRunResult` を定義する。
 */
export interface WebArenaRunResult {
  task_id: WebArenaTaskId;
  success: boolean;
  summary: string;
  steps: WebArenaStep[];
  evaluation: string;
}

/**
 * EN: Define interface `AggregateMetrics`.
 * JP: インターフェース `AggregateMetrics` を定義する。
 */
export interface AggregateMetrics {
  success_rate: number;
  success_rate_ci_95: { lower: number; upper: number };
  template_macro_sr: number;
  average_steps_success_only: number;
  average_steps_overall_with_failures_as_max: number;
  median_steps_success_only: number;
  p90_steps_success_only: number;
  max_steps: number;
}

/**
 * EN: Define interface `WebArenaBatchResult`.
 * JP: インターフェース `WebArenaBatchResult` を定義する。
 */
export interface WebArenaBatchResult {
  total_tasks: number;
  success_count: number;
  score: number;
  aggregate_metrics: AggregateMetrics;
  results: WebArenaRunResult[];
}
