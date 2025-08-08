// /app/src/services/interactiveApiService.ts

/**
 * インタラクティブモード専用API通信サービス
 *
 * 🎯 目的：
 * - インタラクティブ帳簿生成の複数段階API通信を管理
 * - 初期化→ユーザー入力→完了の流れを統一インターフェースで提供
 * - セッション管理とエラーハンドリングを統合
 */

import type {
    InteractiveApiRequest,
    InteractiveApiResponse,
    SessionData,
    UserSelections,
    ProcessData,
    InteractiveStep,
} from '../pages/types/interactiveMode';
import { INTERACTIVE_STEPS } from '../pages/types/interactiveMode';
import type { ReportKey } from '../constants/reportConfig';

// ==============================
// 🌐 API エンドポイント定義
// ==============================

const INTERACTIVE_ENDPOINTS = {
    START: '/ledger_api/report/interactive/start',
    UPDATE: '/ledger_api/report/interactive/update',
    COMPLETE: '/ledger_api/report/interactive/complete',
    STATUS: '/ledger_api/report/interactive/status',
} as const;

// ==============================
// 🔧 型定義
// ==============================

export interface InteractiveSessionInfo {
    sessionId: string;
    reportKey: ReportKey;
    currentStep: InteractiveStep;
    sessionData: SessionData;
    expiresAt: string;
}

export interface InteractiveStartRequest {
    reportKey: ReportKey;
    csvFiles: Record<string, File>;
    options?: Record<string, unknown>;
}

export interface InteractiveUpdateRequest {
    sessionId: string;
    userInput: UserSelections;
    currentStep: InteractiveStep;
}

export interface InteractiveCompleteRequest {
    sessionId: string;
    finalInput?: UserSelections;
}

export interface InteractiveApiError {
    code: string;
    message: string;
    details?: Record<string, unknown>;
}

// ==============================
// 🚀 インタラクティブAPIサービスクラス
// ==============================

export class InteractiveApiService {
    private static instance: InteractiveApiService;
    private activeSessions: Map<string, InteractiveSessionInfo> = new Map();

    // Singleton パターン
    static getInstance(): InteractiveApiService {
        if (!InteractiveApiService.instance) {
            InteractiveApiService.instance = new InteractiveApiService();
        }
        return InteractiveApiService.instance;
    }

    /**
     * ステップ1: インタラクティブ処理の初期化
     */
    async startInteractiveProcess(request: InteractiveStartRequest): Promise<{
        sessionInfo: InteractiveSessionInfo;
        nextStep: number;
        interactions?: unknown[];
        initialData?: ProcessData;
    }> {
        try {
            const formData = new FormData();

            // CSVファイルをformDataに追加
            Object.entries(request.csvFiles).forEach(([key, file]) => {
                if (file) {
                    const englishKey = this.convertLabelToEnglishKey(key);
                    formData.append(englishKey, file);
                }
            });

            formData.append('report_key', request.reportKey);
            if (request.options) {
                formData.append('options', JSON.stringify(request.options));
            }

            const response = await fetch(INTERACTIVE_ENDPOINTS.START, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw await this.createApiError(response);
            }

            const responseData: InteractiveApiResponse = await response.json();

            if (responseData.status === 'error') {
                throw new Error(
                    responseData.error || 'Interactive process start failed'
                );
            }

            // セッション情報を作成・保存
            const sessionInfo: InteractiveSessionInfo = {
                sessionId: this.generateSessionId(),
                reportKey: request.reportKey,
                currentStep:
                    (responseData.nextStep as InteractiveStep) ||
                    INTERACTIVE_STEPS.INITIAL,
                sessionData: responseData.sessionData || {},
                expiresAt: new Date(Date.now() + 30 * 60 * 1000).toISOString(), // 30分後
            };

            this.activeSessions.set(sessionInfo.sessionId, sessionInfo);

            return {
                sessionInfo,
                nextStep: responseData.nextStep || 0,
                interactions: responseData.interactions,
                initialData: responseData.data,
            };
        } catch (error) {
            console.error('Interactive start process failed:', error);
            throw error;
        }
    }

