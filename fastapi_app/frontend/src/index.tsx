// JP: メインチャットUIのエントリポイント
// EN: Entry point for the main chat UI
import React, {
  useState,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useCallback,
  useReducer,
} from 'react';
import { createRoot } from 'react-dom/client';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import type {
  ChatMessage,
  ChatResponse,
  ModelOption,
  ModelSelection,
  ModelsResponse,
  PauseResumeResponse,
  ResetResponse,
  SSEEvent,
  UserProfileResponse,
  VisionState,
} from './types/api';
import type { IndexAppProps } from './types/app';
import { getJson, post, postJson } from './lib/api';

// JP: UIの表示タイミングや文言の定数
// EN: UI timing and copy constants
const MIN_THINKING_MS = 600;
const DEFAULT_BUSY_TITLE = 'AIが考えています';
const DEFAULT_BUSY_SUB = '見つけた情報から回答を組み立て中';
const FALLBACK_STEP_DETAIL = '次の操作を進行中です';
const USER_PROFILE_MAX_LENGTH = 2000;

const initialData: Partial<IndexAppProps> = window.__INDEX_APP_PROPS__ || {};
const browserUrl = initialData.browserUrl || '';

// JP: 接続状態と表示種別の型定義
// EN: Types for connection state and status variants
type ConnectionState = 'idle' | 'connecting' | 'connected' | 'disconnected';
type StatusVariant = 'muted' | 'info' | 'success' | 'warning' | 'error' | 'progress';

type StepInfo = {
  stepNumber: number;
  detail: string;
};

/**
 * EN: Define type alias `VisionStateView`.
 * JP: 型エイリアス `VisionStateView` を定義する。
 */
type VisionStateView = {
  supported: boolean | null;
  effective: boolean;
  userEnabled: boolean;
  loading: boolean;
  error: string;
};

/**
 * EN: Define type alias `ConversationState`.
 * JP: 型エイリアス `ConversationState` を定義する。
 */
type ConversationState = {
  messages: ChatMessage[];
  assistantMessageCount: number;
  assistantMessageCountAtSubmit: number;
  pendingAssistantResponse: boolean;
};

/**
 * EN: Define type alias `ConversationAction`.
 * JP: 型エイリアス `ConversationAction` を定義する。
 */
type ConversationAction =
  | { type: 'set_messages'; messages: ChatMessage[] }
  | { type: 'upsert_message'; message: ChatMessage }
  | { type: 'mark_pending' }
  | { type: 'clear_pending' }
  | { type: 'reset' };

// JP: 最新値を参照するための簡易フック
// EN: Small hook to keep a ref to the latest value
const useLatest = <T,>(value: T) => {
  const ref = useRef(value);
  ref.current = value;
  return ref;
};

// JP: 「考え中」表示用のタイムスタンプ整形
// EN: Format timestamp for the thinking indicator
const formatThinkingTimestamp = (timestamp: number | string) => {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return '';
  }
  return date
    .toLocaleString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
    .replace(/\//g, '/');
};

// JP: メッセージ時刻をUI向けに整形
// EN: Format message timestamp for UI
const formatMessageTimestamp = (timestamp: string) => {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return { text: '', iso: '' };
  }
  return {
    iso: date.toISOString(),
    text: date.toLocaleString('ja-JP', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
  };
};

// JP: ナビゲーションがリロード起点かどうかを判定
// EN: Detect whether the current page load was caused by a reload
const isReloadNavigation = () => {
  const entries =
    typeof window.performance?.getEntriesByType === 'function'
      ? window.performance.getEntriesByType('navigation')
      : [];
  const entry = entries[0] as { type?: unknown } | undefined;
  if (entry && typeof entry.type === 'string') {
    return entry.type === 'reload';
  }

  // NOTE: Legacy fallback for browsers without Navigation Timing Level 2
  const legacyType = window.performance?.navigation?.type;
  return legacyType === 1;
};

// JP: ステップログから進行中情報を抽出
// EN: Extract step info from step-log messages
const extractStepInfo = (content: string | null | undefined): StepInfo | null => {
  if (!content || typeof content !== 'string') {
    return null;
  }
  const lines = content
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
  if (!lines.length) {
    return null;
  }
  const match = lines[0].match(/^ステップ(\d+)/);
  if (!match) {
    return null;
  }
  const stepNumber = Number(match[1]);
  const currentStatus = lines.find((line) => line.startsWith('現在の状況:'));
  const nextGoal = lines.find((line) => line.startsWith('次の目標:'));
  const actionLine = lines.find((line) => line.startsWith('アクション:'));
  const evaluationLine = lines.find((line) => line.startsWith('評価:'));
  let detail = '';
  if (currentStatus) {
    detail = currentStatus.replace('現在の状況:', '').trim();
  } else if (nextGoal) {
    detail = `次の目標: ${nextGoal.replace('次の目標:', '').trim()}`;
  } else if (actionLine) {
    detail = `操作: ${actionLine.replace('アクション:', '').trim()}`;
  } else if (evaluationLine) {
    detail = `評価: ${evaluationLine.replace('評価:', '').trim()}`;
  }
  return { stepNumber, detail };
};

