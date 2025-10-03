// Central service http client implementation entry.
// Implementation lives in `httpClient_impl.ts` to keep this file
// small and clear; exported names are the public API.
export { apiGet, apiPost, apiGetBlob, apiPostBlob } from './httpClient_impl';

// Backwards-compat: also export as default (some code may import default)
const _default = {
	apiGet: (undefined as unknown) as unknown,
	apiPost: (undefined as unknown) as unknown,
	apiGetBlob: (undefined as unknown) as unknown,
	apiPostBlob: (undefined as unknown) as unknown,
};
export default _default;
