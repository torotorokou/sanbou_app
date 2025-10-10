export type ApiResponse<T> = {
    status: 'success' | 'error';
    code: string;
    detail: string;
    result?: T | null;
    hint?: string | null;
};

export class ApiError extends Error {
    code: string;
    httpStatus: number;
    userMessage: string;
    title?: string;
    traceId?: string;

    // constructor aligned with http client usage: (code, httpStatus, userMessage, title?, traceId?)
    constructor(
        code: string,
        httpStatus: number,
        userMessage: string,
        title?: string,
        traceId?: string
    ) {
        super(userMessage);
        this.name = 'ApiError';
        this.code = code;
        this.httpStatus = httpStatus;
        this.userMessage = userMessage;
        this.title = title;
        this.traceId = traceId;
    }
}
