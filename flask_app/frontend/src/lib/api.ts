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

const isRecord = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === 'object' && !Array.isArray(value);

export const isErrorResponse = (value: unknown): value is ErrorResponse =>
  isRecord(value) && typeof value.error === 'string';

const resolveErrorMessage = (
  data: unknown,
  fallback: string,
  preferErrorBody: boolean
): string => {
  if (preferErrorBody && isErrorResponse(data)) {
    return data.error;
  }
  return fallback;
};

const readJson = async <T>(
  response: Response,
  { fallback, throwOnParseError }: JsonRequestOptions<T>
): Promise<T> => {
  try {
    return (await response.json()) as T;
  } catch (error) {
    if (throwOnParseError) {
      throw error;
    }
    return fallback ?? ({} as T);
  }
};

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

  const response = await fetch(input, init);
  const data = parseJson
    ? await readJson<T>(response, { fallback, throwOnParseError })
    : (fallback ?? ({} as T));

  if (!response.ok && throwOnNonOk) {
    const message = resolveErrorMessage(
      data,
      errorMessage || `Request failed (${response.status})`,
      preferErrorBody
    );
    throw new Error(message);
  }

  return { data, response };
};

export const getJson = async <T>(
  url: string,
  options?: JsonRequestOptions<T>
): Promise<{ data: T; response: Response }> => requestJson<T>(url, undefined, options);

export const post = async <T>(
  url: string,
  options?: JsonRequestOptions<T>
): Promise<{ data: T; response: Response }> =>
  requestJson<T>(url, { method: 'POST' }, options);

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
