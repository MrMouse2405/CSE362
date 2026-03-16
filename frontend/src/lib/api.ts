/**
 * API fetch helper.
 *
 * Provides a thin wrapper around `fetch` that:
 *  - Attaches the Bearer token (supplied via `setTokenGetter`)
 *  - Parses JSON responses
 *  - Normalises error handling
 *  - Calls an optional `onUnauthorized` hook on 401 responses so the auth
 *    layer can clear state without creating a circular import.
 */

let getToken: (() => string | null) | null = null;
let onUnauthorized: (() => void) | null = null;

export function setTokenGetter(fn: () => string | null) {
  getToken = fn;
}

export function setOnUnauthorized(fn: () => void) {
  onUnauthorized = fn;
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);

  const token = getToken?.();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(path, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    onUnauthorized?.();
  }

  if (!response.ok) {
    let errorDetail = "API request failed";
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch {
      // Ignore JSON parse error
    }
    throw new Error(
      typeof errorDetail === "string"
        ? errorDetail
        : JSON.stringify(errorDetail),
    );
  }

  // Check if the response has content before parsing JSON
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return response.json() as Promise<T>;
  }

  return null as T;
}
