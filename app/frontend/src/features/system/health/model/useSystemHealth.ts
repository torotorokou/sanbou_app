/**
 * システムヘルスチェック Hook
 * 
 * 管理者向けのオンデマンドヘルスチェック機能を提供。
 * 
 * ## 設計思想
 * - 通常運用では自動実行しない(Docker/K8sのHEALTHCHECKに任せる)
 * - 管理画面などで明示的に「システム状態確認」を実行する際に使用
 * - ユーザー向けエラーハンドリングはAxiosインターセプターで実施
 * - インフラ監視はPrometheus/Grafana/Datadog等の専用ツールで実施
 * 
 * ## 使用例
 * ```tsx
 * // 管理画面でシステムステータスを表示
 * const { status, checkHealth, isChecking } = useSystemHealth();
 * 
 * return (
 *   <Button onClick={checkHealth} loading={isChecking}>
 *     システム状態を確認
 *   </Button>
 * );
 * ```
 */

import { useState, useCallback, useRef } from 'react';
import { coreApi } from '@/shared';

export type ServiceStatus = 'healthy' | 'unhealthy' | 'timeout' | 'error' | 'unknown';
export type OverallStatus = 'healthy' | 'degraded' | 'critical' | 'unknown';

export interface ServiceHealth {
    status: ServiceStatus;
    response_time_ms?: number;
    error_message?: string;
}

export interface UseSystemHealthOptions {
    /** 初回マウント時に自動実行するか（デフォルト: false） */
    autoCheckOnMount?: boolean;
}

export interface SystemHealthStatus {
    status: OverallStatus;
    healthy_services: number;
    total_services: number;
    services: Record<string, ServiceHealth>;
    checked_at: string;
}

export interface UseSystemHealthReturn {
    /** 現在のシステムヘルスステータス */
    status: SystemHealthStatus | null;
    /** ヘルスチェック中かどうか */
    isChecking: boolean;
    /** ヘルスチェックエラー */
    error: Error | null;
    /** 手動でヘルスチェックを実行 */
    checkHealth: () => Promise<void>;
    /** 最後のチェック時刻 */
    lastChecked: Date | null;
}

/**
 * システムヘルスチェック Hook
 * 
 * オンデマンドでバックエンドサービスの状態を確認する。
 * 自動実行は行わず、管理者が明示的に実行する設計。
 * 
 * @param _options - 将来的な拡張用オプション（現在は未使用）
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function useSystemHealth(_options: UseSystemHealthOptions = {}): UseSystemHealthReturn {
    // Note: autoCheckOnMount is intentionally not used. 
    // Health checks are manual-only by design.

    const [status, setStatus] = useState<SystemHealthStatus | null>(null);
    const [isChecking, setIsChecking] = useState(false);
    const [error, setError] = useState<Error | null>(null);
    const [lastChecked, setLastChecked] = useState<Date | null>(null);
    const isCheckingRef = useRef(false);

    const checkHealth = useCallback(async () => {
        if (isCheckingRef.current) {
            console.warn('[useSystemHealth] Health check already in progress');
            return;
        }

        isCheckingRef.current = true;
        setIsChecking(true);
        setError(null);

        try {
            const result = await coreApi.get<SystemHealthStatus>('/core_api/health/services');
            setStatus(result);
            setLastChecked(new Date());
        } catch (err) {
            const errorObj = err instanceof Error ? err : new Error('Unknown error');
            setError(errorObj);
            console.error('[useSystemHealth] Health check failed:', errorObj);
        } finally {
            setIsChecking(false);
            isCheckingRef.current = false;
        }
    }, []);

    // Note: 自動実行は削除。必要な場合は管理画面で明示的に checkHealth() を呼び出す
    // useEffect(() => {
    //     if (autoCheckOnMount) {
    //         checkHealth();
    //     }
    // }, [autoCheckOnMount, checkHealth]);

    return {
        status,
        isChecking,
        error,
        checkHealth,
        lastChecked,
    };
}
