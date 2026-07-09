// Envelope-aware API client for JapanCareer.jp
const BASE = import.meta.env.VITE_API_BASE || "/api/v1";

let accessToken = localStorage.getItem("jc_access") || null;
let refreshToken = localStorage.getItem("jc_refresh") || null;

export function setTokens(tokens) {
  accessToken = tokens?.access || null;
  refreshToken = tokens?.refresh || null;
  if (accessToken) localStorage.setItem("jc_access", accessToken);
  else localStorage.removeItem("jc_access");
  if (refreshToken) localStorage.setItem("jc_refresh", refreshToken);
  else localStorage.removeItem("jc_refresh");
}
export function clearTokens() { setTokens(null); }
export function hasToken() { return !!accessToken; }

async function request(path, { method = "GET", body, auth = true, isForm = false } = {}) {
  const headers = {};
  if (!isForm) headers["Content-Type"] = "application/json";
  if (auth && accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

  let res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: isForm ? body : body ? JSON.stringify(body) : undefined,
  });

  // transparent refresh on 401
  if (res.status === 401 && refreshToken && auth) {
    const r = await fetch(`${BASE}/auth/refresh-token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
    });
    if (r.ok) {
      const data = await r.json();
      const newAccess = data?.data?.access || data?.access;
      if (newAccess) {
        setTokens({ access: newAccess, refresh: refreshToken });
        headers["Authorization"] = `Bearer ${newAccess}`;
        res = await fetch(`${BASE}${path}`, {
          method, headers,
          body: isForm ? body : body ? JSON.stringify(body) : undefined,
        });
      }
    } else {
      clearTokens();
    }
  }

  let payload = null;
  try { payload = await res.json(); } catch { payload = null; }

  if (!res.ok) {
    const message = payload?.message || `Request failed (${res.status})`;
    const err = new Error(message);
    err.status = res.status;
    err.errors = payload?.errors || null;
    throw err;
  }
  return payload;
}

export const api = {
  get: (p, opts) => request(p, { ...opts, method: "GET" }),
  post: (p, body, opts) => request(p, { ...opts, method: "POST", body }),
  put: (p, body, opts) => request(p, { ...opts, method: "PUT", body }),
  del: (p, opts) => request(p, { ...opts, method: "DELETE" }),
  postForm: (p, formData, opts) => request(p, { ...opts, method: "POST", body: formData, isForm: true }),
  raw: request,
};
