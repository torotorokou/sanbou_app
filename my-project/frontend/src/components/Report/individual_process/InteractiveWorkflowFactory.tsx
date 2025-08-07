import React from 'react';
import type { InteractiveWorkflowProps } from '../../../types/interactiveWorkflow';

/**
 * インタラクティブワークフローファクトリー
 * レポートタイプに応じて適切なワークフローコンポーネントを返す
 */
class InteractiveWorkflowFactory {
    private static workflowComponents: Record<string, React.ComponentType<InteractiveWorkflowProps>> = {};

    /**
     * ワークフローコンポーネントを登録
     */
    static register(reportKey: string, component: React.ComponentType<InteractiveWorkflowProps>) {
        this.workflowComponents[reportKey] = component;
    }

    /**
     * ワークフローコンポーネントを取得
     */
    static getWorkflowComponent(reportKey: string): React.ComponentType<InteractiveWorkflowProps> | null {
        return this.workflowComponents[reportKey] || null;
    }

    /**
     * サポートされているレポートタイプの一覧を取得
     */
    static getSupportedReportTypes(): string[] {
        return Object.keys(this.workflowComponents);
    }

    /**
     * レポートタイプがサポートされているかチェック
     */
    static isSupported(reportKey: string): boolean {
        return reportKey in this.workflowComponents;
    }
}

// デフォルトワークフローの登録
// NOTE: 動的インポートを使用して、コード分割を可能にする
export const registerDefaultWorkflows = () => {
    // ブロック単価表ワークフローの遅延ロード
    const loadBlockUnitPriceWorkflow = () =>
        import('./BlockUnitPriceWorkflow').then(module => module.default);

    // 動的インポートでコンポーネントを包む
    const BlockUnitPriceWorkflowWrapper: React.FC<InteractiveWorkflowProps> = (props) => {
        const [Component, setComponent] = React.useState<React.ComponentType<InteractiveWorkflowProps> | null>(null);
        const [loading, setLoading] = React.useState(true);
        const [error, setError] = React.useState<string | null>(null);

        React.useEffect(() => {
            import('./BlockUnitPriceWorkflow')
                .then(module => {
                    setComponent(() => module.default);
                    setLoading(false);
                })
                .catch(err => {
                    console.error('Failed to load BlockUnitPriceWorkflow:', err);
                    setError('ワークフローの読み込みに失敗しました');
                    setLoading(false);
                });
        }, []);

        if (loading) {
            return <div>ワークフローを読み込み中...</div>;
        }

        if (error) {
            return <div>エラー: {error}</div>;
        }

        if (!Component) {
            return <div>ワークフローが見つかりません</div>;
        }

        return <Component {...props} />;
    };

    // ワークフローを登録
    InteractiveWorkflowFactory.register('block_unit_price', BlockUnitPriceWorkflowWrapper);
};

export default InteractiveWorkflowFactory;
