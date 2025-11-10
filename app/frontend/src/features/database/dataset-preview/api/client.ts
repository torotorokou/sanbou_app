/**
 * PreviewClient - HTTP クライアント
 */

export const PreviewClient = {
  async get(path: string, signal?: AbortSignal): Promise<unknown> {
    const res = await fetch(path, { signal });
    if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
    return res.json();
  },
};
