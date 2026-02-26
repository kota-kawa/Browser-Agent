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
/**
 * EN: Import required modules.
 * JP: 必要なモジュールをインポートする。
 */
import { createRoot } from 'react-dom/client';
/**
 * EN: Import required modules.
 * JP: 必要なモジュールをインポートする。
 */
import { marked } from 'marked';
/**
 * EN: Import required modules.
 * JP: 必要なモジュールをインポートする。
 */
import DOMPurify from 'dompurify';
/**
 * EN: Import required modules.
 * JP: 必要なモジュールをインポートする。
 */
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
/**
 * EN: Import required modules.
 * JP: 必要なモジュールをインポートする。
 */
import type { IndexAppProps } from './types/app';
/**
 * EN: Import required modules.
 * JP: 必要なモジュールをインポートする。
 */
import { getJson, post, postJson } from './lib/api';

// JP: UIの表示タイミングや文言の定数
// EN: UI timing and copy constants
const MIN_THINKING_MS = 600;
const DEFAULT_BUSY_TITLE = 'AIが考えています';
const DEFAULT_BUSY_SUB = '見つけた情報から回答を組み立て中';
const FALLBACK_STEP_DETAIL = '次の操作を進行中です';
const USER_PROFILE_MAX_LENGTH = 2000;

const initialData: Partial<IndexAppProps> = window.__INDEX_APP_PROPS__ || {};
/**
 * EN: Declare variable `browserUrl`.
 * JP: 変数 `browserUrl` を宣言する。
 */
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
  /**
   * EN: Branch logic based on a condition.
   * JP: 条件に応じて処理を分岐する。
   */
  if (!lines.length) {
    /**
     * EN: Return a value from this scope.
     * JP: このスコープから値を返す。
     */
    return null;
  }
  /**
   * EN: Declare variable `match`.
   * JP: 変数 `match` を宣言する。
   */
  const match = lines[0].match(/^ステップ(\d+)/);
  /**
   * EN: Branch logic based on a condition.
   * JP: 条件に応じて処理を分岐する。
   */
  if (!match) {
    /**
     * EN: Return a value from this scope.
     * JP: このスコープから値を返す。
     */
    return null;
  }
  /**
   * EN: Declare variable `stepNumber`.
   * JP: 変数 `stepNumber` を宣言する。
   */
  const stepNumber = Number(match[1]);
  /**
   * EN: Declare variable `currentStatus`.
   * JP: 変数 `currentStatus` を宣言する。
   */
  const currentStatus = lines.find((line) => line.startsWith('現在の状況:'));
  /**
   * EN: Declare variable `nextGoal`.
   * JP: 変数 `nextGoal` を宣言する。
   */
  const nextGoal = lines.find((line) => line.startsWith('次の目標:'));
  /**
   * EN: Declare variable `actionLine`.
   * JP: 変数 `actionLine` を宣言する。
   */
  const actionLine = lines.find((line) => line.startsWith('アクション:'));
  /**
   * EN: Declare variable `evaluationLine`.
   * JP: 変数 `evaluationLine` を宣言する。
   */
  const evaluationLine = lines.find((line) => line.startsWith('評価:'));
  /**
   * EN: Declare variable `detail`.
   * JP: 変数 `detail` を宣言する。
   */
  let detail = '';
  /**
   * EN: Branch logic based on a condition.
   * JP: 条件に応じて処理を分岐する。
   */
  if (currentStatus) {
    detail = currentStatus.replace('現在の状況:', '').trim();
  } else if (nextGoal) {
    detail = `次の目標: ${nextGoal.replace('次の目標:', '').trim()}`;
  } else if (actionLine) {
    detail = `操作: ${actionLine.replace('アクション:', '').trim()}`;
  } else if (evaluationLine) {
    detail = `評価: ${evaluationLine.replace('評価:', '').trim()}`;
  }
  /**
   * EN: Return a value from this scope.
   * JP: このスコープから値を返す。
   */
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
  /**
   * EN: Return a value from this scope.
   * JP: このスコープから値を返す。
   */
  return content.includes('ステップでエージェントが実行されました');
};

/**
 * EN: Declare callable constant `findLastStepInfo`.
 * JP: 呼び出し可能な定数 `findLastStepInfo` を宣言する。
 */
