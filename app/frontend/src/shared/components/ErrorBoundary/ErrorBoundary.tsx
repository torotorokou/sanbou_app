/**
 * ErrorBoundary - グローバルエラーバウンダリー
 * 
 * Reactコンポーネントツリー内で発生した JavaScript エラーをキャッチし、
 * ユーザーフレンドリーなフォールバックUIを表示します。
 * 
 * 本番環境ではスタックトレースを隠し、ユーザー向けメッセージを表示します。
 */

import React, { Component, type ErrorInfo, type ReactNode } from 'react';
import { Button, Result, Typography } from 'antd';

const { Paragraph, Text } = Typography;

interface Props {
    children: ReactNode;
    /** カスタムフォールバックUI */
    fallback?: ReactNode;
    /** エラー発生時のコールバック */
    onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
}

const isProduction = import.meta.env.PROD;

/**
 * ErrorBoundary コンポーネント
 * 
 * @example
 * ```tsx
 * <ErrorBoundary>
 *   <App />
 * </ErrorBoundary>
 * ```
 */
class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
        errorInfo: null,
    };

    public static getDerivedStateFromError(error: Error): Partial<State> {
        // 次のレンダリングでフォールバックUIを表示するようにstate更新
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
        // エラー情報をstateに保存
        this.setState({ errorInfo });
        
        // エラーログ出力（本番環境では詳細なスタックトレースは非表示）
        if (!isProduction) {
            console.error('ErrorBoundary caught an error:', error);
            console.error('Error info:', errorInfo);
        } else {
            // 本番環境: 最小限の情報のみログ
            console.error('An error occurred in the application');
        }
        
        // カスタムエラーハンドラーを呼び出し
        this.props.onError?.(error, errorInfo);
        
        // TODO: 本番環境ではエラー監視サービス（Sentry等）に送信
        // if (isProduction) {
        //     reportErrorToService(error, errorInfo);
        // }
    }

    private handleReload = (): void => {
        window.location.reload();
    };

    private handleGoHome = (): void => {
        window.location.href = '/';
    };

    public render(): ReactNode {
        if (this.state.hasError) {
            // カスタムフォールバックがあれば使用
            if (this.props.fallback) {
                return this.props.fallback;
            }

            // デフォルトのエラーUI
            return (
                <Result
                    status="error"
                    title="エラーが発生しました"
                    subTitle="申し訳ございません。予期しないエラーが発生しました。"
                    extra={[
                        <Button type="primary" key="reload" onClick={this.handleReload}>
                            ページを再読み込み
                        </Button>,
                        <Button key="home" onClick={this.handleGoHome}>
                            ホームに戻る
                        </Button>,
                    ]}
                >
                    {!isProduction && this.state.error && (
                        <div style={{ textAlign: 'left', marginTop: 24 }}>
                            <Paragraph>
                                <Text strong style={{ fontSize: 16 }}>
                                    エラー詳細（開発環境のみ表示）:
                                </Text>
                            </Paragraph>
                            <Paragraph>
                                <pre style={{ 
                                    background: '#f5f5f5', 
                                    padding: 16, 
                                    borderRadius: 4,
                                    overflow: 'auto',
                                    maxHeight: 300,
                                    fontSize: 12
                                }}>
                                    {this.state.error.toString()}
                                    {this.state.errorInfo?.componentStack}
                                </pre>
                            </Paragraph>
                        </div>
                    )}
                </Result>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
