const DEFAULT_API_BASE_URL = '';

export class ApiError extends Error {
  status?: number;
  details?: unknown;

  constructor(message: string, options?: { status?: number; details?: unknown }) {
    super(message);
    this.name = 'ApiError';
    this.status = options?.status;
    this.details = options?.details;
  }
}

function normalizeBaseUrl(baseUrl: string) {
  return baseUrl.replace(/\/+$/, '');
}

function joinUrl(baseUrl: string, path: string) {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  if (!path.startsWith('/')) {
    return `${baseUrl}/${path}`;
  }

  return `${baseUrl}${path}`;
}

function getConfiguredApiBaseUrl() {
  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
  return normalizeBaseUrl(configuredBaseUrl || DEFAULT_API_BASE_URL);
}

async function parseResponseBody(response: Response) {
  const contentType = response.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    return response.json();
  }

  const text = await response.text();
  return text ? { message: text } : null;
}

function getErrorMessage(status: number, body: unknown) {
  if (!body) {
    return `A API respondeu com erro ${status}.`;
  }

  if (typeof body === 'string') {
    return body;
  }

  if (typeof body === 'object') {
    const maybeMessage = body as Record<string, unknown>;
    const detail =
      maybeMessage.detail ??
      maybeMessage.message ??
      maybeMessage.error ??
      maybeMessage.title;

    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
  }

  return `A API respondeu com erro ${status}.`;
}

export async function httpRequest<TResponse>(
  path: string,
  init?: RequestInit,
): Promise<TResponse> {
  const apiBaseUrl = getConfiguredApiBaseUrl();

  let response: Response;

  try {
    response = await fetch(joinUrl(apiBaseUrl, path), {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...(init?.headers ?? {}),
      },
    });
  } catch (error) {
    throw new ApiError(
      `Nao foi possivel conectar a API do copiloto tecnico em ${apiBaseUrl}. Verifique se o backend Python esta no ar e se VITE_API_BASE_URL esta correto.`,
      { details: error },
    );
  }

  const body = await parseResponseBody(response);

  if (!response.ok) {
    throw new ApiError(getErrorMessage(response.status, body), {
      status: response.status,
      details: body,
    });
  }

  return body as TResponse;
}

export const httpClient = {
  get baseUrl() {
    return getConfiguredApiBaseUrl();
  },
  get<TResponse>(path: string, init?: Omit<RequestInit, 'method'>) {
    return httpRequest<TResponse>(path, { ...init, method: 'GET' });
  },
  post<TResponse>(path: string, body?: unknown, init?: Omit<RequestInit, 'body' | 'method'>) {
    return httpRequest<TResponse>(path, {
      ...init,
      method: 'POST',
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  },
};
