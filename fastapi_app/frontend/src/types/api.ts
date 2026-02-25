// JP: フロントエンドで使うAPIレスポンス型
// EN: API response types used by the frontend
export type ChatRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: number;
  role: ChatRole;
  content: string;
  timestamp: string;
}

export interface ModelOption {
  provider: string;
  model: string;
  label?: string;
  base_url?: string;
}

export interface ModelSelection {
  provider: string;
  model: string;
  base_url?: string;
  label?: string;
}

export interface ModelsResponse {
  models: ModelOption[];
  current: ModelSelection;
}

export interface VisionState {
  user_enabled: boolean;
  model_supported: boolean;
  effective: boolean;
  provider: string;
  model: string;
}

export interface UserProfileResponse {
  text: string;
}

export interface StatusPayload {
  agent_running?: boolean;
  run_summary?: string;
}

export type SSEEvent =
  | { type: 'message'; payload: ChatMessage }
  | { type: 'update'; payload: ChatMessage }
  | { type: 'reset' }
  | { type: 'status'; payload: StatusPayload }
  | { type: 'model'; payload: ModelOption };

export interface ChatResponse {
  messages?: ChatMessage[];
  run_summary?: string;
  queued?: boolean;
  agent_running?: boolean;
  error?: string;
}

export interface ResetResponse {
  messages?: ChatMessage[];
  error?: string;
}

export interface PauseResumeResponse {
  status?: 'paused' | 'resumed';
  error?: string;
}

export interface EnvUrls {
  shopping: string;
  shopping_admin: string;
  gitlab: string;
  reddit: string;
}

export interface WebArenaTask {
  task_id: number;
  intent: string;
  start_url?: string;
  sites?: string[];
  require_login?: boolean;
}

export interface WebArenaTasksResponse {
  tasks: WebArenaTask[];
  total?: number;
  page?: number;
  per_page?: number;
}

export interface WebArenaStep {
  step: number;
  content: string;
}

export type WebArenaTaskId = number | 'custom';

export interface WebArenaRunResult {
  task_id: WebArenaTaskId;
  success: boolean;
  summary: string;
  steps: WebArenaStep[];
  evaluation: string;
}

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

export interface WebArenaBatchResult {
  total_tasks: number;
  success_count: number;
  score: number;
  aggregate_metrics: AggregateMetrics;
  results: WebArenaRunResult[];
}
