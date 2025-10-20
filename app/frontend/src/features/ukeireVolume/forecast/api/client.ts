/**
 * Ukeire Forecast API Client
 * HTTP通信を担当（fetch wrapper）
 */

export const UkeireForecastClient = {
  async get<T>(path: string, signal?: AbortSignal): Promise<T> {
    const res = await fetch(path, { signal, credentials: "include" });
    if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
    return res.json() as Promise<T>;
  },
};
