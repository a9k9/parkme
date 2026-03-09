export type AuthTokens = {
  access: string;
  refresh: string;
};

const ACCESS_TOKEN_KEY = "parkme.access";
const REFRESH_TOKEN_KEY = "parkme.refresh";

export const AUTH_LOGIN_EVENT = "parkme:auth:login";
export const AUTH_LOGOUT_EVENT = "parkme:auth:logout";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(tokens: AuthTokens) {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
  window.dispatchEvent(new Event(AUTH_LOGIN_EVENT));
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.dispatchEvent(new Event(AUTH_LOGOUT_EVENT));
}

export function hasTokens(): boolean {
  return Boolean(getAccessToken());
}