// JP: 実行サマリメッセージかどうか判定
// EN: Detect run summary messages
const isRunSummaryMessage = (content: string | null | undefined) => {
  if (!content || typeof content !== 'string') {
    return false;
  }
  if (!/^[✅⚠️ℹ️]/.test(content)) {
    return false;
  }
  return content.includes('ステップでエージェントが実行されました');
};

/**
 * EN: Define function `findLastStepInfo`.
 * JP: 関数 `findLastStepInfo` を定義する。
 */
const findLastStepInfo = (messages: ChatMessage[]) => {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    if (!message || message.role !== 'assistant') {
      continue;
    }
    if (isRunSummaryMessage(message.content)) {
      return null;
    }
    const stepInfo = extractStepInfo(message.content);
    if (stepInfo) {
      return stepInfo;
    }
  }
  return null;
};

/**
 * EN: Define function `countAssistantMessages`.
 * JP: 関数 `countAssistantMessages` を定義する。
 */
const countAssistantMessages = (messages: ChatMessage[]) => {
  let count = 0;
  messages.forEach((message) => {
    if (message && message.role === 'assistant') {
      count += 1;
    }
  });
  return count;
};

const buildConversationState = (
  messages: ChatMessage[],
  prevState: ConversationState
): ConversationState => {
  const count = countAssistantMessages(messages);
  const pendingCleared =
    prevState.pendingAssistantResponse && count > prevState.assistantMessageCountAtSubmit;
  return {
    ...prevState,
    messages,
    assistantMessageCount: count,
    pendingAssistantResponse: pendingCleared ? false : prevState.pendingAssistantResponse,
  };
};

// JP: 会話履歴の更新を集中管理する reducer
// EN: Reducer that manages conversation updates
const conversationReducer = (
  state: ConversationState,
  action: ConversationAction
): ConversationState => {
  switch (action.type) {
    case 'set_messages':
      return buildConversationState(action.messages, state);
    case 'upsert_message': {
      const nextMessages = [...state.messages];
      const existingIndex = nextMessages.findIndex((item) => item.id === action.message.id);
      if (existingIndex >= 0) {
        nextMessages[existingIndex] = action.message;
      } else {
        nextMessages.push(action.message);
      }
      return buildConversationState(nextMessages, state);
    }
    case 'mark_pending':
      return {
        ...state,
        pendingAssistantResponse: true,
        assistantMessageCountAtSubmit: state.assistantMessageCount,
      };
    case 'clear_pending':
      return {
        ...state,
        pendingAssistantResponse: false,
      };
    case 'reset':
      return {
        messages: [],
        assistantMessageCount: 0,
        assistantMessageCountAtSubmit: 0,
        pendingAssistantResponse: false,
      };
    default:
      return state;
  }
};

/**
 * EN: Define function `encodeModelSelection`.
 * JP: 関数 `encodeModelSelection` を定義する。
 */
const encodeModelSelection = (selection: ModelSelection | ModelOption | null | undefined) => {
  if (!selection || !selection.provider || !selection.model) {
    return null;
  }
  return JSON.stringify({ provider: selection.provider, model: selection.model });
};

/**
 * EN: Define type alias `MessageBubbleProps`.
 * JP: 型エイリアス `MessageBubbleProps` を定義する。
 */
type MessageBubbleProps = {
  content?: string | null;
};

// JP: Markdown をサニタイズして表示するバブル
// EN: Bubble that renders sanitized Markdown
const MessageBubble = ({ content }: MessageBubbleProps) => {
  const text = typeof content === 'string' ? content : '';
  const htmlContent = useMemo(() => {
    const parsed = marked.parse(text, {
      breaks: true,
      gfm: true,
    });
    return DOMPurify.sanitize(parsed, { USE_PROFILES: { html: true } });
  }, [text]);

  return <div className="bubble" dangerouslySetInnerHTML={{ __html: htmlContent }} />;
};

/**
 * EN: Define type alias `MessageItemProps`.
 * JP: 型エイリアス `MessageItemProps` を定義する。
 */
type MessageItemProps = {
  message: ChatMessage;
};

// JP: 1件のチャットメッセージ表示
// EN: Single chat message item
const MessageItem = ({ message }: MessageItemProps) => {
  const formatted = useMemo(
    () => formatMessageTimestamp(message.timestamp),
    [message.timestamp]
  );

  return (
    <article className={`message ${message.role}`} data-id={message.id}>
      <header className="message__header">
        <div className="message__title">
          <span className="message__avatar" aria-hidden="true">
            {message.role === 'assistant' ? '🤖' : '🧑'}
          </span>
          <span className="message__badge">
            {message.role === 'assistant' ? 'LLM' : 'ユーザー'}
          </span>
        </div>
        <time className="message__timestamp" dateTime={formatted.iso || undefined}>
          {formatted.text}
        </time>
      </header>
      <div className="message__body">
        <MessageBubble content={message.content} />
      </div>
    </article>
  );
};

/**
 * EN: Define type alias `ThinkingMessageProps`.
 * JP: 型エイリアス `ThinkingMessageProps` を定義する。
 */
type ThinkingMessageProps = {
  title: string;
  sub: string;
  timestamp: number;
};

