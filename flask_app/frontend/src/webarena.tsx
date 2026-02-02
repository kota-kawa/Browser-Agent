import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import type {
  EnvUrls,
  ModelOption,
  ModelSelection,
  VisionState,
  WebArenaRunResult,
  WebArenaTask,
  WebArenaTasksResponse,
} from './types/api';
import type { WebArenaAppProps } from './types/app';

const initialData: Partial<WebArenaAppProps> = window.__WEBARENA_APP_PROPS__ || {};
const browserUrl = initialData.browserUrl || '';
const envDefaults: Partial<EnvUrls> = initialData.envUrls || {};
const supportedSites = Array.isArray(initialData.supportedSites)
  ? initialData.supportedSites
  : [];

const PER_PAGE = 20;

type VisionStateView = {
  supported: boolean | null;
  effective: boolean;
  userEnabled: boolean;
  loading: boolean;
  error: string;
};

type BatchState = {
  status: 'running' | 'complete' | 'error';
  total: number;
  currentIndex: number;
  currentTaskId: number | null;
  results: WebArenaRunResult[];
  successCount: number;
  timeText?: string;
  errorMessage?: string;
};

type LogState =
  | { type: 'idle' }
  | { type: 'blank' }
  | { type: 'single-running' }
  | { type: 'single-result'; result: WebArenaRunResult }
  | { type: 'error'; message?: string; prefix?: string }
  | { type: 'batch'; batch: BatchState };

const encodeModelSelection = (selection: ModelSelection | ModelOption | null | undefined) => {
  if (!selection || !selection.provider || !selection.model) {
    return null;
  }
  return JSON.stringify({ provider: selection.provider, model: selection.model });
};

const formatSiteLabel = (site: string) => {
  if (!site) {
    return 'ALL';
  }
  return site
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
};

