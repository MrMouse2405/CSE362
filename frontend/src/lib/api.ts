import { auth } from "$lib/state/auth.svelte";

export async function apiFetch(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers);
  if (auth.token) {
    headers.set("Authorization", `Bearer ${auth.token}`);
  }

  const response = await fetch(path, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = "API request failed";
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch (e) {
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
    return response.json();
  }

  return null;
}
