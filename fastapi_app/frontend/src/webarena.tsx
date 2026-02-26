// JP: WebArena UI のエントリポイント
// EN: Entry point for the WebArena UI
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
/**
 * EN: Import required modules.
 * JP: 必要なモジュールをインポートする。
 */
import type { WebArenaAppProps } from './types/app';
/**
 * EN: Import required modules.
 * JP: 必要なモジュールをインポートする。
 */
import { getJson, postJson, requestJson } from './lib/api';

const initialData: Partial<WebArenaAppProps> = window.__WEBARENA_APP_PROPS__ || {};
/**
 * EN: Declare variable `browserUrl`.
 * JP: 変数 `browserUrl` を宣言する。
 */
const browserUrl = initialData.browserUrl || '';
const envDefaults: Partial<EnvUrls> = initialData.envUrls || {};
/**
 * EN: Declare variable `supportedSites`.
 * JP: 変数 `supportedSites` を宣言する。
 */
const supportedSites = Array.isArray(initialData.supportedSites)
  ? initialData.supportedSites
  : [];

// JP: タスク一覧のページサイズ
// EN: Page size for the task list
const PER_PAGE = 20;

type VisionStateView = {
  supported: boolean | null;
  effective: boolean;
  userEnabled: boolean;
  loading: boolean;
  error: string;
};

/**
 * EN: Define type alias `BatchState`.
 * JP: 型エイリアス `BatchState` を定義する。
 */
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

/**
 * EN: Define type alias `LogState`.
 * JP: 型エイリアス `LogState` を定義する。
 */
type LogState =
  | { type: 'idle' }
  | { type: 'blank' }
  | { type: 'single-running' }
  | { type: 'single-result'; result: WebArenaRunResult }
  | { type: 'error'; message?: string; prefix?: string }
  | { type: 'batch'; batch: BatchState };

// JP: モデル選択を JSON 文字列に変換
// EN: Encode model selection as JSON string
const encodeModelSelection = (selection: ModelSelection | ModelOption | null | undefined) => {
  if (!selection || !selection.provider || !selection.model) {
    return null;
  }
  return JSON.stringify({ provider: selection.provider, model: selection.model });
};

// JP: サイト名を UI 表示向けに整形
// EN: Format site label for display
const formatSiteLabel = (site: string) => {
  if (!site) {
    return 'ALL';
  }
  return site
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
};

