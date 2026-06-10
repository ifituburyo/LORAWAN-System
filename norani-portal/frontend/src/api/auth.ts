import { api } from "./client";
import type { TokenResponse, User } from "./types";

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await api.post<TokenResponse>("/auth/login", { email, password });
  return res.data;
}

export async function logout(): Promise<void> {
  try {
    await api.post("/auth/logout");
  } catch {
    // Ignore — we clear local state regardless
  }
}

export async function getCurrentUser(): Promise<User> {
  const res = await api.get<User>("/auth/me");
  return res.data;
}
