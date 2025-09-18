import axios from 'axios';

const baseURL = import.meta.env.VITE_RAG_API_BASE_URL || '/rag_api';

export const http = axios.create({
	baseURL,
	withCredentials: false,
});

export default http;
