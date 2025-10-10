// shared/infrastructure/http/index.ts
// HTTPクライアントの公開API

export { 
    apiGet, 
    apiPost, 
    apiGetBlob, 
    apiPostBlob,
    fetchWithTimeout,
    // ApiError is intentionally NOT re-exported here to avoid duplicate
    // symbol conflicts with shared/types where ApiError is also exported.
} from './httpClient';

// Re-export ApiError under an alias to avoid duplicate-export ambiguity
// while preserving compatibility for existing consumers importing from
// '@shared/infrastructure/http'. Prefer using '@shared/types' for the
// canonical ApiError type.
export { ApiError as ApiHttpError } from './httpClient';
