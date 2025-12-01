/**
 * Report API Client
 * MVC: API層 - HTTP通信の抽象化
 * 
 * すべてのレポート関連のAPI呼び出しをここに集約
 */

import { coreApi } from '@/shared';

// Re-export block unit price functions from dedicated module
export {
    initializeBlockUnitPrice,
    startBlockUnitPrice,
    selectTransport,
    applyPrice,
    finalizePrice,
    type BlockUnitPriceInitialRequest,
    type BlockUnitPriceInitialResponse,
    type BlockUnitPriceStartRequest,
    type BlockUnitPriceStartResponse,
    type SelectTransportRequest,
    type SelectTransportResponse,
    type ApplyPriceRequest,
    type ApplyPriceResponse,
    type FinalizePriceRequest,
    type FinalizePriceResponse,
} from '@features/report/interactive/infrastructure';

/**
 * レポート生成のレスポンス型
 */
export interface ReportArtifactResponse {
    status?: string;
    report_key?: string;
    report_date?: string;
    artifact?: {
        excel_download_url?: string | null;
        pdf_preview_url?: string | null;
        report_token?: string | null;
    } | null;
    summary?: unknown;
    metadata?: unknown;
    [key: string]: unknown;
}

/**
 * レポート生成リクエスト（基本形）
 */
export interface ReportGenerateRequest {
    report_key: string;
    date?: string;
    factory_id?: string;
    period_type?: 'oneday' | 'oneweek' | 'onemonth';
    [key: string]: unknown;
}

/**
 * 工場日報生成
 */
export async function generateFactoryReport(
    date: string,
    factory_id?: string
): Promise<ReportArtifactResponse> {
    return coreApi.post<ReportArtifactResponse>(
        '/core_api/reports/factory_report/',
        { date, factory_id }
    );
}

/**
 * 収支表生成
 */
export async function generateBalanceSheet(
    date: string,
    factory_id?: string
): Promise<ReportArtifactResponse> {
    return coreApi.post<ReportArtifactResponse>(
        '/core_api/reports/balance_sheet/',
        { date, factory_id }
    );
}

/**
 * 平均表生成
 */
export async function generateAverageSheet(
    date: string,
    factory_id?: string
): Promise<ReportArtifactResponse> {
    return coreApi.post<ReportArtifactResponse>(
        '/core_api/reports/average_sheet/',
        { date, factory_id }
    );
}

/**
 * 管理表生成
 */
export async function generateManagementSheet(
    date: string,
    factory_id?: string
): Promise<ReportArtifactResponse> {
    return coreApi.post<ReportArtifactResponse>(
        '/core_api/reports/management_sheet/',
        { date, factory_id }
    );
}

// NOTE: initializeBlockUnitPrice and related functions are re-exported from @/features/block-unit-price above

/**
 * 汎用レポート生成（FormData使用）
 * FormDataを使用するレポート生成用
 */
export async function generateReportWithFiles<T = ReportArtifactResponse>(
    endpoint: string,
    formData: FormData
): Promise<T> {
    return coreApi.uploadForm<T>(endpoint, formData, { timeout: 60000 });
}
