const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Request failed');
  }
  
  return response.json();
}

export const api = {
  health: () => fetchJson<{ status: string }>('/health'),
  
  emails: {
    list: (limit = 50) => fetchJson<import('./types').Email[]>(`/emails/?limit=${limit}`),
    get: (id: string) => fetchJson<import('./types').Email>(`/emails/${id}`),
    import: (limit?: number) => fetchJson<import('./types').Email[]>(`/emails/import${limit ? `?limit=${limit}` : ''}`, { method: 'POST' }),
  },
  
  classifications: {
    list: () => fetchJson<import('./types').Classification[]>('/classifications/'),
    get: (emailId: string) => fetchJson<import('./types').Classification>(`/classifications/${emailId}`),
    classify: (emailId: string) => fetchJson<import('./types').Classification>(`/classifications/${emailId}`, { method: 'POST' }),
  },
  
  drafts: {
    list: (status?: string) => fetchJson<import('./types').Draft[]>(`/drafts/${status ? `?status=${status}` : ''}`),
    pending: () => fetchJson<import('./types').Draft[]>('/drafts/pending'),
    get: (id: string) => fetchJson<import('./types').Draft>(`/drafts/${id}`),
    generate: (emailId: string) => fetchJson<import('./types').Draft>(`/drafts/generate/${emailId}`, { method: 'POST' }),
    update: (id: string, body: string, subject?: string) => 
      fetchJson<import('./types').Draft>(`/drafts/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ body, subject, editor: 'web-ui' }),
      }),
    approve: (id: string, approvedBy: string) =>
      fetchJson<import('./types').Draft>(`/drafts/${id}/approve`, {
        method: 'POST',
        body: JSON.stringify({ approved_by: approvedBy }),
      }),
    reject: (id: string, rejectedBy: string, reason?: string) =>
      fetchJson<import('./types').Draft>(`/drafts/${id}/reject`, {
        method: 'POST',
        body: JSON.stringify({ rejected_by: rejectedBy, reason }),
      }),
    send: (id: string) => fetchJson<{ status: string; outbox_id: string }>(`/drafts/${id}/send`, { method: 'POST' }),
    canSend: (id: string) => fetchJson<{ can_send: boolean; status: string; reason: string }>(`/drafts/${id}/can-send`),
  },
  
  triage: {
    processAll: (params?: { import_new?: boolean; generate_drafts?: boolean; limit?: number }) =>
      fetchJson<import('./types').TriageSummary>(`/triage/process-all?${new URLSearchParams(
        Object.entries(params || {}).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)])
      )}`, { method: 'POST' }),
    getQueue: () => fetchJson<import('./types').ReviewQueue>('/triage/queue'),
    getResult: (emailId: string) => fetchJson<{ email: import('./types').Email; classification: import('./types').Classification; draft: import('./types').Draft | null }>(`/triage/email/${emailId}`),
  },
  
  audit: {
    list: (limit = 100) => fetchJson<import('./types').AuditLog[]>(`/audit/?limit=${limit}`),
    forEntity: (type: string, id: string) => fetchJson<import('./types').AuditLog[]>(`/audit/entity/${type}/${id}`),
  },
};
