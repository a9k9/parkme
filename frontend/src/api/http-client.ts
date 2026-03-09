import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from "@/lib/auth";

export type HttpClientConfig = {
  baseUrl?: string;
  headers?: HeadersInit;
  signal?: AbortSignal;
  retryOnUnauthorized?: boolean;
};

type HttpClientResponse<T> = {
  data: T;
  status: number;
};

const DEFAULT_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const REFRESH_ENDPOINT = "/api/auth/token/refresh/";

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return (await response.json()) as T;
  }

  return (await response.text()) as T;
}

async function refreshAccessToken(baseUrl: string, refreshToken: string) {
  const response = await fetch(`${baseUrl}${REFRESH_ENDPOINT}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ refresh: refreshToken }),
  });

  if (!response.ok) {
    return null;
  }

  const data = (await parseResponse<{ access: string }>(response)) ?? null;
  return data?.access ? data.access : null;
}

export async function httpClient<T>(
  url: string,
  options: RequestInit = {},
  config: HttpClientConfig = {},
): Promise<HttpClientResponse<T>> {
  const baseUrl = config.baseUrl ?? DEFAULT_BASE_URL;
  const headers = new Headers(config.headers ?? {});

  if (options.headers) {
    const optionHeaders = new Headers(options.headers);
    optionHeaders.forEach((value, key) => headers.set(key, value));
  }

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const accessToken = getAccessToken();
  if (accessToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(`${baseUrl}${url}`, {
    ...options,
    headers,
    signal: config.signal ?? options.signal,
  });

  if (response.status === 401 && config.retryOnUnauthorized !== false) {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      const nextAccessToken = await refreshAccessToken(baseUrl, refreshToken);
      if (nextAccessToken) {
        setTokens({ access: nextAccessToken, refresh: refreshToken });
        const retryHeaders = new Headers(headers);
        retryHeaders.set("Authorization", `Bearer ${nextAccessToken}`);
        return httpClient<T>(
          url,
          { ...options, headers: retryHeaders },
          { ...config, retryOnUnauthorized: false },
        );
      }
      clearTokens();
    }
  }

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || response.statusText);
  }

  const data = await parseResponse<T>(response);
  return { data, status: response.status };
}