const findLastStepInfo = (messages: ChatMessage[]) => {
  /**
   * EN: Iterate with a loop.
   * JP: ループで処理を繰り返す。
   */
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    /**
     * EN: Declare variable `message`.
     * JP: 変数 `message` を宣言する。
     */
    const message = messages[index];
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (!message || message.role !== 'assistant') {
      continue;
    }
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (isRunSummaryMessage(message.content)) {
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return null;
    }
    /**
     * EN: Declare variable `stepInfo`.
     * JP: 変数 `stepInfo` を宣言する。
     */
    const stepInfo = extractStepInfo(message.content);
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (stepInfo) {
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return stepInfo;
    }
  }
  /**
   * EN: Return a value from this scope.
   * JP: このスコープから値を返す。
   */
  return null;
};

/**
 * EN: Declare callable constant `countAssistantMessages`.
 * JP: 呼び出し可能な定数 `countAssistantMessages` を宣言する。
 */
const countAssistantMessages = (messages: ChatMessage[]) => {
  /**
   * EN: Declare variable `count`.
   * JP: 変数 `count` を宣言する。
   */
  let count = 0;
  messages.forEach((message) => {
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (message && message.role === 'assistant') {
      count += 1;
    }
  });
  /**
   * EN: Return a value from this scope.
   * JP: このスコープから値を返す。
   */
  return count;
};

/**
 * EN: Declare callable constant `buildConversationState`.
 * JP: 呼び出し可能な定数 `buildConversationState` を宣言する。
 */
const buildConversationState = (
  messages: ChatMessage[],
  prevState: ConversationState
): ConversationState => {
  /**
   * EN: Declare variable `count`.
   * JP: 変数 `count` を宣言する。
   */
  const count = countAssistantMessages(messages);
  /**
   * EN: Declare variable `pendingCleared`.
   * JP: 変数 `pendingCleared` を宣言する。
   */
  const pendingCleared =
    prevState.pendingAssistantResponse && count > prevState.assistantMessageCountAtSubmit;
  /**
   * EN: Return a value from this scope.
   * JP: このスコープから値を返す。
   */
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
      /**
       * EN: Declare variable `nextMessages`.
       * JP: 変数 `nextMessages` を宣言する。
       */
      const nextMessages = [...state.messages];
      /**
       * EN: Declare variable `existingIndex`.
       * JP: 変数 `existingIndex` を宣言する。
       */
      const existingIndex = nextMessages.findIndex((item) => item.id === action.message.id);
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (existingIndex >= 0) {
        nextMessages[existingIndex] = action.message;
      } else {
        nextMessages.push(action.message);
      }
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return buildConversationState(nextMessages, state);
    }
    case 'mark_pending':
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return {
        ...state,
        pendingAssistantResponse: true,
        assistantMessageCountAtSubmit: state.assistantMessageCount,
      };
    case 'clear_pending':
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return {
        ...state,
        pendingAssistantResponse: false,
      };
    case 'reset':
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return {
        messages: [],
        assistantMessageCount: 0,
        assistantMessageCountAtSubmit: 0,
        pendingAssistantResponse: false,
      };
    default:
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return state;
  }
};

/**
 * EN: Declare callable constant `encodeModelSelection`.
 * JP: 呼び出し可能な定数 `encodeModelSelection` を宣言する。
 */
