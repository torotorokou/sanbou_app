// src/types/api.ts
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
    hint?: string | null;

    constructor(
        message: string,
        code: string,
        httpStatus: number,
        hint?: string | null
    ) {
        super(message);
        this.code = code;
        this.httpStatus = httpStatus;
        this.hint = hint;
    }
}
