// The Flask JSON endpoints (blueprints/api_bp.py). Same session cookie as the pages; bodies always JSON.

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method,
    credentials: 'same-origin',
    headers: { Accept: 'application/json', ...(body === undefined ? {} : { 'Content-Type': 'application/json' }) },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(response.status, data.error || `The server said ${response.status}`);
  }
  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body: unknown) => request<T>('POST', path, body),
  patch: <T>(path: string, body: unknown) => request<T>('PATCH', path, body),
  del: <T>(path: string) => request<T>('DELETE', path, {}),     // an empty JSON body: the API takes nothing else
};

/** GET /api/me */
export interface Me {
  email: string;
  /** A built-in role, or custom: one of the organization's own (role_label is its name) */
  role: 'owner' | 'admin' | 'member' | 'viewer' | 'sales' | 'custom';
  role_label: string;
  org: { id: string; name: string };
  /** Every permission they have (permissions.py: quotes.read, projects.write, ...) */
  permissions: string[];
  /** The app's shorthand for them (permissions.flags) */
  can: { edit: boolean; edit_customers: boolean; manage: boolean; read_mail: boolean; quotations_only: boolean };
}