// JP: 進行中表示（Thinking）
// EN: Thinking indicator component
const ThinkingMessage = ({ title, sub, timestamp }: ThinkingMessageProps) => {
  return (
    <div className="msg system compact assistant pending thinking" id="thinking-message">
      <div className="thinking-header">
        <span className="thinking-agent-icon" aria-hidden="true"></span>
        <span className="thinking-labels">
          <span className="thinking-title">{title}</span>
          <span className="thinking-sub">{sub}</span>
        </span>
      </div>
      <span className="msg-time">{formatThinkingTimestamp(timestamp)}</span>
    </div>
  );
};

/**
 * EN: Define type alias `ConnectionIndicatorProps`.
 * JP: 型エイリアス `ConnectionIndicatorProps` を定義する。
 */
type ConnectionIndicatorProps = {
  state: ConnectionState;
};

// JP: SSE接続状態の表示
// EN: Connection state indicator for SSE
const ConnectionIndicator = ({ state }: ConnectionIndicatorProps) => {
  let message = '接続を待機しています';
  if (state === 'connected') {
    message = 'リアルタイム更新中';
  } else if (state === 'connecting') {
    message = '接続中…';
  } else if (state === 'disconnected') {
    message = '再接続を試行中';
  }

  return (
    <div
      id="connection-indicator"
      className="connection-indicator"
      role="status"
      aria-live="polite"
      data-state={state}
    >
      <span className="dot" aria-hidden="true"></span>
      <span className="text">{message}</span>
    </div>
  );
};

