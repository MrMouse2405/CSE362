import { goto } from "$app/navigation";
import { browser } from "$app/environment";
import { apiFetch } from "$lib/api";

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  role: "student" | "teacher" | "admin";
}

class AuthState {
  // 1. Make state private to prevent arbitrary external mutations
  #user = $state<User | null>(null);
  #token = $state<string | null>(null);

  constructor() {
    // 2. Use SvelteKit's 'browser' flag for SSR safety
    if (browser) {
      this.#token = localStorage.getItem("token");
      if (this.#token) {
        this.loadUser();
      }
    }
  }

  // 3. Use a getter/setter to replace the $effect.
  // Every time `this.token = ...` is called, localStorage automatically syncs.
  get token() {
    return this.#token;
  }

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

  // Expose user as a read-only getter to the outside world
  get user() {
    return this.#user;
  }

  get isAuthenticated() {
    return !!this.#token;
  }

  get isAdmin() {
    return this.#user?.role === "admin";
  }

  async loadUser() {
    try {
      this.#user = await apiFetch("/api/auth/me");
    } catch {
      // If fetching the user fails (e.g., token expired), clear everything out
      this.token = null;
      this.#user = null;
    }
  }

  async login(email: string, password: string) {
    const params = new URLSearchParams();
    params.append("username", email);
    params.append("password", password);

    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: params,
    });

    if (!res.ok) {
      let errorDetail = "Login failed";
      try {
        const errorData = await res.json();
        errorDetail = errorData.detail || errorDetail;
      } catch (e) {
        // ignore JSON parse errors
      }
      throw new Error(
        typeof errorDetail === "string"
          ? errorDetail
          : JSON.stringify(errorDetail),
      );
    }

    const data = await res.json();

    // Setting this will now automatically update localStorage via the setter
    this.token = data.access_token;

    try {
      this.#user = await apiFetch("/api/auth/me");
    } catch (error) {
      this.token = null;
      throw error;
    }
  }

  logout() {
    this.token = null;
    this.#user = null;
    goto("/login");
  }
}

export const auth = new AuthState();
