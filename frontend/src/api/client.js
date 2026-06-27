// In dev, Vite proxies /api to localhost:5000, so relative path works.
// In production, VITE_API_BASE_URL points to the Render backend URL.
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '') + '/api';

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...options,
  });
  if (res.status === 401) {
    throw new Error('UNAUTHORIZED');
  }
  return res.json();
}

export async function getAuthStatus() {
  try {
    return await apiFetch('/auth/status');
  } catch {
    return { authenticated: false };
  }
}

export async function logout() {
  return apiFetch('/auth/logout', { method: 'POST' });
}

export async function getSessions() {
  return apiFetch('/sessions');
}

export async function createSession() {
  return apiFetch('/sessions', { method: 'POST' });
}

export async function deleteSession(sessionId) {
  return apiFetch(`/chat/${sessionId}`, { method: 'DELETE' });
}

export async function getChat(sessionId) {
  return apiFetch(`/chat/${sessionId}`);
}

export async function sendMessage(sessionId, message, imageFile) {
  const formData = new FormData();
  formData.append('message', message);
  if (imageFile) formData.append('image', imageFile);

  return apiFetch(`/chat/${sessionId}`, {
    method: 'POST',
    body: formData,
  });
}

export async function getUserStats() {
  return apiFetch('/user/stats');
}

export async function getUpcomingEvents() {
  return apiFetch('/calendar/upcoming');
}

export async function getTodayTasks() {
  return apiFetch('/tasks/today');
}
