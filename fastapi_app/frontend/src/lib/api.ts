// JP: API レスポンスの共通型とヘルパー
// EN: Shared API response types and helpers
export type ErrorResponse = {
  error: string;
};

type JsonRequestOptions<T> = {
  fallback?: T;
  errorMessage?: string;
  preferErrorBody?: boolean;
  throwOnNonOk?: boolean;
  throwOnParseError?: boolean;
  parseJson?: boolean;
};

// JP: オブジェクト判定のユーティリティ
// EN: Utility to detect plain objects
const isRecord = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === 'object' && !Array.isArray(value);

export const isErrorResponse = (value: unknown): value is ErrorResponse =>
  isRecord(value) && typeof value.error === 'string';

// JP: エラーメッセージの優先順位を決定
// EN: Decide the error message to surface
const resolveErrorMessage = (
  data: unknown,
  fallback: string,
  preferErrorBody: boolean
): string => {
  if (preferErrorBody && isErrorResponse(data)) {
    return data.error;
  }
  /**
   * EN: Return a value from this scope.
   * JP: このスコープから値を返す。
   */
  return fallback;
};

// JP: JSON パース失敗時にフォールバックを返す
// EN: Return fallback when JSON parsing fails
const readJson = async <T>(
  response: Response,
  { fallback, throwOnParseError }: JsonRequestOptions<T>
): Promise<T> => {
  try {
    return (await response.json()) as T;
  } catch (error) {
    /**
     * EN: Branch logic based on a condition.
     * JP: 条件に応じて処理を分岐する。
     */
    if (throwOnParseError) {
      throw error;
    }
    /**
     * EN: Return a value from this scope.
     * JP: このスコープから値を返す。
     */
    return fallback ?? ({} as T);
  }
};

// JP: fetch の薄いラッパー（JSON パースとエラー処理）
// EN: Thin fetch wrapper with JSON parsing and error handling
export const requestJson = async <T>(
  input: RequestInfo | URL,
  init?: RequestInit,
  options: JsonRequestOptions<T> = {}
): Promise<{ data: T; response: Response }> => {
  const {
    fallback,
    errorMessage,
    preferErrorBody = true,
    throwOnNonOk = true,
    throwOnParseError = true,
    parseJson = true,
  } = options;

  /**
   * EN: Declare variable `response`.
   * JP: 変数 `response` を宣言する。
   */
  const response = await fetch(input, init);
  /**
   * EN: Declare variable `data`.
   * JP: 変数 `data` を宣言する。
   */
  const data = parseJson
    ? await readJson<T>(response, { fallback, throwOnParseError })
    : (fallback ?? ({} as T));

  /**
   * EN: Branch logic based on a condition.
   * JP: 条件に応じて処理を分岐する。
   */
  if (!response.ok && throwOnNonOk) {
    /**
     * EN: Declare variable `message`.
     * JP: 変数 `message` を宣言する。
     */
    const message = resolveErrorMessage(
      data,
      errorMessage || `Request failed (${response.status})`,
      preferErrorBody
    );
    throw new Error(message);
  }

  /**
   * EN: Return a value from this scope.
   * JP: このスコープから値を返す。
   */
  return { data, response };
};

// JP: GET 用の簡易ラッパー
// EN: Convenience wrapper for GET
export const getJson = async <T>(
  url: string,
  options?: JsonRequestOptions<T>
): Promise<{ data: T; response: Response }> => requestJson<T>(url, undefined, options);

// JP: POST（ボディなし）用の簡易ラッパー
// EN: Convenience wrapper for POST without body
export const post = async <T>(
  url: string,
  options?: JsonRequestOptions<T>
): Promise<{ data: T; response: Response }> =>
  requestJson<T>(url, { method: 'POST' }, options);

// JP: JSON ボディ付き POST の簡易ラッパー
// EN: Convenience wrapper for POST with JSON body
export const postJson = async <TResponse, TBody>(
  url: string,
  body: TBody,
  options?: JsonRequestOptions<TResponse>
): Promise<{ data: TResponse; response: Response }> =>
  requestJson<TResponse>(
    url,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
    options
  );