const App = () => {
  const [modelOptions, setModelOptions] = useState<ModelOption[]>([]);
  const [selectedModelValue, setSelectedModelValue] = useState('');
  const [modelBusy, setModelBusy] = useState(false);

  const [visionState, setVisionState] = useState<VisionStateView>({
    supported: null,
    effective: false,
    userEnabled: true,
    loading: true,
    error: '',
  });
  const [visionBusy, setVisionBusy] = useState(false);

  const [envUrls, setEnvUrls] = useState<EnvUrls>({
    shopping: envDefaults.shopping || '',
    shopping_admin: envDefaults.shopping_admin || '',
    gitlab: envDefaults.gitlab || '',
    reddit: envDefaults.reddit || '',
  });

  const [tasks, setTasks] = useState<WebArenaTask[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [tasksError, setTasksError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(true);
  const [selectedSite, setSelectedSite] = useState('');

  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [isCustom, setIsCustom] = useState(false);
  const [customIntent, setCustomIntent] = useState('');
  const [customUrl, setCustomUrl] = useState('');

  const [statusMessage, setStatusMessage] = useState('');
  const [statusColor, setStatusColor] = useState('var(--text-muted)');
  const statusTimerRef = useRef<number | null>(null);

  const [runInProgress, setRunInProgress] = useState(false);
  const [batchInProgress, setBatchInProgress] = useState(false);
  const [runButtonLabel, setRunButtonLabel] = useState('選択タスクを実行');

  const [logState, setLogState] = useState<LogState>({ type: 'idle' });

  const setStatus = useCallback((message: string, color?: string, clearAfterMs?: number) => {
    setStatusMessage(message);
    if (color) {
      setStatusColor(color);
    }
    if (statusTimerRef.current) {
      clearTimeout(statusTimerRef.current);
      statusTimerRef.current = null;
    }
    if (clearAfterMs) {
      statusTimerRef.current = window.setTimeout(() => {
        setStatusMessage('');
        setStatusColor('var(--text-muted)');
        statusTimerRef.current = null;
      }, clearAfterMs);
    }
  }, []);

  const loadModels = useCallback(async () => {
    try {
      const response = await fetch('/api/models');
      const data = (await response.json()) as
        | ModelOption[]
        | { models?: ModelOption[]; current?: ModelSelection };
      const models = Array.isArray(data)
        ? data
        : Array.isArray((data as { models?: ModelOption[] }).models)
          ? ((data as { models?: ModelOption[] }).models ?? [])
          : [];
      setModelOptions(models);

      const current =
        !Array.isArray(data) && typeof (data as { current?: unknown }).current === 'object'
          ? ((data as { current?: ModelSelection }).current ?? null)
          : null;
      const desired = encodeModelSelection(current);
      const hasDesired =
        desired && models.some((model) => encodeModelSelection(model) === desired);

      if (hasDesired) {
        setSelectedModelValue(desired);
      } else if (models.length) {
        setSelectedModelValue(encodeModelSelection(models[0]) || '');
      }
    } catch (error) {
      console.error(error);
      setModelOptions([]);
    }
  }, []);

  const applyModel = useCallback(async (selection: ModelSelection) => {
    await fetch('/model_settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(selection),
    });
  }, []);

  const refreshVisionState = useCallback(async () => {
    try {
      const res = await fetch('/api/vision');
      const data = (await res.json()) as VisionState;
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

  const loadTasks = useCallback(async () => {
    setTasksLoading(true);
    setTasksError('');
    try {
      const siteQuery = selectedSite ? `&site=${selectedSite}` : '';
      const res = await fetch(
        `/webarena/tasks?page=${currentPage}&per_page=${PER_PAGE}${siteQuery}`
      );
      const data = (await res.json()) as WebArenaTasksResponse;
      setTasks(Array.isArray(data.tasks) ? data.tasks : []);
      setHasNextPage((data.tasks || []).length >= PER_PAGE);
    } catch (error) {
      console.error('Failed to load tasks', error);
      setTasks([]);
      setTasksError('Failed to load tasks.');
    } finally {
      setTasksLoading(false);
    }
  }, [currentPage, selectedSite]);

  useEffect(() => {
    loadModels();
    refreshVisionState();
  }, [loadModels, refreshVisionState]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  useEffect(() => {
    return () => {
      if (statusTimerRef.current) {
        clearTimeout(statusTimerRef.current);
        statusTimerRef.current = null;
      }
    };
  }, []);

  const handleModelChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    setSelectedModelValue(value);
    let selection: ModelSelection;
    try {
      selection = JSON.parse(value) as ModelSelection;
    } catch (error) {
      setStatus('モデル設定の解析に失敗しました。', 'var(--accent-danger)', 3000);
      return;
    }

    setStatus('モデルを変更中...', 'var(--text-muted)');
    setModelBusy(true);
    try {
      await applyModel(selection);
      setStatus('モデルを変更しました。', 'var(--text-muted)', 3000);
    } catch (error) {
      setStatus('モデルの変更に失敗しました。', 'var(--accent-danger)', 3000);
    } finally {
      setModelBusy(false);
      refreshVisionState();
    }
  };

  const handleVisionToggle = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const enabled = event.target.checked;
    setVisionBusy(true);
    try {
      await fetch('/api/vision', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      });
    } catch (error) {
      console.error('Failed to update vision toggle', error);
      alert('スクリーンショット設定の更新に失敗しました。');
    } finally {
      setVisionBusy(false);
      refreshVisionState();
    }
  };

  const handleTaskSelect = (taskId: number | 'custom') => {
    if (taskId === 'custom') {
      setIsCustom(true);
      setSelectedTaskId(null);
      return;
    }
    setIsCustom(false);
    setSelectedTaskId(taskId);
  };

  const handleCustomCardClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement;
    const tagName = target.tagName;
    if (tagName === 'INPUT' || tagName === 'TEXTAREA') {
      return;
    }
    handleTaskSelect('custom');
  };

  const handleSiteFilter = (site: string) => {
    setSelectedSite(site || '');
    setCurrentPage(1);
    setSelectedTaskId(null);
    setIsCustom(false);
  };

  const handleRun = async () => {
    if (selectedTaskId === null && !isCustom) {
      alert('タスクを選択してください。');
      return;
    }

    const payload: {
      env_urls: EnvUrls;
      custom_task?: { intent: string; start_url?: string };
      task_id?: number | null;
      selected_site?: string;
    } = {
      env_urls: {
        shopping: envUrls.shopping,
        shopping_admin: envUrls.shopping_admin,
        gitlab: envUrls.gitlab,
        reddit: envUrls.reddit,
      },
    };

    if (isCustom) {
      if (!customIntent.trim()) {
        alert('カスタムタスクの指示を入力してください。');
        return;
      }
      payload.custom_task = { intent: customIntent, start_url: customUrl };
    } else {
      payload.task_id = selectedTaskId;
    }

    if (selectedSite) {
      payload.selected_site = selectedSite;
    }

    setStatus('評価を実行中...', 'var(--accent-info)');
    setRunInProgress(true);
    setLogState({ type: 'single-running' });

    try {
      const res = await fetch('/webarena/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = (await res.json()) as WebArenaRunResult & { error?: string };
      if (!res.ok) {
        throw new Error(data.error || 'Error running task');
      }
      setLogState({ type: 'single-result', result: data });
      setStatus('完了', 'var(--accent-success)');
    } catch (error) {
      const err = error as { message?: string };
      setLogState({ type: 'error', message: err.message, prefix: 'エラーが発生しました: ' });
      setStatus('エラー', 'var(--accent-danger)');
    } finally {
      setRunInProgress(false);
      setRunButtonLabel('評価を実行');
    }
  };

  const handleBatchRun = async () => {
    setStatus('一括実行中...', 'var(--accent-info)');
    setBatchInProgress(true);
    setLogState({ type: 'blank' });

    let taskIds: number[] = [];
    try {
      const siteQuery = selectedSite ? `&site=${selectedSite}` : '';
      const taskRes = await fetch(`/webarena/tasks?page=1&per_page=1000${siteQuery}`);
      const taskData = (await taskRes.json()) as WebArenaTasksResponse;
      taskIds = (taskData.tasks || []).map((task) => task.task_id);
    } catch (error) {
      const err = error as { message?: string };
      setLogState({
        type: 'error',
        message: `タスクの取得に失敗しました: ${err.message}`,
        prefix: '',
      });
      setStatus('エラー', 'var(--accent-danger)');
      setBatchInProgress(false);
      return;
    }

    if (!taskIds.length) {
      setLogState({ type: 'error', message: '表示中のタスクがありません。', prefix: '' });
      setStatus('エラー', 'var(--accent-danger)');
      setBatchInProgress(false);
      return;
    }

    const results: WebArenaRunResult[] = [];
    let successCount = 0;
    const startTime = Date.now();

    setLogState({
      type: 'batch',
      batch: {
        status: 'running',
        total: taskIds.length,
        currentIndex: 0,
        currentTaskId: null,
        results: [],
        successCount: 0,
      },
    });

    try {
      for (let index = 0; index < taskIds.length; index += 1) {
        const taskId = taskIds[index];
        setLogState({
          type: 'batch',
          batch: {
            status: 'running',
            total: taskIds.length,
            currentIndex: index + 1,
            currentTaskId: taskId,
            results: [...results],
            successCount,
          },
        });

        let data: WebArenaRunResult;
        try {
          const res = await fetch('/webarena/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              env_urls: {
                shopping: envUrls.shopping,
                shopping_admin: envUrls.shopping_admin,
                gitlab: envUrls.gitlab,
                reddit: envUrls.reddit,
              },
              task_id: taskId,
              selected_site: selectedSite || undefined,
            }),
          });
          const responseData = (await res.json()) as WebArenaRunResult & { error?: string };
          if (!res.ok) {
            data = {
              task_id: taskId,
              success: false,
              summary: responseData.error || `TASK ${taskId} の実行に失敗しました`,
              evaluation: 'Batch runner recorded an error for this task.',
              steps: [],
            };
          } else {
            data = responseData;
          }
        } catch (error) {
          const err = error as { message?: string };
          data = {
            task_id: taskId,
            success: false,
            summary: `エラー: ${err.message}`,
            evaluation: 'Batch runner caught an exception.',
            steps: [],
          };
        }

        results.push(data);
        if (data.success) {
          successCount += 1;
        }

        setLogState({
          type: 'batch',
          batch: {
            status: 'running',
            total: taskIds.length,
            currentIndex: index + 1,
            currentTaskId: taskId,
            results: [...results],
            successCount,
          },
        });
      }

      const endTime = Date.now();
      const totalTimeMs = endTime - startTime;
      const totalMinutes = Math.floor(totalTimeMs / 60000);
      const totalSeconds = ((totalTimeMs % 60000) / 1000).toFixed(1);
      const timeText =
        totalMinutes > 0 ? `${totalMinutes}分 ${totalSeconds}秒` : `${totalSeconds}秒`;

      setLogState({
        type: 'batch',
        batch: {
          status: 'complete',
          total: taskIds.length,
          currentIndex: taskIds.length,
          currentTaskId: null,
          results: [...results],
          successCount,
          timeText,
        },
      });

      try {
        setStatus('結果を保存中...', 'var(--accent-info)');
        await fetch('/webarena/save_results', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ results }),
        });
        setStatus('完了 (保存済み)', 'var(--accent-success)');
      } catch (error) {
        console.error('Save failed', error);
        setStatus('完了 (保存失敗)', 'var(--accent-success)');
      }
    } catch (error) {
      const err = error as { message?: string };
      setLogState({
        type: 'batch',
        batch: {
          status: 'error',
          total: taskIds.length,
          currentIndex: results.length,
          currentTaskId: null,
          results: [...results],
          successCount,
          errorMessage: err.message,
        },
      });
      setStatus('エラー', 'var(--accent-danger)');
    } finally {
      setBatchInProgress(false);
    }
  };

  const handleEnvChange = (key: keyof EnvUrls) => (event: React.FormEvent<HTMLInputElement>) => {
    const target = event.target as HTMLInputElement;
    setEnvUrls((prev) => ({ ...prev, [key]: target.value }));
  };

  const renderLogs = () => {
    if (logState.type === 'single-running') {
      return (
        <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <i>Running task... check browser view</i>
        </div>
      );
    }

    if (logState.type === 'error') {
      return (
        <div style={{ color: 'red', padding: '20px' }}>
          {logState.prefix || ''}
          {logState.message}
        </div>
      );
    }

    if (logState.type === 'single-result') {
      const result = logState.result;
      const summaryStyle = {
        padding: '16px',
        marginBottom: '16px',
        borderRadius: '12px',
        background: result.success ? '#f0fdf4' : '#fef2f2',
        border: `1px solid ${result.success ? '#bbf7d0' : '#fecaca'}`,
      };
      return (
        <div>
          <div style={summaryStyle}>
            <div
              style={{
                fontWeight: 700,
                color: result.success ? '#15803d' : '#b91c1c',
                marginBottom: '8px',
              }}
            >
              {result.success ? '✓ 成功 (SUCCESS)' : '✕ 失敗 (FAILURE)'}
            </div>
            <div
              dangerouslySetInnerHTML={{
                __html: `<strong>Summary:</strong> ${result.summary || ''}`,
              }}
            ></div>
            {result.evaluation && (
              <div
                style={{
                  marginTop: '8px',
                  paddingTop: '8px',
                  borderTop: '1px dashed rgba(0,0,0,0.1)',
                  fontSize: '0.9em',
                }}
                dangerouslySetInnerHTML={{
                  __html: `<strong>Details:</strong><br>${result.evaluation.replace(/\n/g, '<br>')}`,
                }}
              ></div>
            )}
          </div>
          {(result.steps || []).map((step, index) => (
            <div
              key={`${step.step}-${index}`}
              className="wa-step"
              dangerouslySetInnerHTML={{
                __html: `<span class="wa-step-num">${step.step}.</span> ${step.content}`,
              }}
            ></div>
          ))}
        </div>
      );
    }

    if (logState.type === 'batch') {
      const batch = logState.batch;
      const total = batch.total || 0;
      const currentIndex = batch.currentIndex || 0;
      const pct = total > 0 ? Math.max(5, Math.round((currentIndex / total) * 100)) : 0;
      const progressLabel =
        batch.status === 'complete'
          ? '完了'
          : batch.status === 'error'
            ? 'エラー'
            : '一括実行中';
      const progressMessage =
        batch.status === 'complete'
          ? `成功 ${batch.successCount || 0} / ${total} 件`
          : batch.status === 'error'
            ? batch.errorMessage
            : batch.currentTaskId
              ? `TASK ${batch.currentTaskId} を実行中... (${currentIndex}/${total})`
              : `実行中... (${currentIndex}/${total})`;

      const summary =
        batch.status === 'complete' ? (
          <div className="wa-batch-summary">
            <div className="wa-batch-summary__title">バッチ結果</div>
            <div className="wa-batch-summary__stats">
              成功: {batch.successCount || 0} / {total} | スコア:{' '}
              {total ? Math.round(((batch.successCount || 0) / total) * 10000) / 100 : 0}%
              <br />
              所要時間: {batch.timeText || ''}
            </div>
          </div>
        ) : null;

      return (
        <div>
          {summary}
          <div className="wa-progress-card">
            <div className="wa-progress-meta">
              <div className="wa-progress-label">{progressLabel}</div>
              <div className="wa-progress-count">
                <span data-progress-count>{currentIndex}</span> / {total}
              </div>
            </div>
            <div className="wa-progress-bar">
              <div
                className={`wa-progress-bar-fill${
                  batch.status === 'complete'
                    ? ' is-complete'
                    : batch.status === 'error'
                      ? ' is-error'
                      : ''
                }`}
                data-progress-bar
                style={{
                  width:
                    batch.status === 'complete' || batch.status === 'error' ? '100%' : `${pct}%`,
                }}
              ></div>
            </div>
            <div className="wa-progress-current" data-progress-current>
              {progressMessage}
            </div>
          </div>
          {(batch.results || []).map((result, index) => (
            <div className="wa-task-result" key={result.task_id ?? index}>
              <div className="wa-task-result__head">
                <div className="wa-task-result__title">
                  ({index + 1}/{total}) TASK {result.task_id ?? ''}
                </div>
                <span
                  className={`wa-badge ${result.success ? 'wa-badge-success' : 'wa-badge-fail'}`}
                >
                  {result.success ? 'SUCCESS' : 'FAIL'}
                </span>
              </div>
              <div
                className="wa-task-result__summary"
                dangerouslySetInnerHTML={{
                  __html: `<strong>Summary:</strong> ${result.summary || ''}`,
                }}
              ></div>
              {result.evaluation && (
                <div
                  className="wa-task-result__evaluation"
                  dangerouslySetInnerHTML={{
                    __html: result.evaluation.replace(/\n/g, '<br>'),
                  }}
                ></div>
              )}
            </div>
          ))}
          {batch.status === 'error' && (
            <div className="wa-task-result">
              <div className="wa-task-result__head">
                <div className="wa-task-result__title">バッチを中断しました</div>
                <span className="wa-badge wa-badge-fail">ERROR</span>
              </div>
              <div className="wa-task-result__summary">{batch.errorMessage || ''}</div>
            </div>
          )}
        </div>
      );
    }

    if (logState.type === 'blank') {
      return null;
    }

    return (
      <p style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '20px' }}>
        タスクを選択して「評価を実行」をクリックしてください。
      </p>
    );
  };

  const resultBadge = useMemo(() => {
    if (logState.type !== 'single-result') {
      return { visible: false, text: '', className: 'wa-badge' };
    }
    const success = logState.result?.success;
    return {
      visible: true,
      text: success ? 'SUCCESS' : 'FAILURE',
      className: `wa-badge ${success ? 'wa-badge-success' : 'wa-badge-fail'}`,
    };
  }, [logState]);

  const visionBadgeText = visionState.loading
    ? 'CHECKING'
    : visionState.supported
      ? 'SUPPORTED'
      : 'UNSUPPORTED';
  const visionBadgeClass = `wa-badge ${
    visionState.loading
      ? 'wa-badge-pending'
      : visionState.supported
        ? 'wa-badge-success'
        : 'wa-badge-fail'
  }`;

  let visionHint = 'モデルがサポートしていればスクリーンショットを送信します。';
  if (visionState.error) {
    visionHint = visionState.error;
  } else if (!visionState.loading) {
    if (!visionState.supported) {
      visionHint = '選択中のモデルはスクリーンショット非対応です。GPT/Gemini/Claude 系のみ対応。';
    } else if (visionState.effective) {
      visionHint = 'スクリーンショットをモデルに送信しています。';
    } else {
      visionHint = 'スクリーンショット送信を停止中です。';
    }
  }

  const runDisabled = runInProgress || modelBusy || batchInProgress;
  const batchDisabled = batchInProgress;

  return (
    <div className="wa-layout">
      <aside className="wa-sidebar">
        <div className="wa-header">
          <h1>WebArena Eval</h1>
          <a href="/" className="wa-back-link">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            ホームに戻る
          </a>
        </div>

        <div className="wa-section">
          <h4 className="wa-section-title">評価モデル</h4>
          <div className="model-selector-wrapper">
            <select
              id="model-selector"
              value={modelOptions.length ? selectedModelValue : undefined}
              onChange={handleModelChange}
            >
              {modelOptions.length === 0 ? (
                <option>Loading models...</option>
              ) : (
                modelOptions.map((model) => (
                  <option
                    key={encodeModelSelection(model) || model.label}
                    value={encodeModelSelection(model) as string}
                  >
                    {model.label}
                  </option>
                ))
              )}
            </select>
          </div>
        </div>

        <div className="wa-section">
          <div
            className="wa-section-title"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <span>スクリーンショット参照</span>
            <span id="vision-support-badge" className={visionBadgeClass}>
              {visionBadgeText}
            </span>
          </div>
          <label className="wa-toggle">
            <input
              type="checkbox"
              id="vision-toggle"
              checked={visionState.userEnabled}
              disabled={visionState.loading || !visionState.supported || visionBusy}
              onChange={handleVisionToggle}
            />
            <span className="wa-toggle-slider" aria-hidden="true"></span>
            <span className="wa-toggle-label" id="vision-toggle-label">
              {visionState.userEnabled ? 'ON' : 'OFF'}
            </span>
          </label>
          <p id="vision-hint" className="wa-hint">
            {visionHint}
          </p>
        </div>

        <details className="wa-config-details">
          <summary>環境設定 (Base URLs)</summary>
          <div className="wa-config-content">
            <div className="wa-input-group">
              <label>Shopping</label>
              <input
                type="text"
                id="url-shopping"
                className="wa-input"
                value={envUrls.shopping}
                onInput={handleEnvChange('shopping')}
              />
            </div>
            <div className="wa-input-group">
              <label>Admin</label>
              <input
                type="text"
                id="url-admin"
                className="wa-input"
                value={envUrls.shopping_admin}
                onInput={handleEnvChange('shopping_admin')}
              />
            </div>
            <div className="wa-input-group">
              <label>GitLab</label>
              <input
                type="text"
                id="url-gitlab"
                className="wa-input"
                value={envUrls.gitlab}
                onInput={handleEnvChange('gitlab')}
              />
            </div>
            <div className="wa-input-group">
              <label>Reddit</label>
              <input
                type="text"
                id="url-reddit"
                className="wa-input"
                value={envUrls.reddit}
                onInput={handleEnvChange('reddit')}
              />
            </div>
          </div>
        </details>

        <div className="wa-section">
          <h4 className="wa-section-title">環境で絞り込み</h4>
          <div id="site-filters" style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            <button
              className={`wa-btn-chip${selectedSite === '' ? ' active' : ''}`}
              data-site=""
              onClick={() => handleSiteFilter('')}
            >
              ALL
            </button>
            {supportedSites.map((site) => (
              <button
                key={site}
                className={`wa-btn-chip${selectedSite === site ? ' active' : ''}`}
                data-site={site}
                onClick={() => handleSiteFilter(site)}
              >
                {formatSiteLabel(site)}
              </button>
            ))}
          </div>
        </div>

        <div
          className="wa-section"
          style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h4 className="wa-section-title">タスク一覧</h4>
            <div className="wa-pagination">
              <button
                id="prev-page"
                className="wa-btn-sm"
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
              >
                &lt;
              </button>
              <span
                id="page-indicator"
                style={{
                  fontSize: '0.75rem',
                  color: 'var(--text-muted)',
                  fontWeight: 600,
                  padding: '0 6px',
                }}
              >
                {currentPage}
              </span>
              <button
                id="next-page"
                className="wa-btn-sm"
                disabled={!hasNextPage}
                onClick={() => setCurrentPage((prev) => prev + 1)}
              >
                &gt;
              </button>
            </div>
          </div>

          <div id="task-list" className="wa-task-list" style={{ overflowY: 'auto', padding: '4px' }}>
            {tasksLoading ? (
              <div style={{ padding: '10px', color: '#94a3b8', textAlign: 'center' }}>
                Loading...
              </div>
            ) : tasksError ? (
              <div style={{ color: 'red', padding: '10px' }}>{tasksError}</div>
            ) : (
              tasks.map((task) => (
                <div
                  key={task.task_id}
                  className={`wa-task-card${
                    selectedTaskId === task.task_id && !isCustom ? ' active' : ''
                  }`}
                  data-id={task.task_id}
                  onClick={() => handleTaskSelect(task.task_id)}
                >
                  <div className="wa-task-id">TASK {task.task_id}</div>
                  <div className="wa-task-desc" title={task.intent}>
                    {task.intent}
                  </div>
                </div>
              ))
            )}
          </div>

          <div
            className={`wa-task-card${isCustom ? ' active' : ''}`}
            id="custom-task-card"
            style={{ marginTop: '10px', borderStyle: 'dashed' }}
            onClick={handleCustomCardClick}
          >
            <div className="wa-task-id">CUSTOM TASK</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 500 }}>カスタムタスクを実行</div>
            <div
              id="custom-inputs"
              style={{ marginTop: '10px', display: isCustom ? 'block' : 'none' }}
            >
              <input
                type="text"
                id="custom-url"
                className="wa-input"
                placeholder="開始URL"
                style={{ marginBottom: '8px' }}
                value={customUrl}
                onInput={(event) => setCustomUrl((event.target as HTMLInputElement).value)}
              />
              <textarea
                id="custom-intent"
                className="wa-input"
                rows={3}
                placeholder="指示内容を入力..."
                value={customIntent}
                onInput={(event) => setCustomIntent((event.target as HTMLTextAreaElement).value)}
              ></textarea>
            </div>
          </div>
        </div>

        <div style={{ paddingTop: '10px' }}>
          <button
            id="run-eval-btn"
            className="control-button control-button--primary"
            style={{ width: '100%', height: '46px', fontSize: '1rem', marginBottom: '8px' }}
            disabled={runDisabled}
            onClick={handleRun}
          >
            {runInProgress ? (
              <>
                <span className="connection-indicator" data-state="connecting">
                  <span className="dot"></span>
                </span>
                実行中...
              </>
            ) : (
              runButtonLabel
            )}
          </button>
          <button
            id="run-batch-btn"
            className="control-button"
            style={{
              width: '100%',
              height: '42px',
              fontSize: '0.95rem',
              border: '1px solid var(--border-subtle)',
            }}
            disabled={batchDisabled}
            onClick={handleBatchRun}
          >
            {batchInProgress ? (
              <>
                <span className="connection-indicator" data-state="connecting">
                  <span className="dot"></span>
                </span>
                一括実行中...
              </>
            ) : (
              '表示中タスクを順番に実行'
            )}
          </button>
          <div
            id="status-msg"
            style={{
              textAlign: 'center',
              marginTop: '8px',
              fontSize: '0.8rem',
              color: statusColor,
              minHeight: '1.2em',
            }}
          >
            {statusMessage}
          </div>
        </div>
      </aside>

      <main className="wa-main-col">
        <div className="wa-browser-container">
          <iframe
            src={browserUrl}
            title="Remote Browser"
            style={{ width: '100%', height: '100%', border: 'none' }}
          ></iframe>
        </div>
        <div className="wa-results-container">
          <div className="wa-results-header">
            <h3>実行ログ / 結果</h3>
            <span
              id="result-badge"
              className={resultBadge.className}
              style={{ display: resultBadge.visible ? 'inline-flex' : 'none' }}
            >
              {resultBadge.text}
            </span>
          </div>
          <div id="logs" className="wa-log-area">
            {renderLogs()}
          </div>
        </div>
      </main>
    </div>
  );
};

const root = document.getElementById('root');
if (root) {
  createRoot(root).render(<App />);
}
