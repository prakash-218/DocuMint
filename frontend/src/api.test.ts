import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError } from './api';

function respond(status: number, body: unknown) {
  return vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('api', () => {
  it('posts JSON with the session cookie and returns the answer', async () => {
    const fetch = respond(200, { ok: true });
    vi.stubGlobal('fetch', fetch);
    await expect(api.post('/api/thing', { a: 1 })).resolves.toEqual({ ok: true });
    const [path, init] = fetch.mock.calls[0];
    expect(path).toBe('/api/thing');
    expect(init).toMatchObject({ method: 'POST', credentials: 'same-origin', body: '{"a":1}' });
    expect(init.headers).toMatchObject({ 'Content-Type': 'application/json', Accept: 'application/json' });
  });

  it("turns the server's refusal into an ApiError with its message", async () => {
    vi.stubGlobal('fetch', respond(403, { error: 'Your role is Sales: projects, quotations and customers only' }));
    const failure = api.get('/api/invoices');
    await expect(failure).rejects.toBeInstanceOf(ApiError);
    await expect(failure).rejects.toMatchObject({ status: 403, message: 'Your role is Sales: projects, quotations and customers only' });
  });
});
