const API_BASE = '/api/v1'

async function fetchJson(path: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`)
  return res.json()
}

export const api = {
  runs: {
    list: (params?: Record<string, string | number>) => {
      const qs = params ? '?' + new URLSearchParams(params as Record<string, string>).toString() : ''
      return fetchJson(`/runs${qs}`)
    },
    get: (id: string) => fetchJson(`/runs/${id}`),
    delete: (id: string) => fetchJson(`/runs/${id}`, { method: 'DELETE' }),
  },
  projects: {
    list: () => fetchJson('/projects'),
  },
  playground: {
    models: () => fetchJson('/playground/models'),
    completion: (body: object) => fetchJson('/playground/completion', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  },
  deployments: {
    list: () => fetchJson('/deployments'),
    get: (id: string) => fetchJson(`/deployments/${id}`),
    create: (body: object) => fetchJson('/deployments', { method: 'POST', body: JSON.stringify(body) }),
    update: (id: string, body: object) => fetchJson(`/deployments/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    delete: (id: string) => fetchJson(`/deployments/${id}`, { method: 'DELETE' }),
    start: (id: string) => fetchJson(`/deployments/${id}/start`, { method: 'POST' }),
    stop: (id: string) => fetchJson(`/deployments/${id}/stop`, { method: 'POST' }),
    logs: (id: string) => fetchJson(`/deployments/${id}/logs`),
  },
}