    /**
     * ステップ2: ユーザー入力の送信と次ステップの取得
     */
    async updateInteractiveProcess(request: InteractiveUpdateRequest): Promise<{
        nextStep: number;
        interactions?: unknown[];
        data?: ProcessData;
        isComplete: boolean;
    }> {
        try {
            const sessionInfo = this.activeSessions.get(request.sessionId);
            if (!sessionInfo) {
                throw new Error('Session not found or expired');
            }

            const apiRequest: InteractiveApiRequest = {
                action: 'update',
                reportKey: sessionInfo.reportKey,
                sessionData: sessionInfo.sessionData,
                userInput: request.userInput,
                currentStep: request.currentStep,
            };

            const response = await fetch(INTERACTIVE_ENDPOINTS.UPDATE, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(apiRequest),
            });

            if (!response.ok) {
                throw await this.createApiError(response);
            }

            const responseData: InteractiveApiResponse = await response.json();

            if (responseData.status === 'error') {
                throw new Error(
                    responseData.error || 'Interactive process update failed'
                );
            }

            // セッション情報を更新
            if (responseData.sessionData) {
                sessionInfo.sessionData = {
                    ...sessionInfo.sessionData,
                    ...responseData.sessionData,
                };
                sessionInfo.currentStep =
                    (responseData.nextStep as InteractiveStep) ||
                    sessionInfo.currentStep;
                this.activeSessions.set(request.sessionId, sessionInfo);
            }

            return {
                nextStep: responseData.nextStep || sessionInfo.currentStep,
                interactions: responseData.interactions,
                data: responseData.data,
                isComplete:
                    responseData.status === 'success' && !responseData.nextStep,
            };
        } catch (error) {
            console.error('Interactive update process failed:', error);
            throw error;
        }
    }

    /**
     * ステップ3: インタラクティブ処理の完了
     */
    async completeInteractiveProcess(
        request: InteractiveCompleteRequest
    ): Promise<{
        downloadUrl?: string;
        fileName?: string;
        previewUrl?: string;
        resultData?: ProcessData;
    }> {
        try {
            const sessionInfo = this.activeSessions.get(request.sessionId);
            if (!sessionInfo) {
                throw new Error('Session not found or expired');
            }

            const apiRequest: InteractiveApiRequest = {
                action: 'complete',
                reportKey: sessionInfo.reportKey,
                sessionData: sessionInfo.sessionData,
                userInput: request.finalInput,
                currentStep: sessionInfo.currentStep,
            };

            const response = await fetch(INTERACTIVE_ENDPOINTS.COMPLETE, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(apiRequest),
            });

            if (!response.ok) {
                throw await this.createApiError(response);
            }

            // レスポンスがファイル（blob）の場合
            const contentType = response.headers.get('content-type');
            if (contentType && !contentType.includes('application/json')) {
                const blob = await response.blob();
                const fileName = this.extractFileName(response);
                const downloadUrl = window.URL.createObjectURL(blob);

                // セッションを清理
                this.activeSessions.delete(request.sessionId);

                return {
                    downloadUrl,
                    fileName,
                };
            }

            // JSONレスポンスの場合
            const responseData: InteractiveApiResponse = await response.json();

            if (responseData.status === 'error') {
                throw new Error(
                    responseData.error ||
                        'Interactive process completion failed'
                );
            }

            // セッションを清理
            this.activeSessions.delete(request.sessionId);

            return {
                downloadUrl:
                    typeof responseData.data === 'object' &&
                    responseData.data &&
                    'downloadUrl' in responseData.data
                        ? String(responseData.data.downloadUrl)
                        : undefined,
                fileName:
                    typeof responseData.data === 'object' &&
                    responseData.data &&
                    'fileName' in responseData.data
                        ? String(responseData.data.fileName)
                        : undefined,
                previewUrl:
                    typeof responseData.data === 'object' &&
                    responseData.data &&
                    'previewUrl' in responseData.data
                        ? String(responseData.data.previewUrl)
                        : undefined,
                resultData: responseData.data,
            };
        } catch (error) {
            console.error('Interactive complete process failed:', error);
            throw error;
        }
    }

    /**
     * セッション情報の取得
     */
    getSessionInfo(sessionId: string): InteractiveSessionInfo | undefined {
        return this.activeSessions.get(sessionId);
    }

    /**
     * セッションの削除
     */
    clearSession(sessionId: string): void {
        this.activeSessions.delete(sessionId);
    }

    // ==============================
    // 🔧 プライベートヘルパーメソッド
    // ==============================

    private generateSessionId(): string {
        return `interactive_${Date.now()}_${Math.random()
            .toString(36)
            .substr(2, 9)}`;
    }

    private convertLabelToEnglishKey(label: string): string {
        const labelToEnglishKey: Record<string, string> = {
            出荷一覧: 'shipment',
            受入一覧: 'receive',
            ヤード一覧: 'yard',
        };
        return labelToEnglishKey[label] || label;
    }

    private extractFileName(response: Response): string {
        const contentDisposition = response.headers.get('content-disposition');
        if (contentDisposition) {
            const filenameMatch =
                contentDisposition.match(/filename="?([^"]+)"?/);
            if (filenameMatch) {
                return filenameMatch[1];
            }
        }
        return `interactive_report_${Date.now()}.xlsx`;
    }

    private async createApiError(response: Response): Promise<Error> {
        let errorMessage = `API request failed: ${response.status} ${response.statusText}`;

        try {
            const errorData = await response.json();
            if (errorData.message) {
                errorMessage = errorData.message;
            } else if (errorData.error) {
                errorMessage = errorData.error;
            }
        } catch {
            // JSONパースに失敗した場合はデフォルトメッセージを使用
        }

        return new Error(errorMessage);
    }
}

// ==============================
// 🎯 便利な関数エクスポート
// ==============================

/**
 * インタラクティブAPIサービスのインスタンスを取得
 */
export const getInteractiveApiService = (): InteractiveApiService => {
    return InteractiveApiService.getInstance();
};
