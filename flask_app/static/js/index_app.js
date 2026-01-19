(() => {
  if (!window.React || !window.ReactDOM || !window.htm) {
    return;
  }

  const {
    useState,
    useEffect,
    useLayoutEffect,
    useMemo,
    useRef,
    useCallback,
  } = window.React;
  const html = window.htm.bind(window.React.createElement);

  const MIN_THINKING_MS = 600;
  const DEFAULT_BUSY_TITLE = 'AIが考えています';
  const DEFAULT_BUSY_SUB = '見つけた情報から回答を組み立て中';
  const FALLBACK_STEP_DETAIL = '次の操作を進行中です';

  const initialData = window.__INDEX_APP_PROPS__ || {};
  const browserUrl = initialData.browserUrl || '';

  const formatThinkingTimestamp = (timestamp) => {
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

  const formatMessageTimestamp = (timestamp) => {
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

  const extractStepInfo = (content) => {
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

  const isRunSummaryMessage = (content) => {
    if (!content || typeof content !== 'string') {
      return false;
    }
    if (!/^[✅⚠️ℹ️]/.test(content)) {
      return false;
    }
    return content.includes('ステップでエージェントが実行されました');
  };

  const findLastStepInfo = (messages) => {
    if (!Array.isArray(messages)) {
      return null;
    }
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

  const countAssistantMessages = (messages) => {
    let count = 0;
    messages.forEach((message) => {
      if (message && message.role === 'assistant') {
        count += 1;
      }
    });
    return count;
  };

  const encodeModelSelection = (selection) => {
    if (!selection || !selection.provider || !selection.model) {
      return null;
    }
    return JSON.stringify({ provider: selection.provider, model: selection.model });
  };

  const MessageBubble = ({ content }) => {
    const text = typeof content === 'string' ? content : '';
    const htmlContent = useMemo(() => {
      if (!window.marked) {
        return text;
      }
      const parsed = window.marked.parse(text, {
        breaks: true,
        gfm: true,
      });
      if (window.DOMPurify) {
        return window.DOMPurify.sanitize(parsed, { USE_PROFILES: { html: true } });
      }
      return parsed;
    }, [text]);

    if (window.marked) {
      return html`<div className="bubble" dangerouslySetInnerHTML=${{ __html: htmlContent }} />`;
    }
    return html`<div className="bubble">${htmlContent}</div>`;
  };

  const MessageItem = ({ message }) => {
    const formatted = useMemo(
      () => formatMessageTimestamp(message.timestamp),
      [message.timestamp],
    );

    return html`
      <article className=${`message ${message.role}`} data-id=${message.id}>
        <header className="message__header">
          <div className="message__title">
            <span className="message__avatar" aria-hidden="true">
              ${message.role === 'assistant' ? '🤖' : '🧑'}
            </span>
            <span className="message__badge">
              ${message.role === 'assistant' ? 'LLM' : 'ユーザー'}
            </span>
          </div>
          <time
            className="message__timestamp"
            dateTime=${formatted.iso || undefined}
          >
            ${formatted.text}
          </time>
        </header>
        <div className="message__body">
          <${MessageBubble} content=${message.content} />
        </div>
      </article>
    `;
  };

  const ThinkingMessage = ({ title, sub, timestamp }) => {
    return html`
      <div className="msg system compact assistant pending thinking" id="thinking-message">
        <div className="thinking-header">
          <span className="thinking-orb" aria-hidden="true"></span>
          <span className="thinking-labels">
            <span className="thinking-title">${title}</span>
            <span className="thinking-sub">${sub}</span>
          </span>
        </div>
        <span className="msg-time">${formatThinkingTimestamp(timestamp)}</span>
      </div>
    `;
  };

  const ConnectionIndicator = ({ state }) => {
    let message = '接続を待機しています';
    if (state === 'connected') {
      message = 'リアルタイム更新中';
    } else if (state === 'connecting') {
      message = '接続中…';
    } else if (state === 'disconnected') {
      message = '再接続を試行中';
    }

    return html`
      <div
        id="connection-indicator"
        className="connection-indicator"
        role="status"
        aria-live="polite"
        data-state=${state}
      >
        <span className="dot" aria-hidden="true"></span>
        <span className="text">${message}</span>
      </div>
    `;
  };

  const App = () => {
    const [conversation, setConversation] = useState([]);
    const [assistantMessageCount, setAssistantMessageCount] = useState(0);
    const [assistantMessageCountAtSubmit, setAssistantMessageCountAtSubmit] = useState(0);
    const [pendingAssistantResponse, setPendingAssistantResponse] = useState(false);
    const [isRunning, setIsRunning] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [isPausing, setIsPausing] = useState(false);
    const [isResetting, setIsResetting] = useState(false);
    const [connectionState, setConnectionState] = useState('idle');
    const [modelOptions, setModelOptions] = useState([]);
    const [selectedModelValue, setSelectedModelValue] = useState('');
    const [stepInProgress, setStepInProgress] = useState(false);
    const [currentStepNumber, setCurrentStepNumber] = useState(null);
    const [currentStepDetail, setCurrentStepDetail] = useState('');
    const [thinkingVisible, setThinkingVisible] = useState(false);
    const [busyMessageTitle, setBusyMessageTitle] = useState(DEFAULT_BUSY_TITLE);
    const [busyMessageSub, setBusyMessageSub] = useState(DEFAULT_BUSY_SUB);

    const conversationRef = useRef([]);
    const assistantMessageCountRef = useRef(0);
    const assistantMessageCountAtSubmitRef = useRef(0);
    const pendingAssistantResponseRef = useRef(false);
    const isRunningRef = useRef(false);
    const isPausedRef = useRef(false);

    const messagesRef = useRef(null);
    const formRef = useRef(null);
    const promptInputRef = useRef(null);
    const pendingSubmitModeRef = useRef('continue');
    const eventSourceRef = useRef(null);
    const reconnectTimerRef = useRef(null);
    const thinkingHideTimerRef = useRef(null);
    const thinkingShownAtRef = useRef(0);
    const thinkingTimestampRef = useRef(null);
    const shouldBusyRef = useRef(false);
    const prevBusyRef = useRef(false);
    const scrollPendingRef = useRef(false);
    const statusClearTimerRef = useRef(null);
    const statusRef = useRef({ message: '', variant: 'muted' });

    const setAssistantMessageCountState = (value) => {
      assistantMessageCountRef.current = value;
      setAssistantMessageCount(value);
    };

    const setAssistantMessageCountAtSubmitState = (value) => {
      assistantMessageCountAtSubmitRef.current = value;
      setAssistantMessageCountAtSubmit(value);
    };

    const setPendingAssistantResponseState = (value) => {
      pendingAssistantResponseRef.current = value;
      setPendingAssistantResponse(value);
    };

    const setIsRunningState = (value) => {
      isRunningRef.current = value;
      setIsRunning(value);
    };

    const setIsPausedState = (value) => {
      isPausedRef.current = value;
      setIsPaused(value);
    };

    const clearStepActivity = useCallback(() => {
      setStepInProgress(false);
      setCurrentStepNumber(null);
      setCurrentStepDetail('');
    }, []);

    const updateStepActivity = useCallback((stepInfo) => {
      if (!stepInfo) {
        return;
      }
      setStepInProgress(true);
      setCurrentStepNumber(stepInfo.stepNumber);
      setCurrentStepDetail(stepInfo.detail || '');
      requestScrollToBottom();
    }, []);

    const setStatus = useCallback((message, variant = 'info') => {
      if (statusClearTimerRef.current) {
        clearTimeout(statusClearTimerRef.current);
        statusClearTimerRef.current = null;
      }
      statusRef.current = { message, variant };
      if (message && (variant === 'info' || variant === 'success')) {
        statusClearTimerRef.current = window.setTimeout(() => {
          statusRef.current = { message: '', variant: 'muted' };
          statusClearTimerRef.current = null;
        }, 5000);
      }
    }, []);

    const requestScrollToBottom = useCallback(() => {
      scrollPendingRef.current = true;
    }, []);

    const updateConversationState = useCallback(
      (nextMessages, { syncStep } = { syncStep: false }) => {
        conversationRef.current = nextMessages;
        setConversation(nextMessages);
        const count = countAssistantMessages(nextMessages);
        setAssistantMessageCountState(count);
        if (
          pendingAssistantResponseRef.current &&
          count > assistantMessageCountAtSubmitRef.current
        ) {
          setPendingAssistantResponseState(false);
        }
        if (syncStep) {
          const lastStepInfo = findLastStepInfo(nextMessages);
          if (lastStepInfo && (isRunningRef.current || pendingAssistantResponseRef.current)) {
            updateStepActivity(lastStepInfo);
          } else if (!isRunningRef.current && !pendingAssistantResponseRef.current) {
            clearStepActivity();
          }
        }
      },
      [clearStepActivity, updateStepActivity],
    );

    const appendOrUpdateMessage = useCallback(
      (message) => {
        if (!message || typeof message.id === 'undefined') {
          return;
        }
        const currentMessages = conversationRef.current;
        const nextMessages = [...currentMessages];
        const existingIndex = nextMessages.findIndex((item) => item.id === message.id);
        if (existingIndex >= 0) {
          nextMessages[existingIndex] = message;
        } else {
          nextMessages.push(message);
          requestScrollToBottom();
        }
        updateConversationState(nextMessages);

        if (message.role === 'assistant') {
          const stepInfo = extractStepInfo(message.content);
          if (stepInfo) {
            updateStepActivity(stepInfo);
          } else if (isRunSummaryMessage(message.content)) {
            clearStepActivity();
          }
        }
      },
      [clearStepActivity, requestScrollToBottom, updateConversationState, updateStepActivity],
    );

    const loadHistory = useCallback(async () => {
      try {
        const response = await fetch('/api/history');
        if (!response.ok) {
          throw new Error('履歴の取得に失敗しました。');
        }
        const data = await response.json();
        updateConversationState(data.messages || [], { syncStep: true });
        requestScrollToBottom();
        setStatus('', 'muted');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }, [requestScrollToBottom, setStatus, updateConversationState]);

    const handleResetEvent = useCallback(() => {
      updateConversationState([], { syncStep: false });
      setStatus('履歴をリセットしました。', 'success');
      setPendingAssistantResponseState(false);
      setAssistantMessageCountAtSubmitState(0);
      clearStepActivity();
      setIsRunningState(false);
      setIsPausedState(false);
      setConnectionState('connected');
      loadHistory();
    }, [clearStepActivity, loadHistory, setStatus, updateConversationState]);

    const loadModels = useCallback(
      async (preferredSelection) => {
        try {
          const response = await fetch('/api/models');
          if (!response.ok) {
            throw new Error('モデルの取得に失敗しました。');
          }
          const data = await response.json();
          const models = Array.isArray(data)
            ? data
            : Array.isArray(data.models)
              ? data.models
              : [];
          const current =
            !Array.isArray(data) && typeof data.current === 'object' ? data.current : null;
          const preferred = encodeModelSelection(preferredSelection);

          setModelOptions(models);
          const desired = preferred || encodeModelSelection(current);
          const hasDesired =
            desired &&
            models.some((model) => encodeModelSelection(model) === desired);

          if (hasDesired) {
            setSelectedModelValue(desired);
          } else if (models.length) {
            setSelectedModelValue(encodeModelSelection(models[0]) || '');
          }
        } catch (error) {
          setStatus(error.message, 'error');
        }
      },
      [setStatus],
    );

    const applyModelSelection = useCallback(async (selection) => {
      try {
        const response = await fetch('/model_settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(selection),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || 'モデル設定の適用に失敗しました。');
        }
        setStatus(`モデルを ${selection.label || selection.model} に変更しました。`, 'success');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }, [setStatus]);

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
          const payload = JSON.parse(event.data);
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
          } else if (payload.type === 'status' && payload.payload) {
            const statusPayload = payload.payload || {};
            setIsRunningState(false);
            setIsPausedState(false);
            if (statusPayload.run_summary) {
              // Suppress the top completion banner for finished tasks.
            }
            setPendingAssistantResponseState(false);
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
    }, [appendOrUpdateMessage, clearStepActivity, handleResetEvent, loadModels, setStatus]);

    useEffect(() => {
      setupEventStream();
      loadHistory();
      loadModels();

      return () => {
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
    }, [loadHistory, loadModels, setupEventStream]);

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

    const handleSubmit = async (event) => {
      event.preventDefault();
      const mode = pendingSubmitModeRef.current;
      pendingSubmitModeRef.current = 'continue';
      const isNewTaskSubmission = mode === 'new-task';
      const rawPrompt = promptInputRef.current ? promptInputRef.current.value : '';
      const prompt = rawPrompt.trim();
      if (!prompt) {
        setStatus('プロンプトを入力してください。', 'warning');
        return;
      }

      const submittedPromptValue = rawPrompt;
      setIsSending(true);
      setStatus(
        isNewTaskSubmission
          ? '新しいタスクとしてエージェントに指示を送信しています…'
          : 'エージェントに指示を送信しています…',
        'progress',
      );
      setIsRunningState(true);
      setIsPausedState(false);
      if (isNewTaskSubmission) {
        clearStepActivity();
      }
      setPendingAssistantResponseState(true);
      setAssistantMessageCountAtSubmitState(assistantMessageCountRef.current);

      if (promptInputRef.current) {
        promptInputRef.current.value = '';
        promptInputRef.current.focus();
      }

      let shouldContinueRunning = false;

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(
            isNewTaskSubmission ? { prompt, new_task: true } : { prompt },
          ),
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          const message = data.error || 'LLMへの送信に失敗しました。';
          throw new Error(message);
        }

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
        setStatus(error.message || 'エージェントへの送信に失敗しました。', 'error');
        setPendingAssistantResponseState(false);
        clearStepActivity();
        shouldContinueRunning = false;
      } finally {
        setIsSending(false);
        setIsRunningState(shouldContinueRunning);
        if (!shouldContinueRunning) {
          setIsPausedState(false);
        }
      }
    };

    const handlePauseToggle = async () => {
      if (!isRunning || isPausing) {
        return;
      }
      setIsPausing(true);
      const endpoint = isPaused ? '/api/resume' : '/api/pause';
      try {
        const response = await fetch(endpoint, { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          const message =
            data.error || (isPaused ? '再開に失敗しました。' : '一時停止に失敗しました。');
          throw new Error(message);
        }
        const nextPaused = !isPausedRef.current;
        setIsPausedState(nextPaused);
        setStatus(
          nextPaused
            ? 'エージェントを一時停止しました。'
            : 'エージェントを再開しました。',
          'info',
        );
      } catch (error) {
        setStatus(error.message || '操作に失敗しました。', 'error');
      } finally {
        setIsPausing(false);
      }
    };

    const handleNewTask = () => {
      if (isRunning || isSending) {
        return;
      }
      if (!promptInputRef.current || !promptInputRef.current.value.trim()) {
        setStatus('新しいタスクの指示を入力してください。', 'warning');
        promptInputRef.current?.focus();
        return;
      }
      pendingSubmitModeRef.current = 'new-task';
      if (formRef.current) {
        if (typeof formRef.current.requestSubmit === 'function') {
          formRef.current.requestSubmit();
        } else {
          formRef.current.submit();
        }
      }
    };

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
        const response = await fetch('/api/reset', { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          const message = data.error || '履歴のリセットに失敗しました。';
          throw new Error(message);
        }
        updateConversationState(data.messages || [], { syncStep: true });
        requestScrollToBottom();
        setStatus('履歴をリセットしました。', 'success');
        setIsRunningState(false);
        setIsPausedState(false);
      } catch (error) {
        setStatus(error.message || '履歴のリセットに失敗しました。', 'error');
      } finally {
        setIsResetting(false);
      }
    };

    const handlePromptKeyDown = (event) => {
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

    const handleModelChange = (event) => {
      const value = event.target.value;
      setSelectedModelValue(value);
      try {
        const selection = JSON.parse(value);
        const selected = modelOptions.find(
          (model) => encodeModelSelection(model) === value,
        );
        selection.label = selected ? selected.label : undefined;
        applyModelSelection(selection);
      } catch (error) {
        setStatus('モデル設定の解析に失敗しました。', 'error');
      }
    };

    const shouldDisablePause = !isRunning || isPausing;
    const pauseLabel = !isRunning ? '一時停止' : isPaused ? '再開' : '一時停止';
    const newTaskDisabled = isRunning || isSending;
    const messagesEmpty = conversation.length === 0 && !thinkingVisible;

    const messagesClassName = `messages${messagesEmpty ? ' is-empty' : ''}`;

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

    return html`
      <main className="layout">
        <section className="chat-pane" aria-label="チャット領域">
          <div className="chat-pane__content">
            <header className="chat-header">
              <div className="chat-header-main">
                <h1>チャット</h1>
              </div>
              <div className="chat-header-side">
                <div className="model-selector-group">
                  <label htmlFor="model-selector" className="model-selector-label">AIモデル</label>
                  <div className="model-selector-wrapper">
                    <select
                      id="model-selector"
                      name="model"
                      value=${modelOptions.length ? selectedModelValue : undefined}
                      onChange=${handleModelChange}
                    >
                      ${modelOptions.map((model) =>
                        html`<option key=${encodeModelSelection(model) || model.label} value=${encodeModelSelection(model)}>${model.label}</option>`,
                      )}
                    </select>
                  </div>
                </div>
                <${ConnectionIndicator} state=${connectionState} />
                <div className="chat-controls" role="group" aria-label="チャット操作">
                  <button
                    type="button"
                    id="pause-button"
                    className="control-button control-button--primary"
                    disabled=${shouldDisablePause}
                    onClick=${handlePauseToggle}
                  >
                    ${pauseLabel}
                  </button>
                  <button
                    type="button"
                    id="reset-button"
                    className="control-button control-button--ghost"
                    onClick=${handleReset}
                    disabled=${isResetting}
                  >
                    履歴リセット
                  </button>
                </div>
              </div>
            </header>
            <div className="chat-body">
              <div
                id="messages"
                className=${messagesClassName}
                aria-live="polite"
                aria-busy=${shouldBusy}
                data-empty-text="まだメッセージはありません。入力して会話を始めましょう。"
                ref=${messagesRef}
              >
                ${conversation.map(
                  (message) => html`<${MessageItem} key=${message.id} message=${message} />`,
                )}
                ${thinkingVisible
                  ? html`<${ThinkingMessage}
                      title=${busyMessageTitle}
                      sub=${busyMessageSub}
                      timestamp=${thinkingTimestampRef.current || Date.now()}
                    />`
                  : null}
              </div>
            </div>
          </div>
          <form
            id="prompt-form"
            className=${`prompt-form${isSending ? ' is-sending' : ''}`}
            autoComplete="off"
            onSubmit=${handleSubmit}
            ref=${formRef}
          >
            <label htmlFor="prompt-input" className="sr-only">プロンプト</label>
            <div className="prompt-form__field">
              <textarea
                id="prompt-input"
                name="prompt"
                placeholder="ブラウザに指示したい内容を入力してください。"
                rows="3"
                required
                ref=${promptInputRef}
                onKeyDown=${handlePromptKeyDown}
              ></textarea>
              <button type="submit" className="submit-button" aria-label="送信">
                <span className="button-icon" aria-hidden="true">⮕</span>
              </button>
            </div>
            <div className="prompt-footer">
              <button
                type="button"
                id="new-task-button"
                className="new-task-button"
                aria-label="新しいタスクとして送信"
                disabled=${newTaskDisabled}
                onClick=${handleNewTask}
              >
                新しいタスクとして送信
              </button>
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
              <div className="browser-toolbar-url" title=${browserUrl}>${browserUrl}</div>
            </div>
            <iframe src=${browserUrl} title="コンテナ内ブラウザ"></iframe>
          </div>
        </section>
      </main>
    `;
  };

  const root = document.getElementById('root');
  if (root) {
    window.ReactDOM.createRoot(root).render(html`<${App} />`);
  }
})();
