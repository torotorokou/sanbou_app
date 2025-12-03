/**
 * システムヘルスチェック Hook
 * 
 * バックエンドサービスの稼働状態を監視し、問題がある場合に通知を表示する。
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { coreApi } from '@/shared';
import { notifyWarning, notifyError } from '@features/notification';

export type ServiceStatus = 'healthy' | 'unhealthy' | 'timeout' | 'error' | 'unknown';
export type OverallStatus = 'healthy' | 'degraded' | 'critical' | 'unknown';

export interface ServiceHealth {
    name: string;
    status: ServiceStatus;
    url?: string;
    response_time_ms?: number;
    error?: string;
    checked_at?: string;
}

export interface SystemHealthStatus {
    status: OverallStatus;
    healthy_services: number;
    total_services: number;
    services: Record<string, ServiceHealth>;
    checked_at: string;
}

export interface UseSystemHealthOptions {
    /** 自動チェックを有効にするか（デフォルト: true） */
    enabled?: boolean;
    /** チェック間隔（ミリ秒、デフォルト: 30秒） */
    interval?: number;
    /** 通知を表示するか（デフォルト: true） */
    showNotifications?: boolean;
}

export interface UseSystemHealthReturn {
    /** 現在のシステムヘルスステータス */
    status: SystemHealthStatus | null;
    /** ヘルスチェック中かどうか */
    isChecking: boolean;
    /** 手動でヘルスチェックを実行 */
    checkHealth: () => Promise<void>;
    /** 最後のチェック時刻 */
    lastChecked: Date | null;
}

const SERVICE_LABELS: Record<string, string> = {
    ai_api: 'AI API',
    ledger_api: '帳簿API',
    rag_api: 'RAG API',
    manual_api: 'マニュアルAPI',
};

/**
 * システムヘルスチェック Hook
 */
export function useSystemHealth(options: UseSystemHealthOptions = {}): UseSystemHealthReturn {
    const {
        enabled = true,
        interval = 30000, // 30秒
        showNotifications = true,
    } = options;

    const [status, setStatus] = useState<SystemHealthStatus | null>(null);
    const [isChecking, setIsChecking] = useState(false);
    const [lastChecked, setLastChecked] = useState<Date | null>(null);
    const notifiedServicesRef = useRef<Set<string>>(new Set());
    const intervalIdRef = useRef<NodeJS.Timeout | null>(null);

    const checkHealth = useCallback(async () => {
        if (isChecking) return;

        setIsChecking(true);
        try {
            const result = await coreApi.get<SystemHealthStatus>('/core_api/health/services');
            setStatus(result);
            setLastChecked(new Date());

            // 通知処理
            if (showNotifications) {
                const currentUnhealthyServices = new Set<string>();

                // 問題のあるサービスを検出
                Object.entries(result.services).forEach(([serviceName, serviceStatus]) => {
                    if (serviceStatus.status !== 'healthy') {
                        currentUnhealthyServices.add(serviceName);

                        // まだ通知していないサービスの場合のみ通知
                        if (!notifiedServicesRef.current.has(serviceName)) {
                            const label = SERVICE_LABELS[serviceName] || serviceName;
                            const errorMsg = serviceStatus.error || '接続できません';
                            
                            if (serviceStatus.status === 'timeout') {
                                notifyWarning(
                                    `${label}がタイムアウトしています`,
                                    'サービスの応答が遅くなっています。'
                                );
                            } else {
                                notifyError(
                                    `${label}が利用できません`,
                                    errorMsg
                                );
                            }
                            
                            notifiedServicesRef.current.add(serviceName);
                        }
                    }
                });

                // 回復したサービスを通知済みセットから削除
                notifiedServicesRef.current.forEach((serviceName) => {
                    if (!currentUnhealthyServices.has(serviceName)) {
                        notifiedServicesRef.current.delete(serviceName);
                    }
                });
            }
        } catch (error) {
            console.error('[useSystemHealth] Health check failed:', error);
            // Core API自体が落ちている場合は通知を抑制（ノイズを避けるため）
        } finally {
            setIsChecking(false);
        }
    }, [isChecking, showNotifications]);

    // 自動チェックの設定
    useEffect(() => {
        if (!enabled) {
            if (intervalIdRef.current) {
                clearInterval(intervalIdRef.current);
                intervalIdRef.current = null;
            }
            return;
        }

        // 初回実行
        checkHealth();

        // 定期実行
        intervalIdRef.current = setInterval(checkHealth, interval);

        return () => {
            if (intervalIdRef.current) {
                clearInterval(intervalIdRef.current);
                intervalIdRef.current = null;
            }
        };
    }, [enabled, interval, checkHealth]);

    return {
        status,
        isChecking,
        checkHealth,
        lastChecked,
    };
}