// JP: WebArena 管理画面のメインコンポーネント
// EN: Main component for WebArena console
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
  /**
   * EN: Declare variable `statusTimerRef`.
   * JP: 変数 `statusTimerRef` を宣言する。
   */
  const statusTimerRef = useRef<number | null>(null);

  const [runInProgress, setRunInProgress] = useState(false);
  const [batchInProgress, setBatchInProgress] = useState(false);
  const [runButtonLabel, setRunButtonLabel] = useState('選択タスクを実行');

  const [logState, setLogState] = useState<LogState>({ type: 'idle' });

  /**
   * EN: Declare variable `setStatus`.
   * JP: 変数 `setStatus` を宣言する。
   */
  const setStatus = useCallback((message: string, color?: string, clearAfterMs?: number) => {
    setStatusMessage(message);
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (color) {
      setStatusColor(color);
    }
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (statusTimerRef.current) {
      clearTimeout(statusTimerRef.current);
      statusTimerRef.current = null;
    }
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (clearAfterMs) {
      statusTimerRef.current = window.setTimeout(() => {
        setStatusMessage('');
        setStatusColor('var(--text-muted)');
        statusTimerRef.current = null;
      }, clearAfterMs);
    }
  }, []);

  // JP: モデル一覧と現在選択を取得
  // EN: Load model list and current selection
  const loadModels = useCallback(async () => {
    try {
      const { data } = await getJson<
        ModelOption[] | { models?: ModelOption[]; current?: ModelSelection }
      >('/api/models', {
        throwOnNonOk: false,
      });
      /**
       * EN: Declare variable `dataPayload`.
       * JP: 変数 `dataPayload` を宣言する。
       */
      const dataPayload = data as
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
      setModelOptions(models);

      /**
       * EN: Declare variable `current`.
       * JP: 変数 `current` を宣言する。
       */
      const current =
        !Array.isArray(dataPayload) &&
        typeof (dataPayload as { current?: unknown }).current === 'object'
          ? ((dataPayload as { current?: ModelSelection }).current ?? null)
          : null;
      /**
       * EN: Declare variable `desired`.
       * JP: 変数 `desired` を宣言する。
       */
      const desired = encodeModelSelection(current);
      /**
       * EN: Declare variable `hasDesired`.
       * JP: 変数 `hasDesired` を宣言する。
       */
      const hasDesired =
        desired && models.some((model) => encodeModelSelection(model) === desired);

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
      console.error(error);
      setModelOptions([]);
    }
  }, []);

  /**
   * EN: Declare variable `applyModel`.
   * JP: 変数 `applyModel` を宣言する。
   */
  const applyModel = useCallback(async (selection: ModelSelection) => {
    await postJson('/model_settings', selection, {
      parseJson: false,
      throwOnNonOk: false,
    });
  }, []);

  // JP: Vision 対応状況を取得
  // EN: Refresh vision support state
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

  // JP: タスク一覧を取得（ページング/サイトフィルタ対応）
  // EN: Load tasks with pagination and site filter
  const loadTasks = useCallback(async () => {
    setTasksLoading(true);
    setTasksError('');
    try {
      const siteQuery = selectedSite ? `&site=${selectedSite}` : '';
      const { data } = await getJson<WebArenaTasksResponse>(
        `/webarena/tasks?page=${currentPage}&per_page=${PER_PAGE}${siteQuery}`,
        {
          throwOnNonOk: false,
        }
      );
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
    /**
     * EN: Return a value from this scope.
     * JP: このスコープから値を返す。
     */
    return () => {
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (statusTimerRef.current) {
        clearTimeout(statusTimerRef.current);
        statusTimerRef.current = null;
      }
    };
  }, []);

  /**
   * EN: Declare callable constant `handleModelChange`.
   * JP: 呼び出し可能な定数 `handleModelChange` を宣言する。
   */
  const handleModelChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    /**
     * EN: Declare variable `value`.
     * JP: 変数 `value` を宣言する。
     */
    const value = event.target.value;
    setSelectedModelValue(value);
    let selection: ModelSelection;
    /**
     * EN: Wrap logic with exception handling.
     * JP: 例外処理のためにブロックを囲む。
     */
    try {
      selection = JSON.parse(value) as ModelSelection;
    } catch (error) {
      setStatus('モデル設定の解析に失敗しました。', 'var(--accent-danger)', 3000);
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return;
    }

    setStatus('モデルを変更中...', 'var(--text-muted)');
    setModelBusy(true);
    /**
     * EN: Wrap logic with exception handling.
     * JP: 例外処理のためにブロックを囲む。
     */
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

  /**
   * EN: Declare callable constant `handleVisionToggle`.
   * JP: 呼び出し可能な定数 `handleVisionToggle` を宣言する。
   */
  const handleVisionToggle = async (event: React.ChangeEvent<HTMLInputElement>) => {
    /**
     * EN: Declare variable `enabled`.
     * JP: 変数 `enabled` を宣言する。
     */
    const enabled = event.target.checked;
    setVisionBusy(true);
    /**
     * EN: Wrap logic with exception handling.
     * JP: 例外処理のためにブロックを囲む。
     */
    try {
      await postJson('/api/vision', { enabled }, { parseJson: false, throwOnNonOk: false });
    } catch (error) {
      console.error('Failed to update vision toggle', error);
      alert('スクリーンショット設定の更新に失敗しました。');
    } finally {
      setVisionBusy(false);
      refreshVisionState();
    }
  };

  /**
   * EN: Declare callable constant `handleTaskSelect`.
   * JP: 呼び出し可能な定数 `handleTaskSelect` を宣言する。
   */
  const handleTaskSelect = (taskId: number | 'custom') => {
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (taskId === 'custom') {
      setIsCustom(true);
      setSelectedTaskId(null);
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return;
    }
    setIsCustom(false);
    setSelectedTaskId(taskId);
  };

  /**
   * EN: Declare callable constant `handleCustomCardClick`.
   * JP: 呼び出し可能な定数 `handleCustomCardClick` を宣言する。
   */
  const handleCustomCardClick = (event: React.MouseEvent<HTMLDivElement>) => {
    /**
     * EN: Declare variable `target`.
     * JP: 変数 `target` を宣言する。
     */
    const target = event.target as HTMLElement;
    /**
     * EN: Declare variable `tagName`.
     * JP: 変数 `tagName` を宣言する。
     */
    const tagName = target.tagName;
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (tagName === 'INPUT' || tagName === 'TEXTAREA') {
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return;
    }
    handleTaskSelect('custom');
  };

  // JP: サイトフィルタ変更時にページと選択をリセット
  // EN: Reset pagination/selection when changing the site filter
  const handleSiteFilter = (site: string) => {
    setSelectedSite(site || '');
    setCurrentPage(1);
    setSelectedTaskId(null);
    setIsCustom(false);
  };

  // JP: 単体タスク実行のハンドラ
  // EN: Handler to run a single task
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

    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (isCustom) {
      /**
       * EN: Branch logic based on a condition.
       * JP: 条件に応じて処理を分岐する。
       */
      if (!customIntent.trim()) {
        alert('カスタムタスクの指示を入力してください。');
        /**
         * EN: Return a value from this scope.
         * JP: このスコープから値を返す。
         */
        return;
      }
      payload.custom_task = { intent: customIntent, start_url: customUrl };
    } else {
      payload.task_id = selectedTaskId;
    }

    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (selectedSite) {
      payload.selected_site = selectedSite;
    }

    setStatus('評価を実行中...', 'var(--accent-info)');
    setRunInProgress(true);
    setLogState({ type: 'single-running' });

    /**
     * EN: Wrap logic with exception handling.
     * JP: 例外処理のためにブロックを囲む。
     */
    try {
      const { data } = await postJson<WebArenaRunResult & { error?: string }, typeof payload>(
        '/webarena/run',
        payload,
        {
          errorMessage: 'Error running task',
        }
      );
      setLogState({ type: 'single-result', result: data });
      setStatus('完了', 'var(--accent-success)');
    } catch (error) {
      /**
       * EN: Declare variable `err`.
       * JP: 変数 `err` を宣言する。
       */
      const err = error as { message?: string };
      setLogState({ type: 'error', message: err.message, prefix: 'エラーが発生しました: ' });
      setStatus('エラー', 'var(--accent-danger)');
    } finally {
      setRunInProgress(false);
      setRunButtonLabel('評価を実行');
    }
  };

  // JP: 一括実行（バッチ）のハンドラ
  // EN: Handler to run tasks in batch
  const handleBatchRun = async () => {
    setStatus('一括実行中...', 'var(--accent-info)');
    setBatchInProgress(true);
    setLogState({ type: 'blank' });

    let taskIds: number[] = [];
    try {
      /**
       * EN: Declare variable `siteQuery`.
       * JP: 変数 `siteQuery` を宣言する。
       */
      const siteQuery = selectedSite ? `&site=${selectedSite}` : '';
      const { data: taskData } = await getJson<WebArenaTasksResponse>(
        `/webarena/tasks?page=1&per_page=1000${siteQuery}`,
        {
          throwOnNonOk: false,
        }
      );
      taskIds = (taskData.tasks || []).map((task) => task.task_id);
    } catch (error) {
      /**
       * EN: Declare variable `err`.
       * JP: 変数 `err` を宣言する。
       */
      const err = error as { message?: string };
      setLogState({
        type: 'error',
        message: `タスクの取得に失敗しました: ${err.message}`,
        prefix: '',
      });
      setStatus('エラー', 'var(--accent-danger)');
      setBatchInProgress(false);
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
    if (!taskIds.length) {
      setLogState({ type: 'error', message: '表示中のタスクがありません。', prefix: '' });
      setStatus('エラー', 'var(--accent-danger)');
      setBatchInProgress(false);
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return;
    }

    const results: WebArenaRunResult[] = [];
    /**
     * EN: Declare variable `successCount`.
     * JP: 変数 `successCount` を宣言する。
     */
    let successCount = 0;
    /**
     * EN: Declare variable `startTime`.
     * JP: 変数 `startTime` を宣言する。
     */
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

    /**
     * EN: Wrap logic with exception handling.
     * JP: 例外処理のためにブロックを囲む。
     */
    try {
      /**
       * EN: Iterate with a loop.
       * JP: ループで処理を繰り返す。
       */
      for (let index = 0; index < taskIds.length; index += 1) {
        /**
         * EN: Declare variable `taskId`.
         * JP: 変数 `taskId` を宣言する。
         */
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
        /**
         * EN: Wrap logic with exception handling.
         * JP: 例外処理のためにブロックを囲む。
         */
        try {
          const { data: responseData, response } = await requestJson<
            WebArenaRunResult & { error?: string }
          >(
            '/webarena/run',
            {
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
            },
            { throwOnNonOk: false }
          );
          /**
           * EN: Branch logic based on a condition.
           * JP: 条件に応じて処理を分岐する。
           */
          if (!response.ok) {
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
          /**
           * EN: Declare variable `err`.
           * JP: 変数 `err` を宣言する。
           */
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
        /**
         * EN: Branch logic based on a condition.
         * JP: 条件に応じて処理を分岐する。
         */
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

      /**
       * EN: Declare variable `endTime`.
       * JP: 変数 `endTime` を宣言する。
       */
      const endTime = Date.now();
      /**
       * EN: Declare variable `totalTimeMs`.
       * JP: 変数 `totalTimeMs` を宣言する。
       */
      const totalTimeMs = endTime - startTime;
      /**
       * EN: Declare variable `totalMinutes`.
       * JP: 変数 `totalMinutes` を宣言する。
       */
      const totalMinutes = Math.floor(totalTimeMs / 60000);
      /**
       * EN: Declare callable constant `totalSeconds`.
       * JP: 呼び出し可能な定数 `totalSeconds` を宣言する。
       */
      const totalSeconds = ((totalTimeMs % 60000) / 1000).toFixed(1);
      /**
       * EN: Declare variable `timeText`.
       * JP: 変数 `timeText` を宣言する。
       */
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

      /**
       * EN: Wrap logic with exception handling.
       * JP: 例外処理のためにブロックを囲む。
       */
      try {
        setStatus('結果を保存中...', 'var(--accent-info)');
        await postJson('/webarena/save_results', { results }, {
          parseJson: false,
          throwOnNonOk: false,
        });
        setStatus('完了 (保存済み)', 'var(--accent-success)');
      } catch (error) {
        console.error('Save failed', error);
        setStatus('完了 (保存失敗)', 'var(--accent-success)');
      }
    } catch (error) {
      /**
       * EN: Declare variable `err`.
       * JP: 変数 `err` を宣言する。
       */
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

  /**
   * EN: Declare callable constant `handleEnvChange`.
   * JP: 呼び出し可能な定数 `handleEnvChange` を宣言する。
   */
  const handleEnvChange = (key: keyof EnvUrls) => (event: React.FormEvent<HTMLInputElement>) => {
    /**
     * EN: Declare variable `target`.
     * JP: 変数 `target` を宣言する。
     */
    const target = event.target as HTMLInputElement;
    setEnvUrls((prev) => ({ ...prev, [key]: target.value }));
  };

  /**
   * EN: Declare callable constant `renderLogs`.
   * JP: 呼び出し可能な定数 `renderLogs` を宣言する。
   */
  const renderLogs = () => {
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (logState.type === 'single-running') {
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return (
        <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <i>Running task... check browser view</i>
        </div>
      );
    }

    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (logState.type === 'error') {
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return (
        <div style={{ color: 'red', padding: '20px' }}>
          {logState.prefix || ''}
          {logState.message}
        </div>
      );
    }

    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (logState.type === 'single-result') {
      /**
       * EN: Declare variable `result`.
       * JP: 変数 `result` を宣言する。
       */
      const result = logState.result;
      /**
       * EN: Declare variable `summaryStyle`.
       * JP: 変数 `summaryStyle` を宣言する。
       */
      const summaryStyle = {
        padding: '16px',
        marginBottom: '16px',
        borderRadius: '12px',
        background: result.success ? '#f0fdf4' : '#fef2f2',
        border: `1px solid ${result.success ? '#bbf7d0' : '#fecaca'}`,
      };
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
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

    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (logState.type === 'batch') {
      /**
       * EN: Declare variable `batch`.
       * JP: 変数 `batch` を宣言する。
       */
      const batch = logState.batch;
      /**
       * EN: Declare variable `total`.
       * JP: 変数 `total` を宣言する。
       */
      const total = batch.total || 0;
      /**
       * EN: Declare variable `currentIndex`.
       * JP: 変数 `currentIndex` を宣言する。
       */
      const currentIndex = batch.currentIndex || 0;
      /**
       * EN: Declare variable `pct`.
       * JP: 変数 `pct` を宣言する。
       */
      const pct = total > 0 ? Math.max(5, Math.round((currentIndex / total) * 100)) : 0;
      /**
       * EN: Declare variable `progressLabel`.
       * JP: 変数 `progressLabel` を宣言する。
       */
      const progressLabel =
        batch.status === 'complete'
          ? '完了'
          : batch.status === 'error'
            ? 'エラー'
            : '一括実行中';
      /**
       * EN: Declare variable `progressMessage`.
       * JP: 変数 `progressMessage` を宣言する。
       */
      const progressMessage =
        batch.status === 'complete'
          ? `成功 ${batch.successCount || 0} / ${total} 件`
          : batch.status === 'error'
            ? batch.errorMessage
            : batch.currentTaskId
              ? `TASK ${batch.currentTaskId} を実行中... (${currentIndex}/${total})`
              : `実行中... (${currentIndex}/${total})`;

      /**
       * EN: Declare variable `summary`.
       * JP: 変数 `summary` を宣言する。
       */
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

      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
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

    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (logState.type === 'blank') {
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
    return (
      <p style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '20px' }}>
        タスクを選択して「評価を実行」をクリックしてください。
      </p>
    );
  };

  /**
   * EN: Declare variable `resultBadge`.
   * JP: 変数 `resultBadge` を宣言する。
   */
  const resultBadge = useMemo(() => {
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (logState.type !== 'single-result') {
      /**
       * EN: Return a value from this scope.
       * JP: このスコープから値を返す。
       */
      return { visible: false, text: '', className: 'wa-badge' };
    }
    /**
     * EN: Declare variable `success`.
     * JP: 変数 `success` を宣言する。
     */
    const success = logState.result?.success;
    /**
     * EN: Return a value from this scope.
     * JP: このスコープから値を返す。
     */
    return {
      visible: true,
      text: success ? 'SUCCESS' : 'FAILURE',
      className: `wa-badge ${success ? 'wa-badge-success' : 'wa-badge-fail'}`,
    };
  }, [logState]);

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
  const visionBadgeClass = `wa-badge ${
    visionState.loading
      ? 'wa-badge-pending'
      : visionState.supported
        ? 'wa-badge-success'
        : 'wa-badge-fail'
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
      visionHint = '選択中のモデルはスクリーンショット非対応です。GPT/Gemini/Claude 系のみ対応。';
    } else if (visionState.effective) {
      visionHint = 'スクリーンショットをモデルに送信しています。';
    } else {
      visionHint = 'スクリーンショット送信を停止中です。';
    }
  }

  /**
   * EN: Declare variable `runDisabled`.
   * JP: 変数 `runDisabled` を宣言する。
   */
  const runDisabled = runInProgress || modelBusy || batchInProgress;
  /**
   * EN: Declare variable `batchDisabled`.
   * JP: 変数 `batchDisabled` を宣言する。
   */
  const batchDisabled = batchInProgress;

  /**
   * EN: Return a value from this scope.
   * JP: このスコープから値を返す。
   */
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