const encodeModelSelection = (selection: ModelSelection | ModelOption | null | undefined) => {
  /**
   * EN: Branch logic based on a condition.
   * JP: 条件に応じて処理を分岐する。
   */
  if (!selection || !selection.provider || !selection.model) {
    /**
     * EN: Return a value from this scope.
     * JP: このスコープから値を返す。
     */
    return null;
  }
  /**
   * EN: Return a value from this scope.
   * JP: このスコープから値を返す。
   */
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
    /**
     * EN: Return a value from this scope.
     * JP: このスコープから値を返す。
     */
    return DOMPurify.sanitize(parsed, { USE_PROFILES: { html: true } });
  }, [text]);

  /**
   * EN: Return a value from this scope.
   * JP: このスコープから値を返す。
   */
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

  /**
   * EN: Return a value from this scope.
   * JP: このスコープから値を返す。
   */
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
  /**
   * EN: Declare variable `latestRunStateRef`.
   * JP: 変数 `latestRunStateRef` を宣言する。
   */
  const latestRunStateRef = useLatest({
    isRunning,
    isPaused,
    pendingAssistantResponse,
  });
  /**
   * EN: Declare variable `latestConversationRef`.
   * JP: 変数 `latestConversationRef` を宣言する。
   */
  const latestConversationRef = useLatest(conversation);

  /**
   * EN: Declare variable `messagesRef`.
   * JP: 変数 `messagesRef` を宣言する。
   */
  const messagesRef = useRef<HTMLDivElement | null>(null);
  /**
   * EN: Declare variable `formRef`.
   * JP: 変数 `formRef` を宣言する。
   */
  const formRef = useRef<HTMLFormElement | null>(null);
  /**
   * EN: Declare variable `promptInputRef`.
   * JP: 変数 `promptInputRef` を宣言する。
   */
  const promptInputRef = useRef<HTMLTextAreaElement | null>(null);
  /**
   * EN: Declare variable `eventSourceRef`.
   * JP: 変数 `eventSourceRef` を宣言する。
   */
  const eventSourceRef = useRef<EventSource | null>(null);
  /**
   * EN: Declare variable `reconnectTimerRef`.
   * JP: 変数 `reconnectTimerRef` を宣言する。
   */
  const reconnectTimerRef = useRef<number | null>(null);
  /**
   * EN: Declare variable `thinkingHideTimerRef`.
   * JP: 変数 `thinkingHideTimerRef` を宣言する。
   */
  const thinkingHideTimerRef = useRef<number | null>(null);
  /**
   * EN: Declare variable `thinkingShownAtRef`.
   * JP: 変数 `thinkingShownAtRef` を宣言する。
   */
  const thinkingShownAtRef = useRef(0);
  /**
   * EN: Declare variable `thinkingTimestampRef`.
   * JP: 変数 `thinkingTimestampRef` を宣言する。
   */
  const thinkingTimestampRef = useRef<number | null>(null);
  /**
   * EN: Declare variable `shouldBusyRef`.
   * JP: 変数 `shouldBusyRef` を宣言する。
   */
  const shouldBusyRef = useRef(false);
  /**
   * EN: Declare variable `prevBusyRef`.
   * JP: 変数 `prevBusyRef` を宣言する。
   */
  const prevBusyRef = useRef(false);
  /**
   * EN: Declare variable `scrollPendingRef`.
   * JP: 変数 `scrollPendingRef` を宣言する。
   */
  const scrollPendingRef = useRef(false);
  /**
   * EN: Declare variable `statusClearTimerRef`.
   * JP: 変数 `statusClearTimerRef` を宣言する。
   */
  const statusClearTimerRef = useRef<number | null>(null);
  /**
   * EN: Declare variable `userProfileTouchedRef`.
   * JP: 変数 `userProfileTouchedRef` を宣言する。
   */
  const userProfileTouchedRef = useRef(false);
  const [status, setStatusState] = useState<{ message: string; variant: StatusVariant }>({
    message: '',
    variant: 'muted',
  });

  /**
   * EN: Declare variable `clearStepActivity`.
   * JP: 変数 `clearStepActivity` を宣言する。
   */
  const clearStepActivity = useCallback(() => {
    setStepInProgress(false);
    setCurrentStepNumber(null);
    setCurrentStepDetail('');
  }, []);

  /**
   * EN: Declare variable `updateStepActivity`.
   * JP: 変数 `updateStepActivity` を宣言する。
   */
  const updateStepActivity = useCallback((stepInfo: StepInfo | null) => {
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (!stepInfo) {
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return;
    }
    setStepInProgress(true);
    setCurrentStepNumber(stepInfo.stepNumber);
    setCurrentStepDetail(stepInfo.detail || '');
    requestScrollToBottom();
  }, []);

  /**
   * EN: Declare variable `setStatus`.
   * JP: 変数 `setStatus` を宣言する。
   */
  const setStatus = useCallback((message?: string, variant: StatusVariant = 'info') => {
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (statusClearTimerRef.current) {
      clearTimeout(statusClearTimerRef.current);
      statusClearTimerRef.current = null;
    }
    /**
     * EN: Declare variable `nextMessage`.
     * JP: 変数 `nextMessage` を宣言する。
     */
    const nextMessage = message || '';
    setStatusState({ message: nextMessage, variant });
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (nextMessage && (variant === 'info' || variant === 'success')) {
      statusClearTimerRef.current = window.setTimeout(() => {
        setStatusState({ message: '', variant: 'muted' });
        statusClearTimerRef.current = null;
      }, 5000);
    }
  }, []);

  /**
   * EN: Declare variable `requestScrollToBottom`.
   * JP: 変数 `requestScrollToBottom` を宣言する。
   */
  const requestScrollToBottom = useCallback(() => {
    scrollPendingRef.current = true;
  }, []);

  /**
   * EN: Declare variable `updateConversationState`.
   * JP: 変数 `updateConversationState` を宣言する。
   */
  const updateConversationState = useCallback(
    (nextMessages: ChatMessage[], { syncStep }: { syncStep?: boolean } = { syncStep: false }) => {
      dispatchConversation({ type: 'set_messages', messages: nextMessages });
      /**
       * EN: Declare variable `runtime`.
       * JP: 変数 `runtime` を宣言する。
       */
      const runtime = latestRunStateRef.current;
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (syncStep) {
        /**
         * EN: Declare variable `lastStepInfo`.
         * JP: 変数 `lastStepInfo` を宣言する。
         */
        const lastStepInfo = findLastStepInfo(nextMessages);
        /**
         * EN: Branch logic based on a condition.
         * JP: 条件に応じて処理を分岐する。
         */
        if (lastStepInfo && (runtime.isRunning || runtime.pendingAssistantResponse)) {
          updateStepActivity(lastStepInfo);
        } else if (!runtime.isRunning && !runtime.pendingAssistantResponse) {
          clearStepActivity();
        }
      }
    },
    [clearStepActivity, dispatchConversation, latestRunStateRef, updateStepActivity]
  );

  /**
   * EN: Declare variable `appendOrUpdateMessage`.
   * JP: 変数 `appendOrUpdateMessage` を宣言する。
   */
  const appendOrUpdateMessage = useCallback(
    (message: ChatMessage) => {
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (!message || typeof message.id === 'undefined') {
        /**
         * EN: Return a value from this scope.
         * JP: このスコープから値を返す。
         */
        return;
      }
      /**
       * EN: Declare variable `existingIndex`.
       * JP: 変数 `existingIndex` を宣言する。
       */
      const existingIndex = latestConversationRef.current.findIndex(
        (item) => item.id === message.id
      );
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (existingIndex < 0) {
        requestScrollToBottom();
      }
      dispatchConversation({ type: 'upsert_message', message });

      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (message.role === 'assistant') {
        /**
         * EN: Declare variable `stepInfo`.
         * JP: 変数 `stepInfo` を宣言する。
         */
        const stepInfo = extractStepInfo(message.content);
        /**
         * EN: Branch logic based on a condition.
         * JP: 条件に応じて処理を分岐する。
         */
        if (stepInfo) {
          updateStepActivity(stepInfo);
        } else if (isRunSummaryMessage(message.content)) {
          clearStepActivity();
        }
      }
    },
    [clearStepActivity, dispatchConversation, latestConversationRef, requestScrollToBottom, updateStepActivity]
  );

  /**
   * EN: Declare variable `loadHistory`.
   * JP: 変数 `loadHistory` を宣言する。
   */
  const loadHistory = useCallback(async () => {
    /**
     * EN: Wrap logic with exception handling.
     * JP: 例外処理のためにブロックを囲む。
     */
    try {
      const { data } = await getJson<{ messages?: ChatMessage[] }>('/api/history', {
        errorMessage: '履歴の取得に失敗しました。',
        preferErrorBody: false,
      });
      updateConversationState(data.messages || [], { syncStep: true });
      requestScrollToBottom();
      setStatus('', 'muted');
    } catch (error) {
      /**
       * EN: Declare variable `err`.
       * JP: 変数 `err` を宣言する。
       */
      const err = error as { message?: string };
      setStatus(err.message, 'error');
    }
  }, [requestScrollToBottom, setStatus, updateConversationState]);

  /**
   * EN: Declare variable `handleResetEvent`.
   * JP: 変数 `handleResetEvent` を宣言する。
   */
  const handleResetEvent = useCallback(() => {
    dispatchConversation({ type: 'reset' });
    setStatus('履歴をリセットしました。', 'success');
    clearStepActivity();
    setIsRunning(false);
    setIsPaused(false);
    setConnectionState('connected');
    loadHistory();
  }, [clearStepActivity, dispatchConversation, loadHistory, setStatus]);

  /**
   * EN: Declare variable `loadModels`.
   * JP: 変数 `loadModels` を宣言する。
   */
  const loadModels = useCallback(
    async (preferredSelection?: ModelSelection | null) => {
      /**
       * EN: Wrap logic with exception handling.
       * JP: 例外処理のためにブロックを囲む。
       */
      try {
        const { data } = await getJson<
          ModelsResponse | ModelOption[] | { models?: ModelOption[]; current?: ModelSelection }
        >('/api/models', {
          errorMessage: 'モデルの取得に失敗しました。',
          preferErrorBody: false,
        });
        /**
         * EN: Declare variable `dataPayload`.
         * JP: 変数 `dataPayload` を宣言する。
         */
        const dataPayload = data as
          | ModelsResponse
          | ModelOption[]
          | { models?: ModelOption[]; current?: ModelSelection };
        /**
         * EN: Declare variable `models`.
         * JP: 変数 `models` を宣言する。
         */
        const models = Array.isArray(dataPayload)
          ? dataPayload
          : Array.isArray((dataPayload as { models?: ModelOption[] }).models)
            ? ((dataPayload as { models?: ModelOption[] }).models ?? [])
            : [];
        /**
         * EN: Declare variable `currentCandidate`.
         * JP: 変数 `currentCandidate` を宣言する。
         */
        const currentCandidate =
          !Array.isArray(dataPayload) &&
          typeof (dataPayload as { current?: unknown }).current === 'object'
            ? ((dataPayload as { current?: ModelSelection }).current ?? null)
            : null;
        /**
         * EN: Declare variable `current`.
         * JP: 変数 `current` を宣言する。
         */
        const current = currentCandidate || null;
        /**
         * EN: Declare variable `preferred`.
         * JP: 変数 `preferred` を宣言する。
         */
        const preferred = encodeModelSelection(preferredSelection);

        setModelOptions(models);
        /**
         * EN: Declare variable `desired`.
         * JP: 変数 `desired` を宣言する。
         */
        const desired = preferred || encodeModelSelection(current);
        /**
         * EN: Declare variable `hasDesired`.
         * JP: 変数 `hasDesired` を宣言する。
         */
        const hasDesired = desired && models.some((model) => encodeModelSelection(model) === desired);

        /**
         * EN: Branch logic based on a condition.
         * JP: 条件に応じて処理を分岐する。
         */
        if (hasDesired) {
          setSelectedModelValue(desired);
        } else if (models.length) {
          setSelectedModelValue(encodeModelSelection(models[0]) || '');
        }
      } catch (error) {
        /**
         * EN: Declare variable `err`.
         * JP: 変数 `err` を宣言する。
         */
        const err = error as { message?: string };
        setStatus(err.message, 'error');
      }
    },
    [setStatus]
  );

  /**
   * EN: Declare variable `loadUserProfile`.
   * JP: 変数 `loadUserProfile` を宣言する。
   */
  const loadUserProfile = useCallback(async () => {
    /**
     * EN: Wrap logic with exception handling.
     * JP: 例外処理のためにブロックを囲む。
     */
    try {
      const { data } = await getJson<UserProfileResponse>('/api/user_profile', {
        throwOnNonOk: false,
        preferErrorBody: false,
      });
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (!userProfileTouchedRef.current) {
        setUserProfile(data?.text || '');
        setUserProfileDirty(false);
      }
    } catch (error) {
      /**
       * EN: Declare variable `err`.
       * JP: 変数 `err` を宣言する。
       */
      const err = error as { message?: string };
      setStatus(err.message || 'ユーザー個人データの取得に失敗しました。', 'error');
    }
  }, [setStatus]);

  /**
   * EN: Declare variable `handleUserProfileSave`.
   * JP: 変数 `handleUserProfileSave` を宣言する。
   */
  const handleUserProfileSave = useCallback(async () => {
    setUserProfileSaving(true);
    /**
     * EN: Wrap logic with exception handling.
     * JP: 例外処理のためにブロックを囲む。
     */
    try {
      const { data } = await postJson<UserProfileResponse, { text: string }>('/api/user_profile', {
        text: userProfile,
      });
      setUserProfile(data?.text || '');
      setUserProfileDirty(false);
      setStatus('ユーザー個人データを保存しました。次のタスクから反映されます。', 'success');
    } catch (error) {
      /**
       * EN: Declare variable `err`.
       * JP: 変数 `err` を宣言する。
       */
      const err = error as { message?: string };
      setStatus(err.message || 'ユーザー個人データの保存に失敗しました。', 'error');
    } finally {
      setUserProfileSaving(false);
    }
  }, [setStatus, userProfile]);

  /**
   * EN: Declare variable `refreshVisionState`.
   * JP: 変数 `refreshVisionState` を宣言する。
   */
  const refreshVisionState = useCallback(async () => {
    /**
     * EN: Wrap logic with exception handling.
     * JP: 例外処理のためにブロックを囲む。
     */
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

  /**
   * EN: Declare variable `applyModelSelection`.
   * JP: 変数 `applyModelSelection` を宣言する。
   */
  const applyModelSelection = useCallback(
    async (selection: ModelSelection) => {
      /**
       * EN: Wrap logic with exception handling.
       * JP: 例外処理のためにブロックを囲む。
       */
      try {
        await postJson<{ error?: string }, ModelSelection>('/model_settings', selection, {
          errorMessage: 'モデル設定の適用に失敗しました。',
        });
        setStatus(`モデルを ${selection.label || selection.model} に変更しました。`, 'success');
      } catch (error) {
        /**
         * EN: Declare variable `err`.
         * JP: 変数 `err` を宣言する。
         */
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

    /**
     * EN: Declare variable `eventSource`.
     * JP: 変数 `eventSource` を宣言する。
     */
    const eventSource = new EventSource('/api/stream');
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setConnectionState('connected');
      setStatus('リアルタイム更新と同期しました。', 'success');
    };

    eventSource.onmessage = (event) => {
      /**
       * EN: Wrap logic with exception handling.
       * JP: 例外処理のためにブロックを囲む。
       */
      try {
        /**
         * EN: Declare variable `payload`.
         * JP: 変数 `payload` を宣言する。
         */
        const payload = JSON.parse(event.data) as SSEEvent;
        /**
         * EN: Branch logic based on a condition.
         * JP: 条件に応じて処理を分岐する。
         */
        if (payload.type === 'message' && payload.payload) {
          appendOrUpdateMessage(payload.payload);
        } else if (payload.type === 'update' && payload.payload) {
          appendOrUpdateMessage(payload.payload);
        } else if (payload.type === 'reset') {
          handleResetEvent();
        } else if (payload.type === 'model' && payload.payload) {
          loadModels(payload.payload);
          /**
           * EN: Declare variable `updatedLabel`.
           * JP: 変数 `updatedLabel` を宣言する。
           */
          const updatedLabel = payload.payload.label || payload.payload.model;
          /**
           * EN: Branch logic based on a condition.
           * JP: 条件に応じて処理を分岐する。
           */
          if (updatedLabel) {
            setStatus(`モデル設定が更新されました: ${updatedLabel}`, 'info');
          } else {
            setStatus('モデル設定が更新されました。', 'info');
          }
          refreshVisionState();
        } else if (payload.type === 'status' && payload.payload) {
          /**
           * EN: Declare variable `statusPayload`.
           * JP: 変数 `statusPayload` を宣言する。
           */
          const statusPayload = payload.payload || {};
          setIsRunning(false);
          setIsPaused(false);
          /**
           * EN: Branch logic based on a condition.
           * JP: 条件に応じて処理を分岐する。
           */
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

  // JP: 初期ロード時に履歴・設定・SSEを同期
  // EN: Sync history/config/SSE on initial load
  useEffect(() => {
    setupEventStream();
    loadHistory();
    loadModels();
    loadUserProfile();
    refreshVisionState();

    /**
     * EN: Return a value from this scope.
     * JP: このスコープから値を返す。
     */
    return () => {
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (thinkingHideTimerRef.current) {
        clearTimeout(thinkingHideTimerRef.current);
        thinkingHideTimerRef.current = null;
      }
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (statusClearTimerRef.current) {
        clearTimeout(statusClearTimerRef.current);
        statusClearTimerRef.current = null;
      }
    };
  }, [loadHistory, loadModels, loadUserProfile, refreshVisionState, setupEventStream]);

  /**
   * EN: Declare variable `shouldBusy`.
   * JP: 変数 `shouldBusy` を宣言する。
   */
  const shouldBusy = pendingAssistantResponse || stepInProgress;

  useEffect(() => {
    shouldBusyRef.current = shouldBusy;
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (thinkingHideTimerRef.current) {
      clearTimeout(thinkingHideTimerRef.current);
      thinkingHideTimerRef.current = null;
    }

    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (shouldBusy) {
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (!prevBusyRef.current) {
        thinkingShownAtRef.current = Date.now();
        thinkingTimestampRef.current = Date.now();
      }
      setThinkingVisible(true);
      requestScrollToBottom();
      prevBusyRef.current = true;
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return;
    }

    /**
     * EN: Declare variable `elapsed`.
     * JP: 変数 `elapsed` を宣言する。
     */
    const elapsed = Date.now() - (thinkingShownAtRef.current || Date.now());
    /**
     * EN: Declare variable `remaining`.
     * JP: 変数 `remaining` を宣言する。
     */
    const remaining = Math.max(0, MIN_THINKING_MS - elapsed);

    /**
     * EN: Declare callable constant `finalize`.
     * JP: 呼び出し可能な定数 `finalize` を宣言する。
     */
    const finalize = () => {
      setThinkingVisible(false);
      thinkingShownAtRef.current = 0;
      thinkingTimestampRef.current = null;
    };

    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (remaining > 0) {
      thinkingHideTimerRef.current = window.setTimeout(() => {
        thinkingHideTimerRef.current = null;
        /**
         * EN: Branch logic based on a condition.
         * JP: 条件に応じて処理を分岐する。
         */
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
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (!shouldBusy) {
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return;
    }
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (stepInProgress && currentStepNumber) {
      /**
       * EN: Declare variable `detail`.
       * JP: 変数 `detail` を宣言する。
       */
      const detail = currentStepDetail || FALLBACK_STEP_DETAIL;
      setBusyMessageTitle(`ステップ${currentStepNumber}を実行しています`);
      setBusyMessageSub(detail);
    } else {
      setBusyMessageTitle(DEFAULT_BUSY_TITLE);
      setBusyMessageSub(DEFAULT_BUSY_SUB);
    }
  }, [currentStepDetail, currentStepNumber, shouldBusy, stepInProgress]);

  useLayoutEffect(() => {
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (!scrollPendingRef.current) {
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return;
    }
    scrollPendingRef.current = false;
    /**
     * EN: Declare variable `element`.
     * JP: 変数 `element` を宣言する。
     */
    const element = messagesRef.current;
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
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

    /**
     * EN: Declare variable `submittedPromptValue`.
     * JP: 変数 `submittedPromptValue` を宣言する。
     */
    const submittedPromptValue = rawPrompt;
    setIsSending(true);
    setStatus('新しいタスクとしてエージェントに指示を送信しています…', 'progress');
    setIsRunning(true);
    setIsPaused(false);
    clearStepActivity();
    dispatchConversation({ type: 'mark_pending' });

    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (promptInputRef.current) {
      promptInputRef.current.value = '';
      promptInputRef.current.focus();
    }

    /**
     * EN: Declare variable `shouldContinueRunning`.
     * JP: 変数 `shouldContinueRunning` を宣言する。
     */
    let shouldContinueRunning = false;

    /**
     * EN: Wrap logic with exception handling.
     * JP: 例外処理のためにブロックを囲む。
     */
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

      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (Array.isArray(data.messages)) {
        updateConversationState(data.messages, { syncStep: true });
        requestScrollToBottom();
      }

      /**
       * EN: Declare variable `agentStillRunning`.
       * JP: 変数 `agentStillRunning` を宣言する。
       */
      const agentStillRunning = response.status === 202 || data.agent_running === true;
      shouldContinueRunning = Boolean(agentStillRunning);
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (agentStillRunning) {
        /**
         * EN: Declare variable `runSummary`.
         * JP: 変数 `runSummary` を宣言する。
         */
        const runSummary = data.run_summary || 'エージェントが実行を継続しています。';
        setStatus(runSummary, 'progress');
      } else {
        setStatus('', 'muted');
      }
    } catch (error) {
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (promptInputRef.current && !promptInputRef.current.value.trim()) {
        promptInputRef.current.value = submittedPromptValue;
        /**
         * EN: Branch logic based on a condition.
         * JP: 条件に応じて処理を分岐する。
         */
        if (typeof promptInputRef.current.setSelectionRange === 'function') {
          /**
           * EN: Declare variable `length`.
           * JP: 変数 `length` を宣言する。
           */
          const length = promptInputRef.current.value.length;
          promptInputRef.current.setSelectionRange(length, length);
        }
        promptInputRef.current.focus();
      }
      /**
       * EN: Declare variable `err`.
       * JP: 変数 `err` を宣言する。
       */
      const err = error as { message?: string };
      setStatus(err.message || 'エージェントへの送信に失敗しました。', 'error');
      dispatchConversation({ type: 'clear_pending' });
      clearStepActivity();
      shouldContinueRunning = false;
    } finally {
      setIsSending(false);
      setIsRunning(shouldContinueRunning);
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
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
      /**
       * EN: Declare variable `nextPaused`.
       * JP: 変数 `nextPaused` を宣言する。
       */
      const nextPaused = !latestRunStateRef.current.isPaused;
      setIsPaused(nextPaused);
      setStatus(
        nextPaused ? 'エージェントを一時停止しました。' : 'エージェントを再開しました。',
        'info'
      );
    } catch (error) {
      /**
       * EN: Declare variable `err`.
       * JP: 変数 `err` を宣言する。
       */
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
    /**
     * EN: Wrap logic with exception handling.
     * JP: 例外処理のためにブロックを囲む。
     */
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
      /**
       * EN: Declare variable `err`.
       * JP: 変数 `err` を宣言する。
       */
      const err = error as { message?: string };
      setStatus(err.message || '履歴のリセットに失敗しました。', 'error');
    } finally {
      setIsResetting(false);
    }
  };

  /**
   * EN: Declare callable constant `handlePromptKeyDown`.
   * JP: 呼び出し可能な定数 `handlePromptKeyDown` を宣言する。
   */
  const handlePromptKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault();
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (formRef.current) {
        /**
         * EN: Branch logic based on a condition.
         * JP: 条件に応じて処理を分岐する。
         */
        if (typeof formRef.current.requestSubmit === 'function') {
          formRef.current.requestSubmit();
        } else {
          formRef.current.submit();
        }
      }
    }
  };

  /**
   * EN: Declare callable constant `handleModelChange`.
   * JP: 呼び出し可能な定数 `handleModelChange` を宣言する。
   */
  const handleModelChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    /**
     * EN: Declare variable `value`.
     * JP: 変数 `value` を宣言する。
     */
    const value = event.target.value;
    setSelectedModelValue(value);
    /**
     * EN: Wrap logic with exception handling.
     * JP: 例外処理のためにブロックを囲む。
     */
    try {
      /**
       * EN: Declare variable `selection`.
       * JP: 変数 `selection` を宣言する。
       */
      const selection = JSON.parse(value) as ModelSelection;
      /**
       * EN: Declare variable `selected`.
       * JP: 変数 `selected` を宣言する。
       */
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

  /**
   * EN: Declare variable `selectedModelProvider`.
   * JP: 変数 `selectedModelProvider` を宣言する。
   */
  const selectedModelProvider = useMemo(() => {
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (!selectedModelValue) {
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return '';
    }
    /**
     * EN: Wrap logic with exception handling.
     * JP: 例外処理のためにブロックを囲む。
     */
    try {
      /**
       * EN: Declare variable `parsed`.
       * JP: 変数 `parsed` を宣言する。
       */
      const parsed = JSON.parse(selectedModelValue) as ModelSelection;
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return (parsed.provider || '').toLowerCase();
    } catch (error) {
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return '';
    }
  }, [selectedModelValue]);
  /**
   * EN: Declare variable `showVisionToggle`.
   * JP: 変数 `showVisionToggle` を宣言する。
   */
  const showVisionToggle = ['openai', 'claude', 'gemini'].includes(selectedModelProvider);
  /**
   * EN: Declare variable `visionBadgeText`.
   * JP: 変数 `visionBadgeText` を宣言する。
   */
  const visionBadgeText = visionState.loading
    ? 'CHECKING'
    : visionState.supported
      ? 'SUPPORTED'
      : 'UNSUPPORTED';
  /**
   * EN: Declare variable `visionBadgeClass`.
   * JP: 変数 `visionBadgeClass` を宣言する。
   */
  const visionBadgeClass = `vision-badge${
    visionState.loading ? ' is-pending' : visionState.supported ? ' is-ok' : ' is-off'
  }`;
  /**
   * EN: Declare variable `visionHint`.
   * JP: 変数 `visionHint` を宣言する。
   */
  let visionHint = 'モデルがサポートしていればスクリーンショットを送信します。';
  /**
   * EN: Branch logic based on a condition.
   * JP: 条件に応じて処理を分岐する。
   */
  if (visionState.error) {
    visionHint = visionState.error;
  } else if (!visionState.loading) {
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (!visionState.supported) {
      visionHint = '選択中のモデルはスクリーンショット非対応です。';
    } else if (visionState.effective) {
      visionHint = 'スクリーンショットをモデルに送信しています。';
    } else {
      visionHint = 'スクリーンショット送信を停止中です。';
    }
  }

  /**
   * EN: Declare variable `shouldDisablePause`.
   * JP: 変数 `shouldDisablePause` を宣言する。
   */
  const shouldDisablePause = !isRunning || isPausing;
  /**
   * EN: Declare variable `shouldDisableUserProfileSave`.
   * JP: 変数 `shouldDisableUserProfileSave` を宣言する。
   */
  const shouldDisableUserProfileSave = userProfileSaving || !userProfileDirty;
  /**
   * EN: Declare variable `pauseLabel`.
   * JP: 変数 `pauseLabel` を宣言する。
   */
  const pauseLabel = !isRunning ? '一時停止' : isPaused ? '再開' : '一時停止';
  /**
   * EN: Declare variable `messagesEmpty`.
   * JP: 変数 `messagesEmpty` を宣言する。
   */
  const messagesEmpty = conversation.length === 0 && !thinkingVisible;

  /**
   * EN: Declare variable `messagesClassName`.
   * JP: 変数 `messagesClassName` を宣言する。
   */
  const messagesClassName = `messages${messagesEmpty ? ' is-empty' : ''}`;
  /**
   * EN: Declare variable `statusClassName`.
   * JP: 変数 `statusClassName` を宣言する。
   */
  const statusClassName = `status-banner${status.message ? '' : ' is-empty'}`;

  useEffect(() => {
    /**
     * EN: Declare variable `browserIframe`.
     * JP: 変数 `browserIframe` を宣言する。
     */
    const browserIframe = document.querySelector<HTMLIFrameElement>('.browser-pane iframe');
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (!browserIframe) {
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return undefined;
    }
    /**
     * EN: Declare variable `shell`.
     * JP: 変数 `shell` を宣言する。
     */
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
