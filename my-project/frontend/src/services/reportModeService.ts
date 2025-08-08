// /app/src/services/reportModeService.ts

/**
 * レポートモード管理サービス
 * 
 * 🎯 SOLID原則の適用：
 * - Single Responsibility: モード判定と処理分岐のみを担当
 * - Open/Closed: 新しいモード追加時に既存コードを変更せずに拡張可能
 * - Liskov Substitution: インターフェースに基づく実装の置換が可能
 * - Interface S    public async continueInteractiveProcess(
        userInput: Record<string, unknown>,
        callbacks: ReportCallbacks
    ): Promise<InteractiveResult> {
        // インタラクティブ処理の継続ロジック
        // UIコンポーネントから呼び出される
        callbacks.onProgress?.(this.currentState.currentStep + 1);
        
        // TODO: 実際のAPI呼び出しとステップ処理を実装
        // userInputを使用した処理をここに実装
        console.log('User input received:', userInput);
        
        return {
            success: true,
            resultType: 'excel',
        };
    }ードに特化したインターフェースを提供
 * - Dependency Inversion: 抽象に依存し、具象に依存しない
 */

import { 
    getReportModeInfo, 
    getApiEndpointByReportKey, 
    type ReportKey,
    type ReportModeInfo,
    REPORT_GENERATION_MODES
} from '../pages/types/reportMode';

import type { 
    InteractiveProcessState,
    InteractiveApiRequest,
    InteractiveApiResponse,
    InteractiveResult 
} from '../pages/types/interactiveMode';

// ==============================
// 🔧 抽象インターフェース定義
// ==============================

/**
 * レポート生成処理の抽象インターフェース
 * （Dependency Inversion Principle）
 */
export interface IReportProcessor {
    processReport(
        csvFiles: Record<string, File>,
        reportKey: ReportKey,
        callbacks: ReportCallbacks
    ): Promise<ReportProcessResult>;
}

/**
 * レポート処理のコールバック
 */
export interface ReportCallbacks {
    onStart: () => void;
    onProgress?: (step: number, message?: string) => void;
    onComplete: () => void;
    onError: (error: string) => void;
}

/**
 * レポート処理結果
 */
export interface ReportProcessResult {
    success: boolean;
    mode: string;
    downloadUrl?: string;
    fileName?: string;
    previewUrl?: string;
    error?: string;
}

// ==============================
// 🤖 自動モード処理クラス
// ==============================

/**
 * 自動レポート生成処理
 * （Single Responsibility Principle）
 */
export class AutoReportProcessor implements IReportProcessor {
    async processReport(
        csvFiles: Record<string, File>,
        reportKey: ReportKey,
        callbacks: ReportCallbacks
    ): Promise<ReportProcessResult> {
        try {
            callbacks.onStart();

            // 従来の自動生成API呼び出し
            const apiEndpoint = getApiEndpointByReportKey(reportKey);
            const formData = new FormData();

            // CSVファイルをformDataに追加
            const labelToEnglishKey: Record<string, string> = {
                出荷一覧: 'shipment',
                受入一覧: 'receive',
                ヤード一覧: 'yard',
            };

            Object.keys(csvFiles).forEach((label) => {
                const fileObj = csvFiles[label];
                if (fileObj) {
                    const englishKey = labelToEnglishKey[label] || label;
                    formData.append(englishKey, fileObj);
                }
            });
            formData.append('report_key', reportKey);

            const response = await fetch(apiEndpoint, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`API request failed: ${response.statusText}`);
            }

            const blob = await response.blob();
            const fileName = this.extractFileName(response);
            const downloadUrl = window.URL.createObjectURL(blob);

            callbacks.onComplete();

            return {
                success: true,
                mode: 'auto',
                downloadUrl,
                fileName,
            };

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            callbacks.onError(errorMessage);
            
            return {
                success: false,
                mode: 'auto',
                error: errorMessage,
            };
        }
    }

    private extractFileName(response: Response): string {
        const contentDisposition = response.headers.get('content-disposition');
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
            if (filenameMatch) {
                return filenameMatch[1];
            }
        }
        return `report_${Date.now()}.xlsx`;
    }
}

// ==============================
// 🎮 インタラクティブモード処理クラス
// ==============================

/**
 * インタラクティブレポート生成処理
 * （Single Responsibility Principle）
 */
export class InteractiveReportProcessor implements IReportProcessor {
    private currentState: InteractiveProcessState = {
        currentStep: -1,
        isLoading: false,
    };

