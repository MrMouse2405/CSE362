import { goto } from "$app/navigation";
import { browser } from "$app/environment";
import { apiFetch, setTokenGetter, setOnUnauthorized } from "$lib/api";

export interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  role: "student" | "teacher" | "admin";
}

class AuthState {
  #user = $state<User | null>(null);
  #token = $state<string | null>(null);
  #avatarUrl = $state<string | null>(null);
  #loading = $state(true); // start true — we always need to resolve initial state

  constructor() {
    if (browser) {
      // Wire up the api helper so it can read the token and react to 401s
      // without a circular import.
      setTokenGetter(() => this.#token);
      setOnUnauthorized(() => this.clearAuth());

      const storedToken = localStorage.getItem("token");
      if (storedToken) {
        this.#token = storedToken;
        this.loadUser(); // verifies the token is still valid
      } else {
        // No stored token — nothing to verify, mark loading complete.
        this.#loading = false;
      }
    } else {
      // SSR — nothing to load.
      this.#loading = false;
    }
  }

  /** Sync token to both reactive state and localStorage. */
  private set token(value: string | null) {
    this.#token = value;
    if (browser) {
      if (value) {
        localStorage.setItem("token", value);
      } else {
        localStorage.removeItem("token");
      }
    }
  }

  /** Clear all auth state without navigating (used by the 401 callback). */
  private clearAuth() {
    this.token = null;
    this.#user = null;
    if (this.#avatarUrl) {
      URL.revokeObjectURL(this.#avatarUrl);
      this.#avatarUrl = null;
    }
  }

  get token() {
    return this.#token;
  }

  get user() {
    return this.#user;
  }

  /** True only when we have *both* a token and a verified user object. */
  get isAuthenticated() {
    return !!this.#token && !!this.#user;
  }

  get isAdmin() {
    return this.#user?.role === "admin";
  }

  get isSuperuser() {
    return this.#user?.is_superuser === true;
  }

  /** A blob URL for the current user's avatar, or null if not loaded. */
  get avatarUrl() {
    return this.#avatarUrl;
  }

  /**
   * True while the initial token from localStorage is being verified.
   * The layout should show a loading state (or nothing) until this is false.
   */
  get isLoading() {
    return this.#loading;
  }

  /** Fetch the user's avatar SVG and store it as a blob URL. */
  private async loadAvatar() {
    try {
      const headers: HeadersInit = {};
      if (this.#token) {
        headers["Authorization"] = `Bearer ${this.#token}`;
      }
      const res = await fetch("/api/auth/avatar", { headers });
      if (!res.ok) return;
      const blob = await res.blob();
      this.#avatarUrl = URL.createObjectURL(blob);
    } catch {
      // Non-critical — the fallback initials will show instead.
    }
  }

  /** Verify the stored token by fetching the current user. */
  async loadUser() {
    this.#loading = true;
    try {
      this.#user = await apiFetch<User>("/api/auth/me");
      await this.loadAvatar();
    } catch {
      // Token invalid / expired — clean up.
      this.clearAuth();
    } finally {
      this.#loading = false;
    }
  }

  async login(email: string, password: string) {
    const params = new URLSearchParams();
    params.append("username", email);
    params.append("password", password);

    const data = await apiFetch<{ access_token: string }>("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params,
    });

    this.token = data.access_token;

    try {
      this.#user = await apiFetch<User>("/api/auth/me");
      await this.loadAvatar();
    } catch (error) {
      this.clearAuth();
      throw error;
    }
  }

  async register(email: string, password: string, name: string) {
    await apiFetch<User>("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, name }),
    });

    // Auto-login after successful registration
    await this.login(email, password);
  }

  logout() {
    this.clearAuth();
    goto("/login");
  }
}

export const auth = new AuthState();
