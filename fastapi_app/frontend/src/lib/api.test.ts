import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  getJson,
  isErrorResponse,
  post,
  postJson,
  requestJson,
} from './api';

type MockResponseOptions = {
  ok: boolean;
  status: number;
  data?: unknown;
  parseError?: Error;
};

const createMockResponse = ({
  ok,
  status,
  data,
  parseError,
}: MockResponseOptions): Response =>
  ({
    ok,
    status,
    json: parseError
      ? vi.fn(async () => {
          throw parseError;
        })
      : vi.fn(async () => data),
  } as unknown as Response);

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('isErrorResponse', () => {
  it('returns true only for objects with an error string', () => {
    expect(isErrorResponse({ error: 'bad request' })).toBe(true);
    expect(isErrorResponse({ error: 1 })).toBe(false);
    expect(isErrorResponse('error')).toBe(false);
    expect(isErrorResponse(null)).toBe(false);
  });
});

describe('requestJson', () => {
  it('returns parsed data on successful response', async () => {
    const response = createMockResponse({ ok: true, status: 200, data: { value: 1 } });
    const fetchMock = vi.fn(async () => response);
    vi.stubGlobal('fetch', fetchMock);

    const result = await requestJson<{ value: number }>('/api/test');

    expect(result.data).toEqual({ value: 1 });
    expect(result.response).toBe(response);
    expect(fetchMock).toHaveBeenCalledWith('/api/test', undefined);
  });

  it('throws with error body message for non-ok responses by default', async () => {
    const response = createMockResponse({
      ok: false,
      status: 400,
      data: { error: 'validation failed' },
    });
    vi.stubGlobal('fetch', vi.fn(async () => response));

    await expect(requestJson('/api/test')).rejects.toThrow('validation failed');
  });

  it('uses fallback error message when preferErrorBody is false', async () => {
    const response = createMockResponse({
      ok: false,
      status: 500,
      data: { error: 'internal detail' },
    });
    vi.stubGlobal('fetch', vi.fn(async () => response));

    await expect(
      requestJson('/api/test', undefined, {
        preferErrorBody: false,
        errorMessage: 'custom message',
      })
    ).rejects.toThrow('custom message');
  });

  it('returns fallback when JSON parsing fails and throwOnParseError is false', async () => {
    const response = createMockResponse({
      ok: true,
      status: 200,
      parseError: new Error('invalid json'),
    });
    vi.stubGlobal('fetch', vi.fn(async () => response));

    const result = await requestJson<{ fallback: boolean }>('/api/test', undefined, {
      throwOnParseError: false,
      fallback: { fallback: true },
    });

    expect(result.data).toEqual({ fallback: true });
  });

  it('throws parse error when throwOnParseError is true', async () => {
    const response = createMockResponse({
      ok: true,
      status: 200,
      parseError: new Error('invalid json'),
    });
    vi.stubGlobal('fetch', vi.fn(async () => response));

    await expect(
      requestJson('/api/test', undefined, {
        throwOnParseError: true,
      })
    ).rejects.toThrow('invalid json');
  });

  it('skips JSON parsing when parseJson is false and uses fallback', async () => {
    const response = createMockResponse({
      ok: true,
      status: 200,
      data: { ignored: true },
    });
    vi.stubGlobal('fetch', vi.fn(async () => response));

    const result = await requestJson('/api/test', undefined, {
      parseJson: false,
      fallback: { parsed: false },
    });

    expect(result.data).toEqual({ parsed: false });
  });
});

describe('helper wrappers', () => {
  it('calls GET and POST wrappers with expected methods and body', async () => {
    const response = createMockResponse({ ok: true, status: 200, data: { ok: true } });
    const fetchMock = vi.fn(async () => response);
    vi.stubGlobal('fetch', fetchMock);

    await getJson<{ ok: boolean }>('/api/get');
    await post<{ ok: boolean }>('/api/post');
    await postJson<{ ok: boolean }, { q: string }>('/api/post-json', { q: 'hello' });

    expect(fetchMock).toHaveBeenNthCalledWith(1, '/api/get', undefined);
    expect(fetchMock).toHaveBeenNthCalledWith(2, '/api/post', { method: 'POST' });
    expect(fetchMock).toHaveBeenNthCalledWith(3, '/api/post-json', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ q: 'hello' }),
    });
  });
});