// JP: メインUIコンポーネント
// EN: Main UI component
const App = () => {
  const [conversationState, dispatchConversation] = useReducer(conversationReducer, {
    messages: [],
    assistantMessageCount: 0,
    assistantMessageCountAtSubmit: 0,
    pendingAssistantResponse: false,
  });
  const { messages: conversation, pendingAssistantResponse } = conversationState;
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isPausing, setIsPausing] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>('idle');
  const [modelOptions, setModelOptions] = useState<ModelOption[]>([]);
  const [selectedModelValue, setSelectedModelValue] = useState('');
  const [userProfile, setUserProfile] = useState('');
  const [userProfileDirty, setUserProfileDirty] = useState(false);
  const [userProfileSaving, setUserProfileSaving] = useState(false);
  const [visionState, setVisionState] = useState<VisionStateView>({
    supported: null,
    effective: false,
    userEnabled: true,
    loading: true,
    error: '',
  });
  const [visionBusy, setVisionBusy] = useState(false);
  const [stepInProgress, setStepInProgress] = useState(false);
  const [currentStepNumber, setCurrentStepNumber] = useState<number | null>(null);
  const [currentStepDetail, setCurrentStepDetail] = useState('');
  const [thinkingVisible, setThinkingVisible] = useState(false);
  const [busyMessageTitle, setBusyMessageTitle] = useState(DEFAULT_BUSY_TITLE);
  const [busyMessageSub, setBusyMessageSub] = useState(DEFAULT_BUSY_SUB);
  const latestRunStateRef = useLatest({
    isRunning,
    isPaused,
    pendingAssistantResponse,
  });
  const latestConversationRef = useLatest(conversation);

  const messagesRef = useRef<HTMLDivElement | null>(null);
  const formRef = useRef<HTMLFormElement | null>(null);
  const promptInputRef = useRef<HTMLTextAreaElement | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const thinkingHideTimerRef = useRef<number | null>(null);
  const thinkingShownAtRef = useRef(0);
  const thinkingTimestampRef = useRef<number | null>(null);
  const shouldBusyRef = useRef(false);
  const prevBusyRef = useRef(false);
  const scrollPendingRef = useRef(false);
  const statusClearTimerRef = useRef<number | null>(null);
  const userProfileTouchedRef = useRef(false);
  const [status, setStatusState] = useState<{ message: string; variant: StatusVariant }>({
    message: '',
    variant: 'muted',
  });

  const clearStepActivity = useCallback(() => {
    setStepInProgress(false);
    setCurrentStepNumber(null);
    setCurrentStepDetail('');
  }, []);

  const updateStepActivity = useCallback((stepInfo: StepInfo | null) => {
    if (!stepInfo) {
      return;
    }
    setStepInProgress(true);
    setCurrentStepNumber(stepInfo.stepNumber);
    setCurrentStepDetail(stepInfo.detail || '');
    requestScrollToBottom();
  }, []);

  const setStatus = useCallback((message?: string, variant: StatusVariant = 'info') => {
    if (statusClearTimerRef.current) {
      clearTimeout(statusClearTimerRef.current);
      statusClearTimerRef.current = null;
    }
    const nextMessage = message || '';
    setStatusState({ message: nextMessage, variant });
    if (nextMessage && (variant === 'info' || variant === 'success')) {
      statusClearTimerRef.current = window.setTimeout(() => {
        setStatusState({ message: '', variant: 'muted' });
        statusClearTimerRef.current = null;
      }, 5000);
    }
  }, []);

  const requestScrollToBottom = useCallback(() => {
    scrollPendingRef.current = true;
  }, []);

  const updateConversationState = useCallback(
    (nextMessages: ChatMessage[], { syncStep }: { syncStep?: boolean } = { syncStep: false }) => {
      dispatchConversation({ type: 'set_messages', messages: nextMessages });
      const runtime = latestRunStateRef.current;
      if (syncStep) {
        const lastStepInfo = findLastStepInfo(nextMessages);
        if (lastStepInfo && (runtime.isRunning || runtime.pendingAssistantResponse)) {
          updateStepActivity(lastStepInfo);
        } else if (!runtime.isRunning && !runtime.pendingAssistantResponse) {
          clearStepActivity();
        }
      }
    },
    [clearStepActivity, dispatchConversation, latestRunStateRef, updateStepActivity]
  );

  const appendOrUpdateMessage = useCallback(
    (message: ChatMessage) => {
      if (!message || typeof message.id === 'undefined') {
        return;
      }
      const existingIndex = latestConversationRef.current.findIndex(
        (item) => item.id === message.id
      );
      if (existingIndex < 0) {
        requestScrollToBottom();
      }
      dispatchConversation({ type: 'upsert_message', message });

      if (message.role === 'assistant') {
        const stepInfo = extractStepInfo(message.content);
        if (stepInfo) {
          updateStepActivity(stepInfo);
        } else if (isRunSummaryMessage(message.content)) {
          clearStepActivity();
        }
      }
    },
    [clearStepActivity, dispatchConversation, latestConversationRef, requestScrollToBottom, updateStepActivity]
  );

  const loadHistory = useCallback(async () => {
    try {
      const { data } = await getJson<{ messages?: ChatMessage[] }>('/api/history', {
        errorMessage: '履歴の取得に失敗しました。',
        preferErrorBody: false,
      });
      updateConversationState(data.messages || [], { syncStep: true });
      requestScrollToBottom();
      setStatus('', 'muted');
    } catch (error) {
      const err = error as { message?: string };
      setStatus(err.message, 'error');
    }
  }, [requestScrollToBottom, setStatus, updateConversationState]);

  const resetForReload = useCallback(async () => {
    try {
      const { data } = await post<ResetResponse>('/api/reset', {
        fallback: {},
        errorMessage: 'リロード時の初期化に失敗しました。',
        throwOnParseError: false,
      });
      updateConversationState(data.messages || [], { syncStep: true });
      requestScrollToBottom();
      clearStepActivity();
      setIsRunning(false);
      setIsPaused(false);
      setStatus('ページ再読み込みにより、履歴とブラウザ状態を初期化しました。', 'info');
      return true;
    } catch (error) {
      const err = error as { message?: string };
      setStatus(err.message || 'リロード時の初期化に失敗しました。', 'error');
      return false;
    }
  }, [clearStepActivity, requestScrollToBottom, setStatus, updateConversationState]);

  const handleResetEvent = useCallback(() => {
    dispatchConversation({ type: 'reset' });
    setStatus('履歴をリセットしました。', 'success');
    clearStepActivity();
    setIsRunning(false);
    setIsPaused(false);
    setConnectionState('connected');
    loadHistory();
  }, [clearStepActivity, dispatchConversation, loadHistory, setStatus]);

  const loadModels = useCallback(
    async (preferredSelection?: ModelSelection | null) => {
      try {
        const { data } = await getJson<
          ModelsResponse | ModelOption[] | { models?: ModelOption[]; current?: ModelSelection }
        >('/api/models', {
          errorMessage: 'モデルの取得に失敗しました。',
          preferErrorBody: false,
        });
        const dataPayload = data as
          | ModelsResponse
          | ModelOption[]
          | { models?: ModelOption[]; current?: ModelSelection };
        const models = Array.isArray(dataPayload)
          ? dataPayload
          : Array.isArray((dataPayload as { models?: ModelOption[] }).models)
            ? ((dataPayload as { models?: ModelOption[] }).models ?? [])
            : [];
        const currentCandidate =
          !Array.isArray(dataPayload) &&
          typeof (dataPayload as { current?: unknown }).current === 'object'
            ? ((dataPayload as { current?: ModelSelection }).current ?? null)
            : null;
        const current = currentCandidate || null;
        const preferred = encodeModelSelection(preferredSelection);

        setModelOptions(models);
        const desired = preferred || encodeModelSelection(current);
        const hasDesired = desired && models.some((model) => encodeModelSelection(model) === desired);

        if (hasDesired) {
          setSelectedModelValue(desired);
        } else if (models.length) {
          setSelectedModelValue(encodeModelSelection(models[0]) || '');
        }
      } catch (error) {
        const err = error as { message?: string };
        setStatus(err.message, 'error');
      }
    },
    [setStatus]
  );

  const loadUserProfile = useCallback(async () => {
    try {
      const { data } = await getJson<UserProfileResponse>('/api/user_profile', {
        throwOnNonOk: false,
        preferErrorBody: false,
      });
      if (!userProfileTouchedRef.current) {
        setUserProfile(data?.text || '');
        setUserProfileDirty(false);
      }
    } catch (error) {
      const err = error as { message?: string };
      setStatus(err.message || 'ユーザー個人データの取得に失敗しました。', 'error');
    }
  }, [setStatus]);

  const handleUserProfileSave = useCallback(async () => {
    setUserProfileSaving(true);
    try {
      const { data } = await postJson<UserProfileResponse, { text: string }>('/api/user_profile', {
        text: userProfile,
      });
      setUserProfile(data?.text || '');
      setUserProfileDirty(false);
      setStatus('ユーザー個人データを保存しました。次のタスクから反映されます。', 'success');
    } catch (error) {
      const err = error as { message?: string };
      setStatus(err.message || 'ユーザー個人データの保存に失敗しました。', 'error');
    } finally {
      setUserProfileSaving(false);
    }
  }, [setStatus, userProfile]);

  const refreshVisionState = useCallback(async () => {
    try {
      const { data } = await getJson<VisionState>('/api/vision', {
        throwOnNonOk: false,
      });
      setVisionState({
        supported: !!data.model_supported,
        effective: !!data.effective,
        userEnabled: !!data.user_enabled,
        loading: false,
        error: '',
      });
    } catch (error) {
      console.error('Failed to load vision state', error);
      setVisionState((prev) => ({
        ...prev,
        loading: false,
        error: 'スクリーンショット状態の取得に失敗しました。',
      }));
    }
  }, []);

  const applyModelSelection = useCallback(
    async (selection: ModelSelection) => {
      try {
        await postJson<{ error?: string }, ModelSelection>('/model_settings', selection, {
          errorMessage: 'モデル設定の適用に失敗しました。',
        });
        setStatus(`モデルを ${selection.label || selection.model} に変更しました。`, 'success');
      } catch (error) {
        const err = error as { message?: string };
        setStatus(err.message, 'error');
      } finally {
        refreshVisionState();
      }
    },
    [refreshVisionState, setStatus]
  );

  // JP: SSEでリアルタイム更新を受け取る
  // EN: Set up SSE stream for real-time updates
  const setupEventStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    setConnectionState('connecting');
    setStatus('リアルタイムストリームに接続しています…', 'progress');

    const eventSource = new EventSource('/api/stream');
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setConnectionState('connected');
      setStatus('リアルタイム更新と同期しました。', 'success');
    };

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as SSEEvent;
        if (payload.type === 'message' && payload.payload) {
          appendOrUpdateMessage(payload.payload);
        } else if (payload.type === 'update' && payload.payload) {
          appendOrUpdateMessage(payload.payload);
        } else if (payload.type === 'reset') {
          handleResetEvent();
        } else if (payload.type === 'model' && payload.payload) {
          loadModels(payload.payload);
          const updatedLabel = payload.payload.label || payload.payload.model;
          if (updatedLabel) {
            setStatus(`モデル設定が更新されました: ${updatedLabel}`, 'info');
          } else {
            setStatus('モデル設定が更新されました。', 'info');
          }
          refreshVisionState();
        } else if (payload.type === 'status' && payload.payload) {
          const statusPayload = payload.payload || {};
          setIsRunning(false);
          setIsPaused(false);
          if (statusPayload.run_summary) {
            // Suppress the top completion banner for finished tasks.
          }
          dispatchConversation({ type: 'clear_pending' });
          clearStepActivity();
        }
      } catch (error) {
        console.error('ストリームの処理に失敗しました', error);
      }
    };

    eventSource.onerror = () => {
      setConnectionState('disconnected');
      setStatus('ストリーム接続が切断されました。再接続を試みています…', 'warning');
      eventSource.close();
      reconnectTimerRef.current = window.setTimeout(setupEventStream, 2000);
    };
  }, [appendOrUpdateMessage, clearStepActivity, handleResetEvent, loadModels, refreshVisionState, setStatus]);

  // JP: 初期ロード時に必要ならリロード初期化を実行し、その後に履歴・設定・SSEを同期
  // EN: Optionally reset on reload, then sync history/config/SSE on initial load
  useEffect(() => {
    let disposed = false;

    const initialize = async () => {
      if (isReloadNavigation()) {
        const resetSucceeded = await resetForReload();
        if (!resetSucceeded) {
          await loadHistory();
        }
      } else {
        await loadHistory();
      }

      if (disposed) {
        return;
      }

      setupEventStream();
      loadModels();
      loadUserProfile();
      refreshVisionState();
    };

    initialize();

    return () => {
      disposed = true;
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (thinkingHideTimerRef.current) {
        clearTimeout(thinkingHideTimerRef.current);
        thinkingHideTimerRef.current = null;
      }
      if (statusClearTimerRef.current) {
        clearTimeout(statusClearTimerRef.current);
        statusClearTimerRef.current = null;
      }
    };
  }, [loadHistory, loadModels, loadUserProfile, refreshVisionState, resetForReload, setupEventStream]);

  const shouldBusy = pendingAssistantResponse || stepInProgress;

  useEffect(() => {
    shouldBusyRef.current = shouldBusy;
    if (thinkingHideTimerRef.current) {
      clearTimeout(thinkingHideTimerRef.current);
      thinkingHideTimerRef.current = null;
    }

    if (shouldBusy) {
      if (!prevBusyRef.current) {
        thinkingShownAtRef.current = Date.now();
        thinkingTimestampRef.current = Date.now();
      }
      setThinkingVisible(true);
      requestScrollToBottom();
      prevBusyRef.current = true;
      return;
    }

    const elapsed = Date.now() - (thinkingShownAtRef.current || Date.now());
    const remaining = Math.max(0, MIN_THINKING_MS - elapsed);

    /**
     * EN: Define function `finalize`.
     * JP: 関数 `finalize` を定義する。
     */
    const finalize = () => {
      setThinkingVisible(false);
      thinkingShownAtRef.current = 0;
      thinkingTimestampRef.current = null;
    };

    if (remaining > 0) {
      thinkingHideTimerRef.current = window.setTimeout(() => {
        thinkingHideTimerRef.current = null;
        if (!shouldBusyRef.current) {
          finalize();
        }
      }, remaining);
    } else {
      finalize();
    }
    prevBusyRef.current = false;
  }, [requestScrollToBottom, shouldBusy]);

  useEffect(() => {
    if (!shouldBusy) {
      return;
    }
    if (stepInProgress && currentStepNumber) {
      const detail = currentStepDetail || FALLBACK_STEP_DETAIL;
      setBusyMessageTitle(`ステップ${currentStepNumber}を実行しています`);
      setBusyMessageSub(detail);
    } else {
      setBusyMessageTitle(DEFAULT_BUSY_TITLE);
      setBusyMessageSub(DEFAULT_BUSY_SUB);
    }
  }, [currentStepDetail, currentStepNumber, shouldBusy, stepInProgress]);

  useLayoutEffect(() => {
    if (!scrollPendingRef.current) {
      return;
    }
    scrollPendingRef.current = false;
    const element = messagesRef.current;
    if (element) {
      element.scrollTop = element.scrollHeight;
    }
  }, [conversation, thinkingVisible]);

  // JP: 新規タスクとしてプロンプトを送信
  // EN: Submit a new prompt as a fresh task
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const rawPrompt = promptInputRef.current ? promptInputRef.current.value : '';
    const prompt = rawPrompt.trim();
    if (!prompt) {
      setStatus('プロンプトを入力してください。', 'warning');
      return;
    }

    const submittedPromptValue = rawPrompt;
    setIsSending(true);
    setStatus('新しいタスクとしてエージェントに指示を送信しています…', 'progress');
    setIsRunning(true);
    setIsPaused(false);
    clearStepActivity();
    dispatchConversation({ type: 'mark_pending' });

    if (promptInputRef.current) {
      promptInputRef.current.value = '';
      promptInputRef.current.focus();
    }

    let shouldContinueRunning = false;

    try {
      const { data, response } = await postJson<ChatResponse, { prompt: string; new_task: true }>(
        '/api/chat',
        { prompt, new_task: true },
        {
          fallback: {},
          errorMessage: 'LLMへの送信に失敗しました。',
          throwOnParseError: false,
        }
      );

      if (Array.isArray(data.messages)) {
        updateConversationState(data.messages, { syncStep: true });
        requestScrollToBottom();
      }

      const agentStillRunning = response.status === 202 || data.agent_running === true;
      shouldContinueRunning = Boolean(agentStillRunning);
      if (agentStillRunning) {
        const runSummary = data.run_summary || 'エージェントが実行を継続しています。';
        setStatus(runSummary, 'progress');
      } else {
        setStatus('', 'muted');
      }
    } catch (error) {
      if (promptInputRef.current && !promptInputRef.current.value.trim()) {
        promptInputRef.current.value = submittedPromptValue;
        if (typeof promptInputRef.current.setSelectionRange === 'function') {
          const length = promptInputRef.current.value.length;
          promptInputRef.current.setSelectionRange(length, length);
        }
        promptInputRef.current.focus();
      }
      const err = error as { message?: string };
      setStatus(err.message || 'エージェントへの送信に失敗しました。', 'error');
      dispatchConversation({ type: 'clear_pending' });
      clearStepActivity();
      shouldContinueRunning = false;
    } finally {
      setIsSending(false);
      setIsRunning(shouldContinueRunning);
      if (!shouldContinueRunning) {
        setIsPaused(false);
      }
    }
  };

  // JP: 一時停止/再開のトグル
  // EN: Pause/resume toggle handler
  const handlePauseToggle = async () => {
    if (!isRunning || isPausing) {
      return;
    }
    setIsPausing(true);
    const endpoint = isPaused ? '/api/resume' : '/api/pause';
    try {
      await post<PauseResumeResponse>(endpoint, {
        fallback: {},
        errorMessage: isPaused ? '再開に失敗しました。' : '一時停止に失敗しました。',
        throwOnParseError: false,
      });
      const nextPaused = !latestRunStateRef.current.isPaused;
      setIsPaused(nextPaused);
      setStatus(
        nextPaused ? 'エージェントを一時停止しました。' : 'エージェントを再開しました。',
        'info'
      );
    } catch (error) {
      const err = error as { message?: string };
      setStatus(err.message || '操作に失敗しました。', 'error');
    } finally {
      setIsPausing(false);
    }
  };

  // JP: 会話履歴のリセット
  // EN: Reset conversation history
  const handleReset = async () => {
    if (isResetting) {
      return;
    }
    const confirmed = window.confirm('会話履歴をリセットしますか？');
    if (!confirmed) {
      return;
    }
    setIsResetting(true);
    try {
      const { data } = await post<ResetResponse>('/api/reset', {
        fallback: {},
        errorMessage: '履歴のリセットに失敗しました。',
        throwOnParseError: false,
      });
      updateConversationState(data.messages || [], { syncStep: true });
      requestScrollToBottom();
      setStatus('履歴をリセットしました。', 'success');
      setIsRunning(false);
      setIsPaused(false);
    } catch (error) {
      const err = error as { message?: string };
      setStatus(err.message || '履歴のリセットに失敗しました。', 'error');
    } finally {
      setIsResetting(false);
    }
  };

  /**
   * EN: Define function `handlePromptKeyDown`.
   * JP: 関数 `handlePromptKeyDown` を定義する。
   */
  const handlePromptKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault();
      if (formRef.current) {
        if (typeof formRef.current.requestSubmit === 'function') {
          formRef.current.requestSubmit();
        } else {
          formRef.current.submit();
        }
      }
    }
  };

  /**
   * EN: Define function `handleModelChange`.
   * JP: 関数 `handleModelChange` を定義する。
   */
  const handleModelChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    setSelectedModelValue(value);
    try {
      const selection = JSON.parse(value) as ModelSelection;
      const selected = modelOptions.find((model) => encodeModelSelection(model) === value);
      selection.label = selected ? selected.label : undefined;
      applyModelSelection(selection);
    } catch (error) {
      setStatus('モデル設定の解析に失敗しました。', 'error');
    }
  };

  // JP: Vision（スクリーンショット送信）設定の切替
  // EN: Toggle vision (screenshot) setting
  const handleVisionToggle = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const enabled = event.target.checked;
    setVisionBusy(true);
    try {
      await postJson('/api/vision', { enabled }, { parseJson: false, throwOnNonOk: false });
      setStatus(
        enabled ? 'スクリーンショット送信を有効にしました。' : 'スクリーンショット送信を停止しました。',
        'info'
      );
    } catch (error) {
      console.error('Failed to update vision toggle', error);
      setStatus('スクリーンショット設定の更新に失敗しました。', 'error');
    } finally {
      setVisionBusy(false);
      refreshVisionState();
    }
  };

  const selectedModelProvider = useMemo(() => {
    if (!selectedModelValue) {
      return '';
    }
    try {
      const parsed = JSON.parse(selectedModelValue) as ModelSelection;
      return (parsed.provider || '').toLowerCase();
    } catch (error) {
      return '';
    }
  }, [selectedModelValue]);
  const showVisionToggle = ['openai', 'claude', 'gemini'].includes(selectedModelProvider);
  const visionBadgeText = visionState.loading
    ? 'CHECKING'
    : visionState.supported
      ? 'SUPPORTED'
      : 'UNSUPPORTED';
  const visionBadgeClass = `vision-badge${
    visionState.loading ? ' is-pending' : visionState.supported ? ' is-ok' : ' is-off'
  }`;
  let visionHint = 'モデルがサポートしていればスクリーンショットを送信します。';
  if (visionState.error) {
    visionHint = visionState.error;
  } else if (!visionState.loading) {
    if (!visionState.supported) {
      visionHint = '選択中のモデルはスクリーンショット非対応です。';
    } else if (visionState.effective) {
      visionHint = 'スクリーンショットをモデルに送信しています。';
    } else {
      visionHint = 'スクリーンショット送信を停止中です。';
    }
  }

  const shouldDisablePause = !isRunning || isPausing;
  const shouldDisableUserProfileSave = userProfileSaving || !userProfileDirty;
  const pauseLabel = !isRunning ? '一時停止' : isPaused ? '再開' : '一時停止';
  const messagesEmpty = conversation.length === 0 && !thinkingVisible;

  const messagesClassName = `messages${messagesEmpty ? ' is-empty' : ''}`;
  const statusClassName = `status-banner${status.message ? '' : ' is-empty'}`;

  useEffect(() => {
    const browserIframe = document.querySelector<HTMLIFrameElement>('.browser-pane iframe');
    if (!browserIframe) {
      return undefined;
    }
    const shell = document.querySelector<HTMLDivElement>('.browser-shell');
    const toolbar = shell ? shell.querySelector<HTMLDivElement>('.browser-toolbar') : null;

    /**
     * EN: Define function `syncIframeHeight`.
     * JP: 関数 `syncIframeHeight` を定義する。
     */
    const syncIframeHeight = () => {
      if (!shell) {
        return;
      }
      const toolbarHeight = toolbar ? toolbar.offsetHeight : 0;
      const nextHeight = Math.max(shell.clientHeight - toolbarHeight, 0);
      browserIframe.style.height = `${nextHeight}px`;
    };

    let resizeObserver: ResizeObserver | null = null;
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
    <main className="layout">
      <section className="chat-pane" aria-label="チャット領域" aria-busy={shouldBusy}>
        <div className="chat-pane__content">
          <header className="chat-header">
            <div className="chat-header-main">
              <h1>チャット</h1>
            </div>
            <div className="chat-header-side">
              <details className="chat-header-details">
                <summary className="chat-header-summary">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="icon-settings"
                  >
                    <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                  設定
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="chevron-icon"
                  >
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                </summary>
                <div className="chat-header-controls">
                  <div className="model-selector-group">
                    <label htmlFor="model-selector" className="model-selector-label">
                      AIモデル
                    </label>
                    <div className="model-selector-wrapper">
                      <select
                        id="model-selector"
                        name="model"
                        value={modelOptions.length ? selectedModelValue : undefined}
                        onChange={handleModelChange}
                      >
                        {modelOptions.map((model) => (
                          <option
                            key={encodeModelSelection(model) || model.label}
                            value={encodeModelSelection(model) as string}
                          >
                            {model.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  {showVisionToggle && (
                    <div className="vision-toggle-group" aria-live="polite">
                      <div className="vision-toggle-header">
                        <span className="vision-toggle-title">スクリーンショット参照</span>
                        <span className={visionBadgeClass}>{visionBadgeText}</span>
                      </div>
                      <label className="vision-toggle">
                        <input
                          type="checkbox"
                          id="vision-toggle"
                          checked={visionState.userEnabled}
                          disabled={visionState.loading || !visionState.supported || visionBusy}
                          onChange={handleVisionToggle}
                        />
                        <span className="vision-toggle-slider" aria-hidden="true"></span>
                        <span className="vision-toggle-label">
                          {visionState.userEnabled ? 'ON' : 'OFF'}
                        </span>
                      </label>
                      <p className="vision-toggle-hint">{visionHint}</p>
                    </div>
                  )}
                  <div className="user-profile-group">
                    <div className="user-profile-header">
                      <label htmlFor="user-profile" className="user-profile-label">
                        ユーザー個人データ
                      </label>
                      <button
                        type="button"
                        className="user-profile-save"
                        onClick={handleUserProfileSave}
                        disabled={shouldDisableUserProfileSave}
                      >
                        {userProfileSaving ? '保存中…' : userProfileDirty ? '保存' : '保存済み'}
                      </button>
                    </div>
                    <textarea
                      id="user-profile"
                      className="user-profile-textarea"
                      rows={4}
                      maxLength={USER_PROFILE_MAX_LENGTH}
                      placeholder="例: 予算・好み・制約・検索で優先する条件など"
                      value={userProfile}
                      onChange={(event) => {
                        userProfileTouchedRef.current = true;
                        setUserProfile(event.target.value);
                        setUserProfileDirty(true);
                      }}
                    />
                    <p className="user-profile-hint">
                      ここに入力した内容はシステムプロンプトに挿入され、次のタスクから検索に反映されます。
                    </p>
                  </div>
                  <ConnectionIndicator state={connectionState} />
                  <div className="chat-controls" role="group" aria-label="チャット操作">
                    <button
                      type="button"
                      id="pause-button"
                      className="control-button control-button--primary"
                      disabled={shouldDisablePause}
                      onClick={handlePauseToggle}
                    >
                      {pauseLabel}
                    </button>
                    <button
                      type="button"
                      id="reset-button"
                      className="control-button control-button--ghost"
                      onClick={handleReset}
                      disabled={isResetting}
                    >
                      履歴リセット
                    </button>
                  </div>
                </div>
              </details>
            </div>
          </header>
          <div
            className={statusClassName}
            role="status"
            aria-live="polite"
            aria-atomic="true"
            data-variant={status.variant}
            aria-hidden={!status.message}
          >
            <span className="status-dot" aria-hidden="true"></span>
            <span className="status-text">{status.message}</span>
          </div>
          <div className="chat-body">
            <div
              id="messages"
              className={messagesClassName}
              aria-live="polite"
              aria-busy={shouldBusy}
              data-empty-text="まだメッセージはありません。入力して会話を始めましょう。"
              ref={messagesRef}
            >
              {conversation.map((message) => (
                <MessageItem key={message.id} message={message} />
              ))}
              {thinkingVisible && (
                <ThinkingMessage
                  title={busyMessageTitle}
                  sub={busyMessageSub}
                  timestamp={thinkingTimestampRef.current || Date.now()}
                />
              )}
            </div>
          </div>
        </div>
        <form
          id="prompt-form"
          className={`prompt-form${isSending ? ' is-sending' : ''}`}
          autoComplete="off"
          onSubmit={handleSubmit}
          ref={formRef}
        >
          <label htmlFor="prompt-input" className="sr-only">
            プロンプト
          </label>
          <div className="prompt-form__field">
            <textarea
              id="prompt-input"
              name="prompt"
              placeholder="ブラウザに指示したい内容を入力してください。"
              rows={3}
              required
              ref={promptInputRef}
              onKeyDown={handlePromptKeyDown}
            ></textarea>
            <button type="submit" className="submit-button" aria-label="送信">
              <span className="button-icon" aria-hidden="true">
                ⮕
              </span>
            </button>
          </div>
          <div className="prompt-footer">
            <span className="hint">Ctrl / ⌘ + Enterで送信</span>
          </div>
        </form>
      </section>
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