    async processReport(
        csvFiles: Record<string, File>,
        reportKey: ReportKey,
        callbacks: ReportCallbacks
    ): Promise<ReportProcessResult> {
        try {
            callbacks.onStart();

            // インタラクティブ処理の開始
            const result = await this.startInteractiveProcess(csvFiles, reportKey, callbacks);
            
            callbacks.onComplete();
            
            return {
                success: true,
                mode: 'interactive',
                ...result,
            };

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            callbacks.onError(errorMessage);
            
            return {
                success: false,
                mode: 'interactive',
                error: errorMessage,
            };
        }
    }

    private async startInteractiveProcess(
        csvFiles: Record<string, File>,
        reportKey: ReportKey,
        callbacks: ReportCallbacks
    ): Promise<Partial<ReportProcessResult>> {
        const apiEndpoint = getApiEndpointByReportKey(reportKey);

        callbacks.onProgress?.(0, 'Starting interactive process...');

        const request: InteractiveApiRequest = {
            action: 'start',
            reportKey,
            csvFiles,
            currentStep: this.currentState.currentStep,
        };

        const response = await fetch(apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`Interactive API request failed: ${response.statusText}`);
        }

        const responseData: InteractiveApiResponse = await response.json();

        if (responseData.status === 'error') {
            throw new Error(responseData.error || 'Interactive process failed');
        }

        // ここではUIコンポーネント側でインタラクティブ処理を継続
        // この関数は初期処理のみを担当
        return {
            previewUrl: typeof responseData.data === 'object' && 
                       responseData.data && 
                       'previewUrl' in responseData.data
                       ? String(responseData.data.previewUrl) 
                       : undefined,
        };
    }

    public async continueInteractiveProcess(
        userInput: Record<string, unknown>,
        callbacks: ReportCallbacks
    ): Promise<InteractiveResult> {
        // インタラクティブ処理の継続ロジック
        // UIコンポーネントから呼び出される
        callbacks.onProgress?.(this.currentState.currentStep + 1);
        
        // TODO: 実際のAPI呼び出しとステップ処理を実装
        return {
            success: true,
            resultType: 'excel',
        };
    }
}

// ==============================
// 🏭 ファクトリークラス（Factory Pattern）
// ==============================

/**
 * レポートプロセッサーファクトリー
 * （Open/Closed Principle & Factory Pattern）
 */
export class ReportProcessorFactory {
    private static processors = new Map<string, () => IReportProcessor>();

    static {
        // 静的初期化ブロックで登録
        this.processors.set(REPORT_GENERATION_MODES.AUTO, () => new AutoReportProcessor());
        this.processors.set(REPORT_GENERATION_MODES.INTERACTIVE, () => new InteractiveReportProcessor());
    }

    static createProcessor(reportKey: ReportKey): IReportProcessor {
        const modeInfo = getReportModeInfo(reportKey);
        const processorCreator = this.processors.get(modeInfo.mode);

        if (!processorCreator) {
            throw new Error(`Unsupported report mode: ${modeInfo.mode}`);
        }

        return processorCreator();
    }

    /**
     * 新しいプロセッサーを登録（拡張性のため）
     */
    static registerProcessor(mode: string, creator: () => IReportProcessor): void {
        this.processors.set(mode, creator);
    }
}

// ==============================
// 🎯 メインサービスクラス
// ==============================

/**
 * レポートモードサービス
 * （Facade Pattern）
 */
export class ReportModeService {
    /**
     * 指定された帳簿キーのモード情報を取得
     */
    static getModeInfo(reportKey: ReportKey): ReportModeInfo {
        return getReportModeInfo(reportKey);
    }

    /**
     * レポート生成を実行
     */
    static async generateReport(
        csvFiles: Record<string, File>,
        reportKey: ReportKey,
        callbacks: ReportCallbacks
    ): Promise<ReportProcessResult> {
        const processor = ReportProcessorFactory.createProcessor(reportKey);
        return await processor.processReport(csvFiles, reportKey, callbacks);
    }

    /**
     * 指定されたレポートキーがインタラクティブモードかどうかを判定
     */
    static isInteractiveMode(reportKey: ReportKey): boolean {
        return this.getModeInfo(reportKey).isInteractive;
    }

    /**
     * インタラクティブプロセッサーを取得（型安全性を保証）
     */
    static getInteractiveProcessor(reportKey: ReportKey): InteractiveReportProcessor {
        if (!this.isInteractiveMode(reportKey)) {
            throw new Error(`Report key ${reportKey} is not in interactive mode`);
        }
        
        return ReportProcessorFactory.createProcessor(reportKey) as InteractiveReportProcessor;
    }
}
