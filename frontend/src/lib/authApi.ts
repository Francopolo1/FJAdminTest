import { api } from "./api";
import type { AuthUser, LoginCredentials, RegisterPayload, RegisterResponse, TokenPair } from "../types";

export async function login(credentials: LoginCredentials): Promise<TokenPair> {
  const { data } = await api.post<TokenPair>("/api/auth/login/", {
    username: credentials.email,
    password: credentials.password,
  });
  return data;
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const { data } = await api.get<AuthUser>("/api/core/users/me/");
  return data;
}

export async function logout(refresh: string): Promise<void> {
  await api.post("/api/auth/logout/", { refresh });
}

export async function register(payload: RegisterPayload): Promise<RegisterResponse> {
  const { data } = await api.post<RegisterResponse>("/api/auth/register/", payload);
  return data;
}

export async function requestPasswordReset(email: string): Promise<{ detail: string }> {
  const { data } = await api.post<{ detail: string }>("/api/auth/password-reset/", { email });
  return data;
}

export async function confirmPasswordReset(uid: string, token: string, newPassword: string): Promise<{ detail: string }> {
  const { data } = await api.post<{ detail: string }>("/api/auth/password-reset/confirm/", {
    uid,
    token,
    new_password: newPassword,
  });
  return data;
}
