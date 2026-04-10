/**
 * api.js — Central API communication module for TaskFlow Pro.
 * Frontend is served by Flask on port 5000 — same origin, zero CORS issues.
 */

// If we are on Vercel (different origin than Render), we set this to the Render URL.
// If empty, it assumes the backend is on the same origin (e.g. served by Flask).
export const BASE_URL = ''; // Same origin — Flask serves both API and frontend

// ---------------------------------------------------------------------------
// Token storage (localStorage avoids cross-origin cookie issues in dev)
// ---------------------------------------------------------------------------
export function getToken() {
  return localStorage.getItem('tf_token');
}

export function setToken(token) {
  if (token) localStorage.setItem('tf_token', token);
}

export function clearToken() {
  localStorage.removeItem('tf_token');
}

// ---------------------------------------------------------------------------
// Toast helper (Toastify loaded from CDN)
// ---------------------------------------------------------------------------
export function showToast(message, type = 'info') {
  const colors = { info: '#1A56DB', error: '#EF4444', success: '#10B981' };
  Toastify({
    text: message,
    duration: 3500,
    gravity: 'top',
    position: 'right',
    style: { background: colors[type] ?? colors.info, borderRadius: '8px', fontFamily: 'Inter, sans-serif' },
    stopOnFocus: true,
  }).showToast();
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------
async function apiFetch(method, path, body = null, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const fetchOpts = { method, headers, cache: 'no-store' };
  if (body) fetchOpts.body = JSON.stringify(body);

  try {
    const res = await fetch(BASE_URL + path, fetchOpts);

    // Handle auth expiry
    if (res.status === 401 && !opts.silent) {
      clearToken();
      const isLoginPage = window.location.pathname.includes('index.html')
        || window.location.pathname === '/'
        || window.location.pathname.endsWith('/');
      if (!isLoginPage) {
        window.location.href = 'index.html';
        return;
      }
    }

    if (res.status === 403 && !opts.silent) {
      showToast('Access denied', 'error');
      return { ok: false, status: 403, data: {} };
    }

    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    if (!opts.silent) {
      showToast('Cannot reach the server. Make sure the backend is running on port 5000.', 'error');
    }
    return { ok: false, status: 0, data: {} };
  }
}

// ---------------------------------------------------------------------------
// Auth API
// ---------------------------------------------------------------------------
export const auth = {
  me: () => apiFetch('GET', '/api/auth/me', null, { silent: true }),

  async register(name, email, password) {
    const res = await apiFetch('POST', '/api/auth/register', { name, email, password });
    if (res?.ok && res.data?.token) setToken(res.data.token);
    return res;
  },

  async login(email, password) {
    const res = await apiFetch('POST', '/api/auth/login', { email, password });
    if (res?.ok && res.data?.token) setToken(res.data.token);
    return res;
  },

  logout() {
    clearToken();
    return apiFetch('POST', '/api/auth/logout');
  },
};

// ---------------------------------------------------------------------------
// Tasks API
// ---------------------------------------------------------------------------
export const tasks = {
  list(filters = {}) {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(filters).filter(([, v]) => v != null && v !== ''))
    ).toString();
    return apiFetch('GET', `/api/tasks${qs ? '?' + qs : ''}`);
  },

  create: (data) => apiFetch('POST', '/api/tasks', data),
  get: (id) => apiFetch('GET', `/api/tasks/${id}`),
  update: (id, data) => apiFetch('PUT', `/api/tasks/${id}`, data),
  delete: (id) => apiFetch('DELETE', `/api/tasks/${id}`),
  toggleComplete: (id) => apiFetch('PATCH', `/api/tasks/${id}/complete`),
  addPomodoro: (id) => apiFetch('PATCH', `/api/tasks/${id}/pomodoro`),
  analytics: () => apiFetch('GET', '/api/tasks/analytics'),
  suggest: (title) => apiFetch('POST', '/api/tasks/suggest', { title }),
};
